"""Hash e verificação de senha (SENHAV2) com bcrypt."""

import bcrypt


def senhav2_preenchida(raw: str | None) -> bool:
    """True se SENHAV2 está cadastrada (não nula e não vazia)."""
    if raw is None:
        return False
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="ignore")
    return bool(str(raw).strip())


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or not plain:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
