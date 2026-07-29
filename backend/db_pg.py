"""Ponte Firebird -> Postgres para o banco Questor do Vulcano 2.0.

O Questor migrou de Firebird para Postgres (2026-07). O Vulcano fala Firebird
(driver `firebirdsql`, placeholders `?`, dialeto FB). Para NAO reescrever as ~centenas
de queries, este modulo oferece:

  - `questor_kind()`        : "postgres" ou "firebird" (env QUESTOR_DB_KIND, default firebird)
  - `connect_questor_pg()`  : abre psycopg ao Questor-PG, com retry no connect
  - wrappers `_PgConnection`/`_PgCursor` : mesma interface do firebirdsql
        (`cursor()`, `execute(sql, params)` com `?`, `fetchone/fetchall`,
         `commit/rollback/close`), traduzindo o SQL Firebird em cada execute.
  - `.kind == "postgres"` exposto na conexao e no cursor, para os poucos pontos de
    INTROSPECCAO (RDB$...) que precisam ramificar para `information_schema`.

IMPORTANTE: isto vale SO para o banco `questor`. O banco `vulcano` (VULCANO.FDB) e o
sqlite de POC continuam intactos — nunca passam por aqui.

Traducoes (ver `translate`): `?`->`%s`, `FIRST n`->`LIMIT n`,
`FETCH FIRST n ROWS ONLY`->`LIMIT n`, `STARTING WITH`->`LIKE`, `CONTAINING`->`ILIKE`,
identificadores `"MAIUSCULO"` -> `"minusculo"` (PG guarda em minusculo), e dobra `%`
literal quando ha parametros.
"""
from __future__ import annotations

import os
import re
import time

# ---------------------------------------------------------------- tradutor SQL --

_FIRST_RE = re.compile(r"\bSELECT\s+FIRST\s+(\d+)\b", re.IGNORECASE)
_FETCH_FIRST_RE = re.compile(r"\bFETCH\s+FIRST\s+(\d+)\s+ROWS?\s+ONLY\b", re.IGNORECASE)
_SW_LIT_RE = re.compile(r"\bSTARTING\s+WITH\s+'((?:[^']|'')*)'", re.IGNORECASE)
_SW_PARAM_RE = re.compile(r"\bSTARTING\s+WITH\s+\?", re.IGNORECASE)
_CONTAINING_RE = re.compile(
    r"\bCONTAINING\s+("
    r"'(?:[^']|'')*'"
    r"|\?"
    r"|[A-Za-z_][\w.]*\([^()]*\)"
    r"|[A-Za-z_][\w.]*"
    r")",
    re.IGNORECASE,
)
# identificador entre aspas duplas TODO-MAIUSCULO -> minusculo
_QUOTED_IDENT_RE = re.compile(r'"([A-Z_][A-Z0-9_]*)"')


def _containing_sub(m: "re.Match[str]") -> str:
    op = m.group(1)
    if op.startswith("'") and op.endswith("'"):
        return f"ILIKE '%{op[1:-1]}%'"
    return f"ILIKE ('%' || {op} || '%')"


def translate(sql: str) -> str:
    """Traduz uma query Firebird para Postgres (conjunto de dialetos do Vulcano)."""
    limit_n: str | None = None

    m = _FIRST_RE.search(sql)
    if m:
        limit_n = m.group(1)
        sql = _FIRST_RE.sub("SELECT", sql, count=1)

    m2 = _FETCH_FIRST_RE.search(sql)
    if m2:
        limit_n = m2.group(1)
        sql = _FETCH_FIRST_RE.sub("", sql, count=1)

    sql = _SW_LIT_RE.sub(lambda mm: "LIKE '" + mm.group(1) + "%'", sql)
    sql = _SW_PARAM_RE.sub("LIKE ? || '%'", sql)
    sql = _CONTAINING_RE.sub(_containing_sub, sql)

    # "CODIGOEMPRESA" -> "codigoempresa" (PG rebaixa identificadores nao-aspados;
    # os aspados precisam bater com o nome real, que no PG e minusculo).
    sql = _QUOTED_IDENT_RE.sub(lambda mm: '"' + mm.group(1).lower() + '"', sql)

    has_params = "?" in sql
    if has_params:
        sql = sql.replace("%", "%%")
        sql = sql.replace("?", "%s")

    if limit_n is not None:
        sql = sql.rstrip().rstrip(";")
        sql = f"{sql} LIMIT {limit_n}"

    return sql


# ------------------------------------------------------------- backend / conexao --

def questor_kind() -> str:
    return os.environ.get("QUESTOR_DB_KIND", "firebird").strip().lower()


def _pg_conninfo() -> dict:
    return {
        "host": os.environ.get("QUESTOR_PG_HOST", os.environ.get("FIREBIRD_HOST_QUESTOR", "192.168.16.242")),
        "port": int(os.environ.get("QUESTOR_PG_PORT", "5432")),
        "dbname": os.environ.get("QUESTOR_PG_DB", "questor"),
        "user": os.environ.get("QUESTOR_PG_USER", "sigra_gravacao"),
        "password": os.environ["QUESTOR_PG_PASS"],
        "connect_timeout": int(os.environ.get("QUESTOR_PG_TIMEOUT", "10")),
    }


class _PgCursor:
    """Cursor psycopg que traduz o SQL Firebird em cada execute()."""

    kind = "postgres"

    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=None):
        sql = translate(sql)
        if params is None:
            return self._cur.execute(sql)
        return self._cur.execute(sql, tuple(params))

    def executemany(self, sql, seq_params):
        return self._cur.executemany(translate(sql), seq_params)

    def __iter__(self):
        return iter(self._cur)

    def __enter__(self):
        self._cur.__enter__()
        return self

    def __exit__(self, *exc):
        return self._cur.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._cur, name)


class _PgConnection:
    """Conexao psycopg cujo .cursor() entrega o cursor tradutor."""

    kind = "postgres"

    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *a, **kw):
        return _PgCursor(self._conn.cursor(*a, **kw))

    def __enter__(self):
        # firebirdsql e psycopg suportam `with conn:`; delega o commit/close ao psycopg.
        self._conn.__enter__()
        return self

    def __exit__(self, *exc):
        return self._conn.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def connect_questor_pg():
    """Abre conexao psycopg ao Questor-PG (com retry no connect: o link oscila)."""
    import psycopg  # import tardio: so exige psycopg quando o backend e Postgres

    attempts = int(os.environ.get("QUESTOR_PG_CONNECT_RETRIES", "3"))
    last = None
    for i in range(attempts):
        try:
            return _PgConnection(psycopg.connect(**_pg_conninfo()))
        except psycopg.OperationalError as e:
            last = e
            if "timeout" in str(e).lower() and i < attempts - 1:
                time.sleep(1.5)
                continue
            raise
    raise last  # pragma: no cover
