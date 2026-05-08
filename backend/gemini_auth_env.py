"""Resolve Vertex / Gemini credentials from env ou arquivo JSON no diretório backend."""

from __future__ import annotations

import json
import os

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


def credentials_path_abs(raw: str) -> str:
    """Caminho absoluto para credencial: relativos são sempre relativos ao diretório `backend/` (local e Docker /app)."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    return raw if os.path.isabs(raw) else os.path.abspath(os.path.join(_BACKEND_DIR, raw))


def resolve_google_application_credentials() -> None:
    """Define GOOGLE_APPLICATION_CREDENTIALS com caminho absoluto quando o JSON existe."""

    basename = os.environ.get("GEMINI_CREDENTIALS_FILE", "chave_fernando.json")

    for raw in (
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip(),
        os.environ.get("GEMINI_CREDENTIALS_JSON", "").strip(),
    ):
        if not raw:
            continue
        abs_path = credentials_path_abs(raw)
        if os.path.isfile(abs_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path
            return

    default_path = os.path.join(_BACKEND_DIR, basename)
    if os.path.isfile(default_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(default_path)


def vertex_credentials_configured() -> bool:
    p = credentials_path_abs(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))
    return bool(p and os.path.isfile(p))


def vertex_project_id() -> str:
    proj = (
        os.environ.get("VERTEX_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
    ).strip()
    if proj:
        return proj
    cred = credentials_path_abs(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))
    if cred and os.path.isfile(cred):
        try:
            with open(cred, encoding="utf-8") as cf:
                return (json.load(cf).get("project_id") or "").strip() or "questor-explorer-prod"
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return "questor-explorer-prod"


def vertex_location() -> str:
    return os.environ.get("VERTEX_LOCATION", "us-central1").strip() or "us-central1"
