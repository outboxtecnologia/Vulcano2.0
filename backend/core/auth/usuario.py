"""Consultas USUARIO (Firebird Vulcano) para login e primeiro acesso."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class UsuarioAuthRow:
    id: int
    usuario_id: str
    nome: str
    tipo_permissao: str
    email: str
    senhav2: str | None


def _decode(val) -> str:
    if val is None:
        return ""
    if isinstance(val, bytes):
        return val.decode("cp1252", errors="ignore").strip()
    return str(val).strip()


def buscar_usuario_por_login(get_conn: Callable, ident: str) -> UsuarioAuthRow | None:
    """Busca usuário ativo por e-mail ou USUARIOID."""
    ident = (ident or "").strip()
    if not ident:
        return None
    conn = get_conn("vulcano")
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT FIRST 1 ID, USUARIOID, NOMECOMPLETO, TIPOPERMISSAO, EMAIL, SENHAV2
            FROM USUARIO
            WHERE (UPPER(EMAIL) = UPPER(?) OR UPPER(USUARIOID) = UPPER(?))
              AND ATIVO = 'T'
            """,
            (ident, ident),
        )
        row = cur.fetchone()
        if not row:
            return None
        senhav2_raw = row[5]
        if isinstance(senhav2_raw, bytes):
            senhav2 = senhav2_raw.decode("utf-8", errors="ignore")
        elif senhav2_raw is None:
            senhav2 = None
        else:
            senhav2 = str(senhav2_raw)
        return UsuarioAuthRow(
            id=int(row[0]),
            usuario_id=_decode(row[1]),
            nome=_decode(row[2]),
            tipo_permissao=_decode(row[3]),
            email=_decode(row[4]),
            senhav2=senhav2,
        )
    finally:
        conn.close()


def usuario_para_json(u: UsuarioAuthRow) -> dict:
    return {
        "id": u.id,
        "usuarioId": u.usuario_id,
        "nome": u.nome,
        "tipoPermissao": u.tipo_permissao,
        "email": u.email,
    }


def atualizar_senhav2(get_conn: Callable, user_id: int, senha_hash: str) -> None:
    conn = get_conn("vulcano")
    try:
        cur = conn.cursor()
        cur.execute("UPDATE USUARIO SET SENHAV2 = ? WHERE ID = ?", (senha_hash, user_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
