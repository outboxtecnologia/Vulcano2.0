"""Migra os dados operacionais do app: poc_database.sqlite → Postgres (vulcano2).

Uso (venv do backend, com APP_PG_* / QUESTOR_PG_* no .env):
  python migrar_app_para_pg.py            # copia tudo (pula linhas já existentes)
  python migrar_app_para_pg.py --dry-run  # só mostra contagens

Pré-requisito: rodar antes `python bootstrap_schema.py --target app-pg`.
Timestamps do SQLite (UTC naive) são interpretados como UTC na carga.
"""
from __future__ import annotations

import argparse
import sqlite3

from bootstrap_schema import _load_env
from db_app import _pg_conninfo, sqlite_path

# tabela → colunas com conflito ignorável (idempotência da carga)
TABELAS = {
    "sero_importacoes": "(id)",
    "conversor_batches": "(id)",
    "conversor_data_staging": "(id)",
    "cross_match_feedback": "(id)",
    "cross_match_rules": "(id)",
    "pdf_parser_templates": "(id)",
    "empresa_parser_padrao": "(empresa_id)",
    "evolucao_obras": "(empreendimento, periodo)",
    "import_templates": "(id)",
    "operacoes_baixas": "(id_receber)",
    "parcelas_abertas_projetadas": "(prazo_id)",
    "smart_importer_queue": "(file_hash)",
    "smart_importer_templates": "(id)",
    "usuarios_local": "(usuario_id)",
    "auditoria_memoria_arraste": "(chave_lancamento)",
}

# nomes reais no SQLite quando diferem (case)
NOME_SQLITE = {"sero_importacoes": "SERO_IMPORTACOES"}

SEQ_IDENTITY = [
    "sero_importacoes", "conversor_batches", "conversor_data_staging",
    "cross_match_feedback", "cross_match_rules", "pdf_parser_templates",
    "import_templates", "operacoes_baixas", "smart_importer_queue",
    "smart_importer_templates", "usuarios_local",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _load_env()
    import psycopg

    sq = sqlite3.connect(sqlite_path())
    sq.row_factory = sqlite3.Row
    pg = psycopg.connect(**_pg_conninfo())
    try:
        with pg.cursor() as c:
            c.execute("SET timezone = 'UTC'")  # timestamps SQLite são UTC naive

        total = 0
        for tabela, conflito in TABELAS.items():
            origem = NOME_SQLITE.get(tabela, tabela)
            try:
                rows = sq.execute(f"SELECT * FROM {origem}").fetchall()
            except sqlite3.OperationalError:
                print(f"  - {tabela}: inexistente no SQLite, pulando")
                continue
            if not rows:
                print(f"  - {tabela}: 0 linhas")
                continue
            cols = rows[0].keys()
            if args.dry_run:
                print(f"  - {tabela}: {len(rows)} linhas (dry-run)")
                continue
            placeholders = ", ".join(["%s"] * len(cols))
            on_conflict = f" ON CONFLICT {conflito} DO NOTHING" if conflito else ""
            sql = (f"INSERT INTO {tabela} ({', '.join(cols)}) "
                   f"VALUES ({placeholders}){on_conflict}")
            dados = []
            for r in rows:
                vals = list(r)
                if tabela == "operacoes_baixas":
                    idx = list(cols).index("id_receber")
                    vals[idx] = str(vals[idx])  # INTEGER dinâmico no SQLite → TEXT no PG
                dados.append(tuple(vals))
            with pg.cursor() as c:
                c.executemany(sql, dados)
                print(f"  - {tabela}: {len(rows)} lidas, {c.rowcount if c.rowcount >= 0 else len(rows)} inseridas")
            total += len(rows)

        if not args.dry_run:
            with pg.cursor() as c:
                for t in SEQ_IDENTITY:
                    c.execute(
                        f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {t}), 1))"
                    )
            pg.commit()
            print(f"[OK] Migração concluída: {total} linhas; sequences realinhadas.")
        return 0
    except Exception:
        pg.rollback()
        raise
    finally:
        sq.close()
        pg.close()


if __name__ == "__main__":
    raise SystemExit(main())
