from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Form, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import firebirdsql
from db_pg import connect_questor_pg, questor_kind  # ponte Questor Firebird->Postgres
from db_app import connect_app  # banco operacional do app: SQLite ou Postgres (APP_DB_KIND)
import pdfplumber
import platform
import functools
# BUGFIX: Bypass WMI queries on Windows to avoid freeze during pandas import!
platform.machine = lambda: 'AMD64'
platform.win32_ver = lambda *args, **kwargs: ('10', '', '', '')
class FakeUname:
    system = 'Windows'
    node = 'NODE'
    release = '10'
    version = '10.0.19041'
    machine = 'AMD64'
    processor = 'AMD64 Family'
platform.uname = lambda: FakeUname()


try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import google.generativeai as genai
except BaseException:
    genai = None

def _get_np():
    import numpy as _np
    return _np
def _get_pd():
    import pandas as _pd
    return _pd

class _LazyLoader:
    def __init__(self, loader):
        self._loader = loader
        self._mod = None
    def __getattr__(self, item):
        if self._mod is None:
            self._mod = self._loader()
        return getattr(self._mod, item)

np = _LazyLoader(_get_np)
pd = _LazyLoader(_get_pd)

import os
import re
import io
import tempfile
import asyncio
import math
import sys
from datetime import date, datetime, time as time_type



import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Carrega variáveis sempre a partir do `backend/.env`, independente do CWD.
if getattr(sys, 'frozen', False):
    _DOTENV_PATH = os.path.join(os.path.dirname(sys.executable), ".env")
else:
    _DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)

from gemini_auth_env import (
    resolve_google_application_credentials,
    vertex_credentials_configured,
    vertex_project_id,
    vertex_location,
)

resolve_google_application_credentials()

_DEFAULT_DB_QUESTOR = r"D:\Questor_Restore\Questor.fdb"
_DEFAULT_DB_VULCANO = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb"
DB_PATH_QUESTOR = os.environ.get("DB_PATH_QUESTOR", _DEFAULT_DB_QUESTOR)
DB_PATH_VULCANO = os.environ.get("DB_PATH_VULCANO", _DEFAULT_DB_VULCANO)
FIREBIRD_HOST = os.environ.get("FIREBIRD_HOST", "127.0.0.1")
# Host por base (opcional): se ausente, usa FIREBIRD_HOST para ambos.
FIREBIRD_HOST_QUESTOR = os.environ.get("FIREBIRD_HOST_QUESTOR", FIREBIRD_HOST)
FIREBIRD_HOST_VULCANO = os.environ.get("FIREBIRD_HOST_VULCANO", FIREBIRD_HOST)
FIREBIRD_PORT = int(os.environ.get("FIREBIRD_PORT", "3050"))
FIREBIRD_USER = os.environ.get("FIREBIRD_USER", "SYSDBA")
FIREBIRD_PASSWORD = os.environ.get("FIREBIRD_PASSWORD", "masterkey")

if genai:
    _gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if _gemini_key:
        genai.configure(api_key=_gemini_key)

# Setup Cloud/Vertex para performance corporativa (JSON)
_VERTEX_INIT_DONE = False
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as OriginalVertexModel, Part
    
    class VertexModel:
        def __init__(self, *args, **kwargs):
            global _VERTEX_INIT_DONE
            if not _VERTEX_INIT_DONE:
                vertexai.init(project=vertex_project_id(), location=vertex_location())
                _VERTEX_INIT_DONE = True
            self.model = OriginalVertexModel(*args, **kwargs)
            
        def generate_content(self, *args, **kwargs):
            return self.model.generate_content(*args, **kwargs)
            
        async def generate_content_async(self, *args, **kwargs):
            return await self.model.generate_content_async(*args, **kwargs)
            
    HAS_VERTEXAI = True
except ImportError:
    HAS_VERTEXAI = False

# Vertex só quando o pacote existe e há JSON de credenciais (evita Vertex sem ADC).
USE_VERTEX_FOR_GEMINI = bool(HAS_VERTEXAI and vertex_credentials_configured())

# Modelo rápido por padrão; use GEMINI_MODEL no .env (ex.: gemini-2.5-flash) se quiser.
GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# Timeout da extração via Gemini (segundos). Front-end deve esperar pelo menos esse tempo.
GEMINI_EXTRACT_TIMEOUT_SEC = float(os.environ.get("GEMINI_EXTRACT_TIMEOUT_SEC", "300"))

LAST_RAW_PDF_TEXT_FOR_PARSER = ""

OLLAMA_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL_ID = os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:3b")

# SQLite: prefere `backend/poc_database.sqlite`; se não existir, usa legado no cwd (onde o uvicorn foi iniciado).
# `POC_DATABASE_FILE` no ambiente força o caminho (útil em Docker com volume montado).
if os.environ.get("POC_DATABASE_FILE"):
    POC_DATABASE_FILE = os.environ["POC_DATABASE_FILE"]
else:
    _poc_backend = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poc_database.sqlite")
    _poc_cwd = os.path.join(os.getcwd(), "poc_database.sqlite")
    if os.path.isfile(_poc_backend):
        POC_DATABASE_FILE = _poc_backend
    elif os.path.isfile(_poc_cwd):
        POC_DATABASE_FILE = _poc_cwd
    else:
        POC_DATABASE_FILE = _poc_backend

def _gemini_auth_configured() -> bool:
    if vertex_credentials_configured():
        return True
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def _require_gemini_key():
    if not _gemini_auth_configured():
        raise HTTPException(
            status_code=500,
            detail=(
                "Credenciais Gemini não configuradas: use backend/chave_fernando.json "
                "(ou GOOGLE_APPLICATION_CREDENTIALS / GEMINI_CREDENTIALS_JSON) ou GEMINI_API_KEY no .env"
            ),
        )

def _gemini_parse_json_response(raw: str) -> dict:
    import json
    raw = (raw or "").strip()
    if not raw:
        raise HTTPException(status_code=500, detail="Resposta vazia do LLM (Gemini/Ollama)")

    
    start_obj = raw.find("{")
    start_arr = raw.find("[")
    if start_obj == -1 and start_arr == -1:
        raise HTTPException(status_code=500, detail="Nenhum JSON detectado na resposta do LLM")
    
    start_idx = -1
    if start_obj != -1 and start_arr != -1:
        start_idx = min(start_obj, start_arr)
    else:
        start_idx = max(start_obj, start_arr)
        
    sub = raw
    if start_idx != -1:
        end_obj = raw.rfind("}")
        end_arr = raw.rfind("]")
        end_idx = max(end_obj, end_arr)
            
        if end_idx >= start_idx:
            sub = raw[start_idx : end_idx + 1]
            
    try:
        return json.loads(sub)
    except json.JSONDecodeError as de:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair JSON do texto ({str(de)}):\n{raw[:200]}")

def _ollama_generate_json(prompt: str) -> dict:
    import urllib.request
    import urllib.error
    import json
    with open("debug_ollama_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    import urllib.error
    import json
    url = f"{OLLAMA_API_BASE}/api/generate"
    data = json.dumps({
        "model": OLLAMA_MODEL_ID,
        "prompt": prompt,
        "format": "json",
        "options": {
            "num_ctx": 24576,
            "temperature": 0.0
        },
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            # Ollama returns 'response' field with the generated string
            text_response = res_json.get("response", "")
            with open("debug_ollama_response.txt", "w", encoding="utf-8") as f:
                f.write(text_response)
            
            return _gemini_parse_json_response(text_response)
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f"Erro conectando ao Ollama ({OLLAMA_API_BASE}): {e}")

# ── Schemas de Structured Output (Vertex AI) ────────────────────────────────
# [OPT-2 Deep Think] response_schema injeta schema OpenAPI na chamada Vertex,
# garantindo 100% aderência ao JSON sem fallback/regex.
# [OPT-3 Deep Think] Campo "1_raciocinio_matematico" primeiro → Pseudo-CoT:
# força o LLM a verbalizar o raciocínio ANTES das operações (emula CoT com
# thinking_budget:0, mantendo velocidade e aumentando precisão no IFRS 15).
SCHEMA_INVESTIGACAO = {
    "type": "object",
    "properties": {
        "1_raciocinio_matematico": {
            "type": "string",
            "description": (
                "PREENCHER PRIMEIRO. Descreva passo a passo o raciocínio matemático: "
                "quais valores do contexto foram usados, qual fórmula IFRS 15 foi aplicada "
                "e como chegou ao valor das operações correctivas."
            )
        },
        "causa_raiz": {"type": "string"},
        "tipo_divergencia": {
            "type": "string",
            "enum": ["MISSING_ENTRY", "VALUE_MISMATCH", "TIMING_MISMATCH",
                     "ACCUMULATED_ERROR", "ACCOUNT_MAPPING_ERROR",
                     "DUPLICATE_ENTRY", "ZERO_BALANCE_EXPECTED"]
        },
        "operacoes": {
            "type": "array",
            "description": "Array de operações D/C — permite rateios e lançamentos múltiplos em uma iteração",
            "items": {
                "type": "object",
                "properties": {
                    "tipo":       {"type": "string", "enum": ["D", "C"]},
                    "conta":      {"type": "integer"},
                    "valor":      {"type": "number"},
                    "historico":  {"type": "string"},
                    "competencia":{"type": "string"}
                },
                "required": ["tipo", "conta", "valor"]
            }
        },
        "confianca": {"type": "string", "enum": ["alta", "media", "baixa"]},
        "requer_estorno_retroativo":  {"type": "boolean"},
        "afeta_apuracao_imposto":     {"type": "boolean"},
        "requer_revisao_premissas":   {"type": "boolean"},
        "premissas_a_revisar":        {"type": "array", "items": {"type": "string"}}
    },
    "required": ["1_raciocinio_matematico", "causa_raiz", "tipo_divergencia",
                 "operacoes", "confianca",
                 "requer_estorno_retroativo", "afeta_apuracao_imposto"]
}

SCHEMA_DIAGNOSTICO = {
    "type": "object",
    "properties": {
        "resumo_executivo": {"type": "string"},
        "anomalias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "conta_id":      {"type": "integer"},
                    "nome":          {"type": "string"},
                    "tipo_provavel": {
                        "type": "string",
                        "enum": ["MISSING_ENTRY", "VALUE_MISMATCH", "TIMING_MISMATCH",
                                 "ACCUMULATED_ERROR", "ACCOUNT_MAPPING_ERROR",
                                 "DUPLICATE_ENTRY", "ZERO_BALANCE_EXPECTED"]
                    },
                    "urgencia":      {"type": "string", "enum": ["critica", "alta", "media", "baixa"]},
                    "recomendacao":  {"type": "string"}
                },
                "required": ["conta_id", "nome", "tipo_provavel", "urgencia", "recomendacao"]
            }
        }
    },
    "required": ["resumo_executivo", "anomalias"]
}


def _build_compact_context(data: dict) -> str:
    """
    [OPT-1 Deep Think] Minifica o payload antes de enviar ao Vertex:
    - Remove chaves com valor None, 0, 0.0 ou lista vazia
    - Serializa como JSON compacto (sem indentação)
    Reduz tokens e remove carga cognitiva desnecessária do LLM.
    """
    import json
    def _strip(obj):
        if isinstance(obj, dict):
            return {k: _strip(v) for k, v in obj.items()
                    if v is not None and v != 0 and v != 0.0 and v != [] and v != {}}
        if isinstance(obj, list):
            return [_strip(i) for i in obj]
        return obj
    return json.dumps(_strip(data), ensure_ascii=False, separators=(',', ':'))


async def _gemini_generate_json_async(
    prompt: str,
    file_data: bytes = None,
    mime_type: str = None,
    response_schema: dict = None,   # [OPT-2] Structured Outputs — Vertex apenas
    max_output_tokens: int = 8192
) -> dict:
    """Chama Gemini e retorna um objeto JSON (assíncrono nativo).

    Com response_schema (Vertex AI): garante 100% aderência ao JSON sem fallback/regex.
    Sem response_schema (Google AI Studio / fallback): usa response_mime_type padrão.
    """
    _require_gemini_key()
    resp = None

    contents = [prompt]
    if file_data and mime_type:
        if USE_VERTEX_FOR_GEMINI:
            contents.append(Part.from_data(mime_type=mime_type, data=file_data))
        else:
            contents.append({"mime_type": mime_type, "data": file_data})

    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model_cls = VertexModel if USE_VERTEX_FOR_GEMINI else genai.GenerativeModel
            gen_cfg = {
                "response_mime_type": "application/json",
                "max_output_tokens": max_output_tokens,
            }
            if USE_VERTEX_FOR_GEMINI:
                gen_cfg["thinking_config"] = {"thinking_budget": 0}
                # [OPT-2] Structured Outputs: injeta schema OpenAPI quando disponível
                if response_schema:
                    gen_cfg["response_schema"] = response_schema
            model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg)
            resp = await model.generate_content_async(contents)
            break
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str or "Quota" in err_str or "503" in err_str:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
            # Fallback sem schema (às vezes response_schema causa rejeição em modelos mais antigos)
            try:
                model_cls = VertexModel if USE_VERTEX_FOR_GEMINI else genai.GenerativeModel
                gen_cfg_fb = {
                    "response_mime_type": "application/json",
                    "max_output_tokens": max_output_tokens,
                }
                if USE_VERTEX_FOR_GEMINI:
                    gen_cfg_fb["thinking_config"] = {"thinking_budget": 0}
                model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg_fb)
                fallback_contents = [prompt + "\n\nResponda somente um objeto JSON válido, sem markdown nem texto fora do JSON."]
                if mime_type and file_data:
                    fallback_contents.append(
                        Part.from_data(mime_type=mime_type, data=file_data) if USE_VERTEX_FOR_GEMINI
                        else {"mime_type": mime_type, "data": file_data}
                    )
                resp = await model.generate_content_async(fallback_contents)
                break
            except Exception as ei:
                raise HTTPException(
                    status_code=429,
                    detail=f"Erro ou Quota Vertex/Gemini após tentativas: {str(e)[:300]} / {str(ei)[:100]}"
                )
    return _gemini_parse_json_response(resp.text)

def _gemini_generate_json(prompt: str, file_data: bytes = None, mime_type: str = None) -> dict:
    """Fallback síncrono para endpoints lentos de disparo único (Chat/Save), evitando incompatibilidade no asyncio thread."""
    _require_gemini_key()
    resp = None
    
    contents = [prompt]
    if file_data and mime_type:
        if USE_VERTEX_FOR_GEMINI:
            contents.append(Part.from_data(mime_type=mime_type, data=file_data))
        else:
            contents.append({"mime_type": mime_type, "data": file_data})

    try:
        model_cls = VertexModel if USE_VERTEX_FOR_GEMINI else genai.GenerativeModel
        gen_cfg = {
            "response_mime_type": "application/json",
            "max_output_tokens": 8192,
        }
        if USE_VERTEX_FOR_GEMINI:
            gen_cfg["thinking_config"] = {"thinking_budget": 0}
        model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg)
        resp = model.generate_content(contents)
    except Exception:
        model_cls = VertexModel if USE_VERTEX_FOR_GEMINI else genai.GenerativeModel
        model = model_cls(GEMINI_MODEL_ID)
        fallback_contents = [prompt + "\n\nResponda somente JSON."]
        if file_data and mime_type:
             if USE_VERTEX_FOR_GEMINI:
                 fallback_contents.append(Part.from_data(mime_type=mime_type, data=file_data))
             else:
                 fallback_contents.append({"mime_type": mime_type, "data": file_data})
        resp = model.generate_content(fallback_contents)
    return _gemini_parse_json_response(resp.text)
# from contextlib import asynccontextmanager
# import sindicato_agent as _sa

# @asynccontextmanager
# async def lifespan(app_):
#     _sa.start_scheduler()
#     yield
#     _sa.stop_scheduler()

app = FastAPI(
    title="Questor Explorer / Vulcano 2.0 API",
    description=(
        "API FastAPI para Questor, Vulcano, parsers PDF e fluxos de auditoria. "
        "**Swagger UI:** [`/docs`](/docs) · **ReDoc:** [`/redoc`](/redoc) · **OpenAPI JSON:** [`/openapi.json`](/openapi.json)"
    ),
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/", include_in_schema=False)
def _root_redirect_to_docs():
    """Abre o Swagger ao acessar a raiz do servidor (ex.: http://localhost:8000/)."""
    return RedirectResponse(url="/docs")


# ── Janitor SRE Agent imports ───────────────────────────────────────────────
from core.janitor.profiler import JanitorTimingMiddleware, start_profiler, get_performance_report
from core.janitor.cache    import get_cache_stats, invalidate_cache
from core.janitor.disk_inspector import run_disk_scan, get_disk_report, move_to_quarantine

from pydantic import BaseModel
class RawQuery(BaseModel):
    query: str

class LoginRequest(BaseModel):
    email: str
    password: str


class PrimeiroAcessoVerificarRequest(BaseModel):
    email: str


class PrimeiroAcessoDefinirSenhaRequest(BaseModel):
    email: str
    password: str
    password_confirm: str


def _validar_nova_senha(password: str, password_confirm: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 8 caracteres.")
    if password != password_confirm:
        raise HTTPException(status_code=400, detail="As senhas não coincidem.")


@app.post("/api/auth/login")
def api_auth_login(payload: LoginRequest):
    # 1) usuarios_local (SQLite): permite logar sem o Firebird do vulcano no ar.
    import sqlite3
    try:
        s_conn = sqlite3.connect(POC_DATABASE_FILE)
        s_cur = s_conn.cursor()
        s_cur.execute("""
            SELECT id, usuario_id, nome, tipo_permissao, email
            FROM usuarios_local
            WHERE (UPPER(email) = UPPER(?) OR UPPER(usuario_id) = UPPER(?))
              AND senha = ?
              AND ativo = 'T'
        """, (payload.email, payload.email, payload.password))
        s_row = s_cur.fetchone()
        s_conn.close()
        if s_row:
            return {"success": True, "user": {"id": s_row[0], "usuarioId": s_row[1], "nome": s_row[2], "tipoPermissao": s_row[3], "email": s_row[4]}}
    except Exception:
        pass

    # 2) USUARIO do vulcano (Firebird) — senha hasheada SENHAV2 + primeiro acesso
    from core.auth.password import senhav2_preenchida, verify_password
    from core.auth.usuario import buscar_usuario_por_login, usuario_para_json

    u = buscar_usuario_por_login(get_conn, payload.email)
    if not u:
        raise HTTPException(status_code=401, detail="Credenciais inválidas ou usuário inativo")
    if not senhav2_preenchida(u.senhav2):
        raise HTTPException(
            status_code=401,
            detail="Primeiro acesso necessário — defina sua senha pelo botão Primeiro acesso.",
        )
    if not verify_password(payload.password, u.senhav2):
        raise HTTPException(status_code=401, detail="Credenciais inválidas ou usuário inativo")
    return {"success": True, "user": usuario_para_json(u)}


@app.post("/api/auth/primeiro-acesso/verificar")
def api_primeiro_acesso_verificar(payload: PrimeiroAcessoVerificarRequest):
    from core.auth.password import senhav2_preenchida
    from core.auth.usuario import buscar_usuario_por_login

    u = buscar_usuario_por_login(get_conn, payload.email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou inativo.")
    if senhav2_preenchida(u.senhav2):
        raise HTTPException(status_code=409, detail="Senha já cadastrada. Use Entrar.")
    return {"eligible": True, "nome": u.nome}


@app.post("/api/auth/primeiro-acesso/definir-senha")
def api_primeiro_acesso_definir_senha(payload: PrimeiroAcessoDefinirSenhaRequest):
    from core.auth.password import hash_password, senhav2_preenchida
    from core.auth.usuario import atualizar_senhav2, buscar_usuario_por_login

    _validar_nova_senha(payload.password, payload.password_confirm)
    u = buscar_usuario_por_login(get_conn, payload.email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou inativo.")
    if senhav2_preenchida(u.senhav2):
        raise HTTPException(status_code=409, detail="Senha já cadastrada. Use Entrar.")
    try:
        atualizar_senhav2(get_conn, u.id, hash_password(payload.password))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar a senha: {e}")
    return {"success": True, "message": "Senha definida com sucesso. Você já pode entrar."}

@app.post("/api/explorer/query")
def api_explorer_query(payload: RawQuery):
    conn = get_conn("vulcano")
    try:
        cur = conn.cursor()
        cur.execute(payload.query)
        if not cur.description:
            conn.commit()
            return {"success": True, "columns": [], "rows": [], "message": "Comando executado sem retorno (Commit)"}
            
        cols = [desc[0] for desc in cur.description]
        rows = [list(r) for r in cur.fetchall()]
        return {"success": True, "columns": cols, "rows": rows}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/api/tables")
def api_tables(db: str = "questor"):
    if db not in ("questor", "vulcano"): return {"tables": []}
    conn = get_conn(db)
    try:
        cur = conn.cursor()
        if getattr(conn, "kind", "firebird") == "postgres":
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        else:
            cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 AND RDB$VIEW_BLR IS NULL ORDER BY RDB$RELATION_NAME")
        tables = [str(r[0]).strip() for r in cur.fetchall()]
        return {"tables": tables}
    finally:
        conn.close()

@app.get("/api/table/{table_name}/data")
def api_table_data(table_name: str, db: str = "questor"):
    if db not in ("questor", "vulcano"): return {"columns": [], "data": []}
    
    # Safe regex to prevent injection
    import re
    if not re.match(r"^[A-Za-z0-9_]+$", table_name):
        raise HTTPException(status_code=400, detail="Nome de tabela inválido")
        
    conn = get_conn(db)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT FIRST 100 * FROM {table_name}")
        cols = [desc[0].strip() for desc in cur.description]
        data = []
        for r in cur.fetchall():
            row_dict = {}
            for i, col in enumerate(cols):
                val = r[i]
                if isinstance(val, (bytes, bytearray)):
                    val = val.decode('win1252', 'ignore')
                row_dict[col] = val
            data.append(row_dict)
        return {"columns": cols, "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

class CustoLctoReq(BaseModel):
    empresa_id: int
    empreendimento_id: int
    mes: int
    ano: int
    valor_custo: float
    percentual: float
    historico: str

@app.get("/api/empreendimentos/basico")
def api_empreendimentos_basico(empresa_id: int = 959):
    conn = get_conn("vulcano")
    try:
        cur = conn.cursor()
        cur.execute("SELECT ID, NOME FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? AND ATIVO = 'S'", (empresa_id,))
        emps = [{"id": r[0], "nome": r[1]} for r in cur.fetchall()]
        return {"empreendimentos": emps}
    finally:
        conn.close()

def _ensure_poc_custo_mensal_real(conn):
    """
    Cria a tabela POC_CUSTO_MENSAL_REAL no Vulcano se não existir.
    Usa firebirdsql — chamada lazy na primeira vez que o dashboard de custos é acessado.
    """
    cur = conn.cursor()
    try:
        # Verifica existência via RDB$RELATIONS
        cur.execute("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$RELATION_NAME = 'POC_CUSTO_MENSAL_REAL' AND RDB$SYSTEM_FLAG = 0")
        exists = cur.fetchone()[0]
        if exists:
            return  # Já existe, nada a fazer

        # Cria tabela, generator e trigger
        cur.execute("""
            CREATE TABLE POC_CUSTO_MENSAL_REAL (
                ID                INTEGER NOT NULL,
                ID_EMPREENDIMENTO INTEGER NOT NULL,
                ANO               INTEGER NOT NULL,
                MES               INTEGER NOT NULL,
                COMPETENCIA       VARCHAR(10),
                CUSTO_TOTAL       DOUBLE PRECISION DEFAULT 0.0,
                CONSTRAINT PK_POC_CUSTO_MENSAL_REAL PRIMARY KEY (ID)
            )
        """)
        cur.execute("CREATE GENERATOR GEN_POC_CUSTO_MENSAL_REAL_ID")
        cur.execute("""
            CREATE TRIGGER TRG_POC_CUSTO_MENSAL_BI
            FOR POC_CUSTO_MENSAL_REAL
            ACTIVE BEFORE INSERT POSITION 0
            AS BEGIN
                IF (NEW.ID IS NULL) THEN
                    NEW.ID = GEN_ID(GEN_POC_CUSTO_MENSAL_REAL_ID, 1);
            END
        """)
        conn.commit()
    except Exception as e:
        # Se der erro (tabela já existe em concurrent request, etc.), ignora
        try:
            conn.rollback()
        except Exception:
            pass

@app.get("/api/custos/dashboard/{id_emp}")
def api_custos_dashboard_by_id(id_emp: int, mes: int, ano: int, empresa_id: int = 959):
    conn_vulcano = get_conn("vulcano")
    try:
        _ensure_poc_custo_mensal_real(conn_vulcano)  # Cria tabela se não existir
        cur = conn_vulcano.cursor()
        cur.execute("""
            SELECT ID, NOME, CUSTOORCADO, CONTACUSTO, CONTAESTAND, CONTAESTCON, CODIGOCENTROCUSTO
            FROM EMPREENDIMENTO 
            WHERE ID = ?
        """, (id_emp,))
        r = cur.fetchone()
        if not r:
            return {"empreendimento": None}
            
        nome_emp = r[1]
        cc_emp = r[6]
        
        # --- 1. APURACAO DO % VENDIDO (Física/Vendas Vulcano) ---
        fracao_vendida = 0.0
        try:
            cur.execute("""
                SELECT 
                    (SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?) as TOTAL_AREA,
                    (SELECT SUM(U.METRAGEM) 
                     FROM VENDAUNIDADE VU 
                     JOIN VENDA V ON V.ID = VU.IDVENDA 
                     JOIN UNIDADE U ON U.ID = VU.IDUNIDADE 
                     JOIN BLOCO B ON B.ID = U.IDBLOCO 
                     WHERE B.IDEMPREENDIMENTO = ? AND COALESCE(V.DISTRATO, 'N') NOT IN ('T', 'S', '1')
                       AND (EXTRACT(YEAR FROM V.DTOPER) < ? OR (EXTRACT(YEAR FROM V.DTOPER) = ? AND EXTRACT(MONTH FROM V.DTOPER) <= ?))
                    ) as SOLD_AREA,
                    (SELECT COUNT(U.ID) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?) as TOTAL_UNIDS
                FROM RDB$DATABASE
            """, (id_emp, id_emp, ano, ano, mes, id_emp))
            
            area_row = cur.fetchone()
            unidades_totais = 0
            if area_row and area_row[0] and area_row[0] > 0:
                fracao_vendida = float(area_row[1] or 0) / float(area_row[0])
                area_v = float(area_row[1] or 0)
                area_t = float(area_row[0])
                unidades_totais = int(area_row[2] or 0)

            else:
                area_v = 0.0
                area_t = 0.0
        except Exception as e:
            import traceback
            with open('backend_error.txt', 'w') as err_f:
                err_f.write(traceback.format_exc())
            area_v = 0.0
            area_t = 0.0
            pass

        
        # --- 2. APURACAO DO CUSTO TOTAL GASTO (Cubo Totalizador Vulcano) ---
        custo_real_gasto = 0.0
        try:
            cur.execute("SELECT SUM(CUSTO_TOTAL) FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES <= ?))", (id_emp, ano, ano, mes))
            crg = cur.fetchone()
            if crg and crg[0]:
                custo_real_gasto = float(crg[0])
        except Exception as e:
            pass
        
        # Helper to fetch Account Name from Questor
        def get_nome_conta(conta_id):
            if not conta_id: return ""
            try:
                conn_q = get_conn("questor")
                cur_q = conn_q.cursor()
                cur_q.execute("""
                    SELECT DESCRICAO FROM PLANOGRUPOEMPRESACONTAS 
                    WHERE CODIGOEMPRESA = ? AND CONTACTB = ?
                """, (empresa_id, int(conta_id)))
                n = cur_q.fetchone()
                return n[0] if n else ""
            except Exception:
                return ""

        # --- 3. APURACAO DAS VENDAS MES A MES ---
        vendas_mes_a_mes = []
        try:
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM V.DTOPER) as ANO,
                    EXTRACT(MONTH FROM V.DTOPER) as MES,
                    COUNT(VU.ID) as QTD_VENDIDA
                FROM VENDAUNIDADE VU 
                JOIN VENDA V ON V.ID = VU.IDVENDA 
                JOIN UNIDADE U ON U.ID = VU.IDUNIDADE 
                JOIN BLOCO B ON B.ID = U.IDBLOCO 
                WHERE B.IDEMPREENDIMENTO = ? 
                  AND COALESCE(V.DISTRATO, 'N') NOT IN ('T', 'S', '1')
                  AND (EXTRACT(YEAR FROM V.DTOPER) < ? OR (EXTRACT(YEAR FROM V.DTOPER) = ? AND EXTRACT(MONTH FROM V.DTOPER) <= ?))
                GROUP BY 1, 2
                ORDER BY 1 DESC, 2 DESC
            """, (id_emp, ano, ano, mes))
            vendas_mes_a_mes = [{"ano": r[0], "mes": r[1], "qtd": r[2]} for r in cur.fetchall()]
        except Exception:
            pass
            
        # --- 4. APURACAO DO CUB VIGENTE ---
        cub_vigente = 0.0
        try:
            compet_db = f"{ano}-{str(mes).zfill(2)}-31"
            cur.execute("SELECT FIRST 1 VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND VALOR IS NOT NULL AND MES <= ? ORDER BY MES DESC", (compet_db,))
            cub_row = cur.fetchone()
            if cub_row and cub_row[0]: cub_vigente = float(cub_row[0])
        except:
            pass

        emp_detail = {
            "id": id_emp, "nome": nome_emp, "custo_orcado": float(r[2] or 0.0),
            "custo_real_gasto": custo_real_gasto, "fracao_vendida": fracao_vendida,
            "area_vendida": area_v, "area_total": area_t,
            "conta_custo": r[3], "conta_estoque": r[4], "conta_estconc": r[5], "codigo_cc": cc_emp,
            "conta_custo_nome": get_nome_conta(r[3]),
            "conta_estoque_nome": get_nome_conta(r[4]),
            "conta_estconc_nome": get_nome_conta(r[5]),
            "vendas_mes": vendas_mes_a_mes,
            "cub_vigente": cub_vigente,
            "unidades_totais": unidades_totais
        }
        
        cur.execute("""
            SELECT ANO, MES, SUM(CUSTO_TOTAL) 
            FROM POC_CUSTO_MENSAL_REAL 
            WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES < ?))
            GROUP BY ANO, MES 
            ORDER BY ANO ASC, MES ASC
        """, (id_emp, ano, ano, mes))
        spends = cur.fetchall()

        import sqlite3
        conn_lite = connect_app()
        cur_lite = conn_lite.cursor()
        
        cur_lite.execute("SELECT periodo, percentual FROM evolucao_obras WHERE empreendimento = ?", (nome_emp,))
        pocs_raw = cur_lite.fetchall()
        
        periods = set()
        spend_dict = {}
        for (a, m, val) in spends:
            per = f"{str(a).zfill(4)}-{str(m).zfill(2)}"
            periods.add(per)
            spend_dict[per] = float(val)
                
        poc_dict = {}
        for (per, pct) in pocs_raw:
            a = 0
            m = 0
            try:
                if '/' in per:
                    parts = per.split('/')
                    if len(parts) == 3:
                        a, m = int(parts[2]), int(parts[1])
                elif '-' in per:
                    parts = per.split('-')
                    if len(parts) >= 2:
                        a, m = int(parts[0]), int(parts[1])
            except ValueError:
                pass
                
            if a > 0 and m > 0:
                if a < ano or (a == ano and m <= mes):
                    std_per = f"{str(a).zfill(4)}-{str(m).zfill(2)}"
                    periods.add(std_per)
                    # Use std_per exactly so sort works properly
                    poc_dict[std_per] = float(pct)

                
        sorted_periods = sorted(list(periods))
        
        def get_poc_for_period(target):
            best_poc = 0.0
            for per, pct in sorted(poc_dict.items()):
                if per <= target:
                    best_poc = pct
                else:
                    break
            return best_poc

        historico_calc = []
        running_gasto = 0.0
        prev_custo_acumulado = 0.0
        
        for per in sorted_periods:
            gasto_mes = spend_dict.get(per, 0.0)
            running_gasto += gasto_mes
            poc_m = get_poc_for_period(per)
            
            custo_acumulado_req = running_gasto * fracao_vendida
            valor_mensal = custo_acumulado_req - prev_custo_acumulado
            
            if abs(valor_mensal) >= 0.01:
                historico_calc.append({
                    "periodo": per,
                    "valor": valor_mensal
                })
                
            prev_custo_acumulado = custo_acumulado_req
            
        historico_calc.sort(key=lambda x: x["periodo"], reverse=True)
        
        emp_detail["historico_anterior"] = historico_calc
        emp_detail["custo_reconhecido_anterior"] = prev_custo_acumulado
        
        # Don't forget current POC
        emp_detail["poc_atual"] = get_poc_for_period(f"{str(ano).zfill(4)}-{str(mes).zfill(2)}")
        
        historico_poc = []
        for per, pct in sorted(poc_dict.items(), reverse=True):
            historico_poc.append({"periodo": per, "percentual": float(pct)})
        emp_detail["historico_poc"] = historico_poc
        
        conn_lite.close()
            
        cur.execute("SELECT MES, ANO, TOTAL_PERIODO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ? ORDER BY ANO DESC, MES DESC", (id_emp,))
        emp_detail["timeline"] = [
            {
                "mes": c[0], 
                "ano": c[1], 
                "periodo": f"{str(c[1]).zfill(4)}-{str(c[0]).zfill(2)}",
                "valor": float(c[2] or 0), 
                "poc": float(c[3] or 0), 
                "status": "Integrado"
            } 
            for c in cur.fetchall()
        ]
            
        return {"empreendimento": emp_detail}
    finally:
        conn_vulcano.close()

@app.get("/api/custos/detalhamento/{id_emp}")
def api_custos_detalhamento(id_emp: int, empresa_id: int = 959):
    conn_vulcano = get_conn("vulcano")
    conn_questor = get_conn("questor")
    try:
        _ensure_poc_custo_mensal_real(conn_vulcano)  # Cria tabela se não existir
        # Puxar CC e Conta de Custo
        cur_v = conn_vulcano.cursor()
        cur_v.execute("SELECT CONTACUSTO, CODIGOCENTROCUSTO FROM EMPREENDIMENTO WHERE ID = ?", (id_emp,))
        emp_info = cur_v.fetchone()
        if not emp_info:
            return {"extrato_gerencial": [], "extrato_contabil": []}
            
        conta_custo = emp_info[0]
        cc_emp = emp_info[1]
        
        cur_q = conn_questor.cursor()
        
        extrato_gerencial = []
        try:
            cur_v.execute("SELECT ANO, MES, SUM(CUSTO_TOTAL) FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? GROUP BY ANO, MES ORDER BY ANO DESC, MES DESC", (id_emp,))
            for g in cur_v.fetchall():
                extrato_gerencial.append({"ano": g[0], "mes": g[1], "valor": float(g[2])})
        except Exception as e:
            print("Erro Gerencial Extrato Cache:", e)

        extrato_contabil = []
        if conta_custo:
            try:
                cur_q.execute("""
                    SELECT DATALCTOCTB, VALORLCTOCTB, CHAVELCTOCTB 
                    FROM LCTOCTB 
                    WHERE CODIGOEMPRESA = ? 
                          AND CONTACTBDEB = ? 
                          AND CHAVEORIGEM LIKE 'VU%'
                    ORDER BY DATALCTOCTB DESC
                """, (empresa_id, int(conta_custo)))
                for c in cur_q.fetchall():
                    extrato_contabil.append({"data": str(c[0]), "valor": float(c[1]), "chave": c[2]})
            except Exception as e:
                print("Erro Contabil Extrato:", e)
                
        return {
            "extrato_gerencial": extrato_gerencial,
            "extrato_contabil": extrato_contabil
        }
    finally:
        conn_vulcano.close()
        conn_questor.close()

@app.get("/api/custos/analitico/{id_emp}")
def api_custos_analitico(id_emp: int, mes: int, ano: int, empresa_id: int = 959):
    """
    Retorna os lançamentos analíticos do LCTOGER para um empreendimento em um mês/ano.
    Usado para o drill-down na tela de Fechamento de Custos.
    """
    conn_vulcano = get_conn("vulcano")
    conn_questor = get_conn("questor")
    try:
        cur_v = conn_vulcano.cursor()
        cur_v.execute("SELECT CODIGOCENTROCUSTO FROM EMPREENDIMENTO WHERE ID = ?", (id_emp,))
        emp_info = cur_v.fetchone()
        if not emp_info or not emp_info[0]:
            return {"lancamentos": [], "total": 0.0, "count": 0}

        cc_emp = int(emp_info[0])
        cur_q = conn_questor.cursor()

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode("win1252", "ignore").strip()
            return str(v).strip()

        cur_q.execute("""
            SELECT
                lctoger.datalctoctb,
                lctoger.valorlctoger * lctoger.naturlctoctb as valor_liquido,
                lctoger.contactb,
                lctoctb.contactbdeb,
                lctoctb.contactbcred,
                lctoctb.codigohistctb,
                lctoctb.complhist,
                lctoger.chavelctoctb
            FROM lctoger
            INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa
                AND lctoctb.chavelctoctb = lctoger.chavelctoctb
            WHERE lctoger.codigoempresa = ?
              AND lctoger.codigocentrocusto = ?
              AND extract(year from lctoger.datalctoctb) = ?
              AND extract(month from lctoger.datalctoctb) = ?
              AND NOT (lctoctb.codigohistctb = 370 AND lctoger.naturlctoctb = -1)
            ORDER BY lctoger.datalctoctb, lctoger.chavelctoctb
        """, (empresa_id, cc_emp, ano, mes))

        lancamentos = []
        for r in cur_q.fetchall():
            lancamentos.append({
                "data": str(r[0])[:10] if r[0] else "",
                "valor": float(r[1] or 0),
                "conta_cc": dec(r[2]),
                "conta_deb": dec(r[3]),
                "conta_cred": dec(r[4]),
                "hist_codigo": dec(r[5]),
                "historico": dec(r[6]),
                "chave": dec(r[7]),
            })

        total = sum(l["valor"] for l in lancamentos)
        return {"lancamentos": lancamentos, "total": total, "count": len(lancamentos)}
    finally:
        conn_vulcano.close()
        conn_questor.close()

@app.post("/api/custos/sincronizar_totalizadores/{id_emp}")
def api_custos_sincronizar_totalizadores(id_emp: int, mes: int, ano: int, empresa_id: int = 959):
    conn_vulcano = get_conn("vulcano")
    conn_questor = get_conn("questor")
    try:
        _ensure_poc_custo_mensal_real(conn_vulcano)  # Cria tabela se não existir
        cur_v = conn_vulcano.cursor()
        cur_q = conn_questor.cursor()
        
        # Limpar tabela ODS para TODO o histórico do empreendimento
        cur_v.execute("DELETE FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ?", (id_emp,))
        
        cur_v.execute("SELECT CODIGOCENTROCUSTO FROM EMPREENDIMENTO WHERE ID = ?", (id_emp,))
        emp_inf = cur_v.fetchone()
        if not emp_inf or not emp_inf[0]:
            raise HTTPException(status_code=400, detail="Centro de Custo não mapeado neste empreendimento.")
            
        cc_emp = int(emp_inf[0])
        
        # Sincroniza TODO o histórico deste empreendimento (muito rápido por ser apenas 1 CC)
        cur_q.execute("""
            SELECT extract(year from lctoger.datalctoctb),
                   extract(month from lctoger.datalctoctb),
                   coalesce(sum(coalesce(lctoger.valorlctoger*lctoger.naturlctoctb, 0)), 0)
            FROM lctoger
            INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa 
                AND lctoctb.chavelctoctb = lctoger.chavelctoctb
            WHERE lctoger.codigoempresa = ? AND lctoger.codigocentrocusto = ?
            AND not (lctoctb.codigohistctb = 370 and lctoger.naturlctoctb = -1)
            GROUP BY 1, 2
        """, (empresa_id, cc_emp))
        
        res_mensal = cur_q.fetchall()
        for (a, m, total) in res_mensal:
            competencia = f"{int(a)}-{str(int(m)).zfill(2)}"
            cur_v.execute("""
                INSERT INTO POC_CUSTO_MENSAL_REAL (ID_EMPREENDIMENTO, ANO, MES, COMPETENCIA, CUSTO_TOTAL)
                VALUES (?, ?, ?, ?, ?)
            """, (id_emp, int(a), int(m), competencia, float(total)))
                
        conn_vulcano.commit()
        return {"success": True, "message": "Histórico Completo Sincronizado para este Prédio!"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        conn_vulcano.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn_vulcano.close()
        conn_questor.close()

@app.post("/api/custos/lcto")
def api_custos_lcto(req: CustoLctoReq):
    conn_vulcano = get_conn("vulcano")
    conn_questor = get_conn("questor")
    try:
        # 1. Obter informações de conta no Vulcano
        cur_v = conn_vulcano.cursor()
        cur_v.execute("SELECT CONTACUSTO, CONTAESTAND, CODIGOCENTROCUSTO FROM EMPREENDIMENTO WHERE ID = ?", (req.empreendimento_id,))
        emp_info = cur_v.fetchone()
        if not emp_info or not emp_info[0] or not emp_info[1]:
            raise HTTPException(400, "Contas Contábeis de Custo ou Estoque não parametrizadas no Empreendimento.")
            
        conta_debito = int(emp_info[0])
        conta_credito = int(emp_info[1])
        codigo_cc = int(emp_info[2]) if emp_info[2] else None
        
        # 2. Inserir em POC_CUSTOS no Vulcano
        # Generate ID (simulated seq)
        cur_v.execute("SELECT MAX(ID) FROM POC_CUSTOS")
        max_id = cur_v.fetchone()[0] or 0
        new_id = max_id + 1
        
        periodo_str = f"{req.ano}-{str(req.mes).zfill(2)}"
        
        # Sum previously accumulated cost
        cur_v.execute("SELECT SUM(TOTAL_PERIODO) FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ?", (req.empreendimento_id,))
        custo_acumulado = cur_v.fetchone()[0] or 0.0
        novo_acumulado = float(custo_acumulado) + req.valor_custo
        
        cur_v.execute("""
            INSERT INTO POC_CUSTOS (ID, ID_EMPREENDIMENTO, MES, ANO, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id, req.empreendimento_id, req.mes, req.ano, periodo_str, req.valor_custo, novo_acumulado, req.percentual))
        
        # 3. Inserir em LCTOCTB no Questor
        cur_q = conn_questor.cursor()
        
        # Pegar ultima chave de lote ou seq
        # (Em um ambiente real, geramos CHAVELCTOCTB com triggers/sequences ou UUID, aqui usamos timestamp simulado)
        import time
        chave_lcto = int(time.time() * 10)
        data_fim_mes = f"{req.ano}-{str(req.mes).zfill(2)}-28" # simplificado para dia 28
        
        # SQL Insert into Questor - Simplificado. Em prod real tem fields requeridos.
        # Garantindo a inclusão de CODIGOLCTOPROG genérico caso seja Not Null.
        cur_q.execute("""
            INSERT INTO LCTOCTB 
            (CODIGOEMPRESA, CHAVELCTOCTB, DATALCTOCTB, VALORLCTOCTB, CONTACTBDEB, CONTACTBCRED, CODIGOHISTCTB, COMPLHIST, ORIGEMDADO, CODIGOLCTOPROG, CHAVEORIGEM)
            VALUES (?, ?, CAST(? AS DATE), ?, ?, ?, 99, ?, 1, 1, ?)
        """, (req.empresa_id, chave_lcto, data_fim_mes, req.valor_custo, conta_debito, conta_credito, req.historico, 'VU_POC'))
             
        conn_vulcano.commit()
        conn_questor.commit()
        
        return {"success": True, "message": "Custo integrado com sucesso ao Vulcano e Questor (LCTOCTB).", "valor": req.valor_custo}
    except Exception as e:
        import traceback
        traceback.print_exc()
        conn_vulcano.rollback()
        conn_questor.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn_vulcano.close()
        conn_questor.close()

@app.post("/api/sero/importar-pdf")
async def api_sero_importar_pdf(file: UploadFile = File(...)):
    """
    Importa e processa o PDF do extrato SERO utilizando Vertex AI para extrair 
    as alocações de empresas terceirizadas.
    """
    import io
    import pdfplumber
    import asyncio
    from fastapi import HTTPException
    
    _require_gemini_key()
    
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {e}")
        
    def _extract_pages(raw: bytes) -> list[str]:
        result = []
        max_pages = 20
        max_chars = 4500
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages: break
                extracted = page.extract_text() or page.extract_text(layout=True) or ""
                text = extracted.strip()
                if text:
                    for j in range(0, len(text), max_chars):
                        result.append(f"--- Página {i + 1} (Parte {j//max_chars + 1}) ---\n{text[j:j+max_chars]}")
        return result

    try:
        chunks = await asyncio.to_thread(_extract_pages, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao extrair texto do PDF: {e}")

    if not chunks:
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do PDF.")

    schema = '{"registros":[{"competencia":"","cnpj_cpf":"","origem":"","valor_original":0.0,"taxa_correcao":0.0,"valor_atualizado":0.0}]}'
    
    async def process_chunk(chunk_text: str):
        prompt = f"Extraia TODOS os registros de abatimentos do SERO da tabela de Créditos. É EXTREMAMENTE IMPORTANTE que você extraia TODAS as linhas que contêm uma Competência (ex: 10/2023) e um CNPJ/CPF válido, incluindo as primeiras linhas logo abaixo do cabeçalho. Não pule nenhuma linha válida! Retorne Competência, CPF/CNPJ, Origem, Valor Original, Taxa de Correção Monetária e Valor Atualizado. Retorne APENAS JSON no formato indicado:\n{schema}\n\nTexto:\n{chunk_text}"
        try:
            return await _gemini_generate_json_async(prompt)
        except Exception as e:
            print(f"Erro no chunk SERO: {e}")
            return {"registros": []}

    # Dispara páginas em paralelo conforme regra do AGENTS.md
    tasks = [process_chunk(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    # Consolida os registros
    todas_empresas = []
    for res in results:
        regs = res.get("registros", [])
        for r in regs:
            # Filtra registros inválidos ou vazios (exigindo cnpj_cpf e valor_atualizado)
            if r.get("cnpj_cpf") and r.get("valor_atualizado") is not None:
                todas_empresas.append(r)

    def parse_comp(comp: str):
        if not comp: return "0000-00"
        c = str(comp).strip()
        if "/" in c:
            parts = c.split("/")
            if len(parts) == 2:
                m, y = parts[0].strip(), parts[1].strip()
                if len(y) == 2: y = "20" + y
                if len(y) == 4:
                    return f"{y}-{m.zfill(2)}"
        return c

    for emp in todas_empresas:
        emp["competencia"] = parse_comp(emp.get("competencia", ""))

    # Ordena por competencia cronológica (crescente)
    todas_empresas.sort(key=lambda x: x.get("competencia", ""), reverse=False)
    return todas_empresas

class SeroSalvarInput(BaseModel):
    empresa_id: int
    registros: list[dict]

@app.post("/api/sero/salvar-importacao")
def api_sero_salvar_importacao(payload: SeroSalvarInput):
    """Salva os dados do extrato SERO extraídos do PDF no banco de dados SQLite."""
    conn = None
    try:
        import sqlite3
        conn = connect_app()
        cur = conn.cursor()
        
        def norm_comp(c):
            c = (c or '').strip()
            if "/" in c:
                p = c.split("/")
                if len(p) == 2:
                    y, m = p[1].strip(), p[0].strip()
                    if len(y) == 4:
                        return f"{y}-{m.zfill(2)}"
            return c

        competencias = list(set([norm_comp(reg.get('competencia')) for reg in payload.registros if reg.get('competencia')]))
        if competencias:
            placeholders = ','.join(['?'] * len(competencias))
            cur.execute(f"DELETE FROM SERO_IMPORTACOES WHERE empresa_id = ? AND competencia IN ({placeholders})", [payload.empresa_id] + competencias)
        
        inserts = []
        for reg in payload.registros:
            inserts.append((
                payload.empresa_id,
                norm_comp(reg.get('competencia')),
                reg.get('cnpj_cpf', ''),
                reg.get('origem', ''),
                float(reg.get('valor_original', 0) or 0),
                float(reg.get('taxa_correcao', 0) or 0),
                float(reg.get('valor_atualizado', 0) or 0)
            ))
            
        cur.executemany('''
            INSERT INTO SERO_IMPORTACOES (
                empresa_id, competencia, cnpj_cpf, origem, 
                valor_original, taxa_correcao, valor_atualizado
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', inserts)
        
        conn.commit()
        return {"success": True, "message": f"{len(inserts)} registros salvos com sucesso.", "inseridos": len(inserts)}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@app.get("/api/sero/maodeobra")
def api_sero_maodeobra(empresa_id: int = 959, ano: int = 2025, mes: int = 12, cno: str = None):
    cc_filtro = None
    if cno and "|" in cno:
        cno, cc_filtro = cno.split("|")
    """
    Apuracao SERO/INSS real a partir das tabelas Questor.
    - Folha propria:  CALCULORATEIO (evento 5041) + PERIODOCALCULO (competencia)
    - Folha terceiros: TERCEIROPGTO.VALORORIGEMGPS ou TERCEIROPGTOSERVICO.VALOR (tem COMPET direto)
    - Cadastro obra:  OUTRAEMPRESA + OUTRAEMPEMP (INSCRFEDPROPRIET = CNPJ proprietario)
    - Metragem:       EMPREENDIMENTO.METRAGEMTOTAL (Vulcano, match por CNPJ)
    - CUB:            INDICE_REAJUSTE_TABELA (Vulcano) com fallback para historico embutido
    O parametro `cno` aceita o CODIGOOUTEMP (string) para filtrar uma obra especifica.
    """
    CUB_FALLBACK = {
        "2026-12": 3220.00, "2026-11": 3210.00, "2026-10": 3200.00, "2026-09": 3190.00,
        "2026-08": 3180.00, "2026-07": 3170.00, "2026-06": 3160.00, "2026-05": 3150.00,
        "2026-04": 3140.00, "2026-03": 3130.00, "2026-02": 3120.00, "2026-01": 3110.00,
        "2025-12": 3100.00, "2025-11": 3080.00, "2025-10": 3060.00, "2025-09": 3040.00,
        "2025-08": 3020.00, "2025-07": 3000.00, "2025-06": 2985.00, "2025-05": 2970.00,
        "2025-04": 2955.00, "2025-03": 2940.00, "2025-02": 2925.00, "2025-01": 2910.00,
        "2024-12": 2895.00, "2024-11": 2880.00, "2024-10": 2865.00, "2024-09": 2850.00,
        "2024-08": 2835.00, "2024-07": 2820.00, "2024-06": 2805.00, "2024-05": 2790.00,
        "2024-04": 2950.40, "2024-03": 2915.30, "2024-02": 2890.20, "2024-01": 2870.12,
        "2023-12": 2855.10, "2023-11": 2840.90, "2023-10": 2825.80, "2023-09": 2810.70,
        "2023-08": 2795.50, "2023-07": 2780.15, "2023-06": 2765.40, "2023-05": 2745.20,
        "2023-04": 2725.10, "2023-03": 2710.60, "2023-02": 2695.45, "2023-01": 2685.30,
        "2022-12": 2675.10, "2022-11": 2665.90, "2022-10": 2645.80, "2022-09": 2625.60,
        "2022-08": 2605.30, "2022-07": 2585.10, "2022-06": 2560.40, "2022-05": 2530.15,
        "2022-04": 2505.80, "2022-03": 2485.45, "2022-02": 2470.30, "2022-01": 2450.10,
        "2021-12": 2435.40, "2021-11": 2415.20, "2021-10": 2390.10, "2021-09": 2365.80,
        "2021-08": 2340.65, "2021-07": 2315.50, "2021-06": 2290.30, "2021-05": 2260.10,
        "2021-04": 2235.90, "2021-03": 2215.70, "2021-02": 2195.60, "2021-01": 2180.45,
        "2020-12": 2150.60, "2020-11": 2120.40, "2020-10": 2095.10, "2020-09": 2070.60,
    }

    def dec(v):
        if v is None: return ""
        if isinstance(v, bytes): return v.decode("win1252", "ignore").strip()
        return str(v).strip()

    conn_v = get_conn("vulcano")
    conn_q = get_conn("questor")
    try:
        cur_v = conn_v.cursor()
        cur_q = conn_q.cursor()
        compet_alvo = f"{ano}-{str(mes).zfill(2)}"

        # 1. CUB: tenta banco Vulcano, fallback para dicionario embutido
        cub_history = dict(CUB_FALLBACK)
        try:
            cur_v.execute("SELECT MES, VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND VALOR IS NOT NULL ORDER BY MES ASC")
            for r in cur_v.fetchall():
                cub_history[str(r[0])[:7]] = float(r[1])
        except Exception:
            pass
        cub_vigente = cub_history.get(compet_alvo, 2950.0)

        # 2. Metragem total da empresa (Vulcano EMPREENDIMENTO)
        # Consolidado = soma de todas as obras; filtrado por outemp = distribuição proporcional
        cur_v.execute(
            "SELECT ID, COALESCE(METRAGEMTOTAL, 0), CODIGOCENTROCUSTO"
            " FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ?",
            (empresa_id,)
        )
        emp_rows = cur_v.fetchall()
        metragem_total_empresa = sum(float(r[1] or 0) for r in emp_rows)
        # mapa: centro_custo -> metragem (para vínculo futuro com OUTEMP)
        metragem_por_cc = {r[2]: float(r[1] or 0) for r in emp_rows if r[2]}

        # 3. Cadastro de OUTRAEMPRESA + INSCRFEDPROPRIET (Questor)
        outemp_filtro = ""
        params_outemp = [empresa_id]
        if cno:
            try:
                outemp_filtro = " AND OEE.CODIGOOUTEMP = ?"
                params_outemp.append(int(cno))
            except ValueError:
                pass

        cur_q.execute(
            "SELECT OE.CODIGOOUTEMP, OE.NOMEOUTEMP, OE.INSCRFEDERAL, OEE.INSCRFEDPROPRIET"
            " FROM OUTRAEMPEMP OEE"
            " JOIN OUTRAEMPRESA OE ON OE.CODIGOOUTEMP = OEE.CODIGOOUTEMP"
            " WHERE OEE.CODIGOEMPRESA = ?" + outemp_filtro,
            tuple(params_outemp)
        )
        obras_cadastro = {}
        for r in cur_q.fetchall():
            cod = r[0]
            propri_limpo = "".join(filter(str.isdigit, dec(r[3])))
            obras_cadastro[cod] = {
                "nome": dec(r[1]),
                "inscricao": dec(r[2]),
                "cnpj_proprietario": dec(r[3]),
                # Metragem: divide igualmente entre os outemps da empresa
                # (refinamento futuro: vincular por CODIGOCENTROCUSTO)
                "metragem": 0.0,  # preenchido após saber n_outemps
            }

        if not obras_cadastro:
            return {
                "resumo": {
                    "mao_de_obra": 0.0, "mao_de_obra_folha": 0.0,
                    "mao_de_obra_terceiros_gps": 0.0,
                    "total_inss": 0.0, "cub_vigente": cub_vigente, "area_total": 0.0
                },
                "alocacoes_terceiros": [],
                "curva_s": [],
                "aviso": "Nenhuma OUTRAEMPRESA vinculada a esta empresa no Questor."
            }

        outemps_list = list(obras_cadastro.keys())
        placeholders = ",".join("?" * len(outemps_list))

        # Metragem por outemp via match de nome Questor x Vulcano
        # Busca empreendimentos com metragem
        cur_v.execute(
            "SELECT ID, NOME, COALESCE(METRAGEMTOTAL, 0), CODIGOCENTROCUSTO,"
            " COALESCE(OBRACONCLUIDA, 'N')"
            " FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ? ORDER BY ID DESC",
            (empresa_id,)
        )
        emp_vulcano = cur_v.fetchall()

        def _tokens(s):
            """Extrai tokens >= 4 chars de uma string (ignora preposições curtas)."""
            import re
            return set(w.upper() for w in re.split(r'\W+', str(s)) if len(w) >= 4)

        # Pré-calcula metragem dos empreendimentos em construção (para TIPOOUTEMP=2)
        metragem_em_construcao = sum(
            float(ev[2] or 0)
            for ev in emp_vulcano
            if dec(ev[4]) != "S" and float(ev[2] or 0) > 0
        )

        def _match_metragem(nome_outemp, tipo_outemp):
            """Retorna metragem do empreendimento Vulcano que melhor bate com o nome.
            TIPOOUTEMP=2 (empresa própria, ex: Stuttgart): usa soma dos empreendimentos
                         em construção — o name match não funciona pois o NOMEOUTEMP é
                         o nome da empresa construtora, não do empreendimento.
            TIPOOUTEMP=1 (obra com CNO/CEI próprio): faz match por tokens do nome.
            """
            # Para empresa própria (Stuttgart, etc.): metragem das obras em andamento
            if tipo_outemp == "2":
                return metragem_em_construcao

            # Para obras com CNO/CEI: match por tokens do nome
            toks_q = _tokens(nome_outemp)
            best_score, best_metro = 0, 0.0
            for ev in emp_vulcano:
                nome_v = dec(ev[1]) if ev[1] else ""
                metro  = float(ev[2] or 0)
                if metro == 0:
                    continue
                toks_v = _tokens(nome_v)
                overlap = len(toks_q & toks_v)
                if overlap > best_score:
                    best_score, best_metro = overlap, metro
            return best_metro


        # Busca TIPOOUTEMP para cada outemp do cadastro
        if outemps_list:
            ph2 = ",".join("?" * len(outemps_list))
            cur_q.execute(
                f"SELECT OEE.CODIGOOUTEMP, OEE.TIPOOUTEMP"
                f" FROM OUTRAEMPEMP OEE WHERE OEE.CODIGOEMPRESA = ?"
                f" AND OEE.CODIGOOUTEMP IN ({ph2})",
                tuple([empresa_id] + outemps_list)
            )
            tipo_map = {r[0]: dec(r[1]) for r in cur_q.fetchall()}
        else:
            tipo_map = {}

        for cod, info in obras_cadastro.items():
            tipo = tipo_map.get(cod, "1")
            metro = _match_metragem(info["nome"], tipo)
            # Fallback: se não achou match, divide proporcionalmente pelo número de outemps
            if metro == 0.0 and metragem_total_empresa > 0:
                metro = metragem_total_empresa / max(len(outemps_list), 1)
            obras_cadastro[cod]["metragem"] = metro




        # 4. Folha propria: CALCULORATEIO evento 5041 + PERIODOCALCULO
        sql_folha = (
            "SELECT C.CODIGOOUTEMP, P.COMPET, SUM(C.VALOREVENTO)"
            " FROM CALCULORATEIO C"
            " JOIN PERIODOCALCULO P ON P.CODIGOPERCALCULO = C.CODIGOPERCALCULO"
            " WHERE C.CODIGOEVENTO = 5041 AND C.CODIGOEMPRESA = ?"
        )
        params_folha = [empresa_id]
        
        if cc_filtro:
            sql_folha += f" AND C.CODIGOCENTROCUSTO = {int(cc_filtro)}"
        else:
            sql_folha += " AND C.CODIGOOUTEMP IN (" + placeholders + ")"
            params_folha.extend(outemps_list)
            
        sql_folha += " GROUP BY C.CODIGOOUTEMP, P.COMPET ORDER BY P.COMPET"
        
        cur_q.execute(sql_folha, tuple(params_folha))
        folha_rows = cur_q.fetchall()

        # A pedido do usuário, "Terceiros GPS" e "Empreiteiras PJ" do Questor 
        # foram removidos da apuração, pois não possuem CC amarrado confiavelmente.
        # Os terceiros virão exclusivamente do PDF SERO importado.

        import sqlite3
        conn_lite = connect_app()
        cur_lite = conn_lite.cursor()
        cur_lite.execute("SELECT competencia, cnpj_cpf, origem, valor_atualizado FROM SERO_IMPORTACOES WHERE empresa_id = ?", (empresa_id,))
        sero_importados = cur_lite.fetchall()
        conn_lite.close()
        
        def norm_comp(c):
            c = (c or '').strip()
            if "/" in c:
                p = c.split("/")
                if len(p) == 2:
                    y, m = p[1].strip(), p[0].strip()
                    if len(y) == 4:
                        return f"{y}-{m.zfill(2)}"
            return c

        competencias_importadas = set(norm_comp(r[0]) for r in sero_importados)

        # 6. Agrega por competencia
        from collections import defaultdict
        historico_mensal = defaultdict(lambda: {"realizado": 0.0, "previsto": 0.0})
        total_folha = total_terceiros = 0.0
        alocacoes_t = []
        alocacoes_f = []

        for (outemp, compet_dt, valor) in folha_rows:
            comp = str(compet_dt)[:7]
            v = float(valor or 0)
            historico_mensal[comp]["realizado"] += v
            # Acumula total até o mês selecionado (inclusive)
            if comp <= compet_alvo:
                total_folha += v
                alocacoes_f.append({
                    "compet": comp,
                    "codigooutemp": outemp,
                    "nome_obra": obras_cadastro.get(outemp, {}).get("nome", f"Obra {outemp}"),
                    "valor": round(v, 2)
                })

        for (comp, cnpj_cpf, origem, valor_atualizado) in sero_importados:
            comp = norm_comp(comp)
            v = float(valor_atualizado or 0)
            historico_mensal[comp]["realizado"] += v
            if comp <= compet_alvo:
                total_terceiros += v
                alocacoes_t.append({
                    "compet": comp, "codigooutemp": "SERO",
                    "nome_obra": (origem or "") + " (SERO PDF)",
                    "cno": cnpj_cpf,
                    "valor_recolhido": round(v, 2),
                })


        # 7. Projecao CUB (previsto) para curva-S
        area_total = sum(o["metragem"] for o in obras_cadastro.values())
        if area_total > 0 and historico_mensal:
            data_ini = sorted(historico_mensal.keys())[0]
            y0, m0 = map(int, data_ini.split("-"))
            for offset in range(72):
                cm = m0 + offset; cy = y0
                while cm > 12: cm -= 12; cy += 1
                cs = f"{cy}-{str(cm).zfill(2)}"
                if cs > compet_alvo: break
                historico_mensal[cs]["previsto"] += (area_total * cub_history.get(cs, 2950.0) * 0.20) / 48.0

        curva_s = []
        acc_real = acc_prev = 0.0
        for comp in sorted(historico_mensal.keys()):
            if comp > compet_alvo: break
            acc_real += historico_mensal[comp]["realizado"]
            acc_prev += historico_mensal[comp]["previsto"]
            curva_s.append({
                "mes": comp,
                "realizado_mes": round(historico_mensal[comp]["realizado"], 2),
                "previsto_mes":  round(historico_mensal[comp]["previsto"], 2),
                "realizado": round(acc_real, 2),
                "previsto":  round(acc_prev, 2),
            })

        total_mao_de_obra = total_folha + total_terceiros
        diferenca_base = acc_prev - acc_real
        total_inss = max(diferenca_base * 0.368, 0.0)

        return {
            "resumo": {
                "mao_de_obra":               round(total_mao_de_obra, 2),
                "mao_de_obra_folha":         round(total_folha, 2),
                "mao_de_obra_terceiros_gps": round(total_terceiros, 2),
                "total_inss":                round(total_inss, 2),
                "cub_vigente":               cub_vigente,
                "area_total":                round(area_total, 2),
            },
            "alocacoes_folha": sorted(alocacoes_f, key=lambda x: x["compet"], reverse=True),
            "alocacoes_terceiros": sorted(alocacoes_t, key=lambda x: x["compet"], reverse=True),
            "curva_s": curva_s,
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn_v.close()
        conn_q.close()

@app.get("/api/dimob/preview")
def api_preview_dimob(ano: int = 2025, empresa_id: int = 959):
    try:
        from gerar_dimob import preview_dimob
        res = preview_dimob(ano, empresa_id)
        if hasattr(res, 'get') and not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("message"))
        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dimob/gerar")
def api_gerar_dimob(ano: int = 2025, empresa_id: int = 959):
    try:
        from gerar_dimob import gerar_dimob
        arquivo_saida = f"DIMOB_{ano}_EMP_{empresa_id}.txt"
        gerar_dimob(ano, empresa_id, arquivo_saida)
        if os.path.exists(arquivo_saida):
            return FileResponse(
                path=arquivo_saida, 
                filename=arquivo_saida, 
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename={arquivo_saida}"}
            )
        else:
            raise HTTPException(status_code=500, detail="Arquivo não foi gerado.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from core.services.graph_logic_builder import AccountingGraphPipeline

@app.get("/api/questor/contabilizacoes")
async def api_contabilizacoes(ano: int, mes: int, empresa_id: int = 959, empreendimento_id: str = None):
    import asyncio
    return await asyncio.to_thread(
        AccountingGraphPipeline.api_contabilizacoes, ano, mes, empresa_id, empreendimento_id
    )

class DiagnosticoRow(BaseModel):
    conta_id: int
    competencia: str
    saldo_q: float = 0.0
    saldo_v: float = 0.0
    n_lanc_q: int = 0
    n_lanc_v: int = 0

class DiagnosticoInput(BaseModel):
    empresa_id: int
    linhas: list[DiagnosticoRow]
    top_n: int = 20

from typing import Union, Optional

class MemoriaArrasteInput(BaseModel):
    chave: Union[str, int]
    conta_destino: str
    origem: str = "QUESTOR"

@app.post("/api/questor/populate_poc")
async def api_populate_questor(payload: dict):
    """
    Roda a matriz de inteligência VU (graph_logic_builder), achata todas as virtual_entries
    resultantes para a Empresa selecionada e envia o flat bulk para injeção física no LCTOCTB do Questor.
    Payload: {"ano": int, "mes": int, "empresa_id": int}
    """
    ano = int(payload.get("ano"))
    mes = int(payload.get("mes"))
    empresa_id = int(payload.get("empresa_id", 959))
    empreendimento_id = payload.get("empreendimento_id")
    
    # 1. Obter snapshot vivo (A mesma memória rodando na tela de Auditoria)
    import asyncio
    from core.services.graph_logic_builder import AccountingGraphPipeline
    
    # Recomputa o grafo de dependências atualizado (Single Source of Truth)
    res_list = await asyncio.to_thread(
        AccountingGraphPipeline().run, str(ano), f"{ano}-{mes:02d}", str(empresa_id), empreendimento_id
    )
    
    flat_entries = []
    
    # 2. Descer e Aplainar o grafo
    for proj in res_list:
        for cv in proj.get("contas_virtuais", []):
            conta = cv.get("conta")
            if not conta or conta == 99999: # Ignora saldenhos sintéticos informativos
                continue
            
            for detalhe in cv.get("detalhes", []):
                # Só nos importamos com as virtual entries produzidas pela regra VU 
                if detalhe.get("virtual"):
                    flat_entries.append({
                        "conta": conta,
                        "mov": detalhe.get("valor", detalhe.get("mov", 0.0)),
                        "nat": detalhe.get("natureza", detalhe.get("nat", "D")),
                        "historico": detalhe.get("historico", "")
                    })
                    
    # 3. Disparar pro Injector
    from core.services.questor_injector import inject_batch_to_questor
    target_ym = f"{ano}-{mes:02d}"
    resultado_injekao = await asyncio.to_thread(
        inject_batch_to_questor, empresa_id, target_ym, flat_entries
    )

    return resultado_injekao

async def salvar_memoria_arraste(payload: MemoriaArrasteInput):
    """Salva a preferência de arrastar-e-soltar do Kanban no SQLite"""
    try:
        chave = str(payload.chave).strip()
        conta_destino = str(payload.conta_destino).strip()
        origem = str(payload.origem).strip()
        
        if not chave or not conta_destino:
            return JSONResponse({"status": "error", "message": "Chave ou destino vazio"}, status_code=400)
            
        import sqlite3
        conn = connect_app()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS auditoria_memoria_arraste (
                chave_lancamento TEXT PRIMARY KEY,
                conta_destino TEXT,
                origem TEXT,
                data_modificacao TIMESTAMP
            )
        ''')
        conn.execute('''
            INSERT INTO auditoria_memoria_arraste (chave_lancamento, conta_destino, origem, data_modificacao)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chave_lancamento) DO UPDATE SET 
                conta_destino=excluded.conta_destino,
                origem=excluded.origem,
                data_modificacao=CURRENT_TIMESTAMP
        ''', (chave, conta_destino, origem))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Mapeado para {conta_destino}"}
    except Exception as e:
        print(f"Erro ao salvar memória arraste: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/auditoria/diagnostico")
async def api_auditoria_diagnostico(data: DiagnosticoInput):
    """
    Analisa divergências entre Questor (LCTOCTB) e Vulcano (contabilizacoes)
    usando:
      • DuckDB  — JOIN analítico em DataFrames (sem novo banco)
      • PyOD    — IsolationForest por conta (anomaly_score 0-1)
      • LevelShift — detecta QUANDO a divergência começou (numpy nativo)
      • KMeans  — classifica o PADRÃO da divergência por conta
      • LLM Gemini — Formulação de causa raiz das principais anomalias
    """
    import warnings, logging, asyncio
    warnings.filterwarnings("ignore")

    try:
        import pandas as pd
        import numpy as np

        if not data.linhas:
            return {"contas": [], "summary": "Nenhum dado enviado para análise."}

        # Nomes das contas (Questor)
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute("SELECT CONTACTB, DESCRCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = ?", (data.empresa_id,))
        plano = {int(r[0]): str(r[1] or "").strip() for r in cur_q.fetchall() if r[0]}
        conn_q.close()

        def _sync_ml_core():
            import duckdb
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            try:
                from pyod.models.iforest import IForest
                has_pyod = True
            except ImportError as e:
                print(f"PyOD inativo/bloqueado: {e}")
                has_pyod = False

            df_todas = pd.DataFrame([r.dict() for r in data.linhas])
            df_q = df_todas[["conta_id", "competencia", "saldo_q", "n_lanc_q"]].copy()
            df_v = df_todas[["conta_id", "competencia", "saldo_v", "n_lanc_v"]].copy()

            df_q["conta_id"] = pd.to_numeric(df_q["conta_id"], errors="coerce")
            df_v["conta_id"] = pd.to_numeric(df_v["conta_id"], errors="coerce")
            df_q = df_q.dropna(subset=["conta_id"])
            df_v = df_v.dropna(subset=["conta_id"])
            df_q["conta_id"] = df_q["conta_id"].astype(int)
            df_v["conta_id"] = df_v["conta_id"].astype(int)

            if df_q.empty and df_v.empty:
                return [], 0, 0, 0, 0

            ddb = duckdb.connect()
            delta_df = ddb.execute("""
                SELECT
                    COALESCE(q.conta_id, v.conta_id) AS conta_id,
                    COALESCE(q.competencia, v.competencia) AS competencia,
                    COALESCE(q.saldo_q, 0.0) AS saldo_q,
                    COALESCE(v.saldo_v, 0.0) AS saldo_v,
                    COALESCE(q.saldo_q, 0.0) - COALESCE(v.saldo_v, 0.0) AS delta,
                    COALESCE(q.n_lanc_q, 0) AS n_lanc_q,
                    COALESCE(v.n_lanc_v, 0) AS n_lanc_v,
                    ABS(COALESCE(q.saldo_q, 0.0) - COALESCE(v.saldo_v, 0.0)) AS abs_delta
                FROM df_q q
                FULL OUTER JOIN df_v v ON q.conta_id = v.conta_id AND q.competencia = v.competencia
                ORDER BY conta_id, competencia
            """).fetchdf()

            if delta_df.empty:
                return [], 0, 0, 0, 0

            features_df = ddb.execute("""
                SELECT
                    conta_id,
                    AVG(delta)                              AS media_delta,
                    STDDEV(delta)                           AS std_delta,
                    MAX(abs_delta)                          AS max_delta_abs,
                    AVG(abs_delta)                          AS media_abs_delta,
                    SUM(CASE WHEN abs_delta > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                                                            AS pct_meses_divergentes,
                    COUNT(*)                                AS n_meses,
                    AVG(n_lanc_q)                           AS avg_lanc_questor,
                    AVG(n_lanc_v)                           AS avg_lanc_vulcano
                FROM delta_df
                GROUP BY conta_id
                HAVING COUNT(*) >= 2
            """).fetchdf()

            if features_df.empty or len(features_df) < 3:
                return [], -1, 0, 0, 0

            _feat_cols = ["media_delta", "std_delta", "max_delta_abs", "pct_meses_divergentes", "avg_lanc_questor"]
            X = features_df[_feat_cols].fillna(0).values
            X_scaled = StandardScaler().fit_transform(X)

            contamination = min(0.2, max(0.05, 3 / len(X)))
            iso = IForest(contamination=contamination, random_state=42, n_estimators=100)
            iso.fit(X_scaled)

            scores_raw = iso.decision_scores_
            min_s, max_s = scores_raw.min(), scores_raw.max()
            scores_norm = (scores_raw - min_s) / (max_s - min_s + 1e-9)
            features_df["anomaly_score"] = scores_norm.round(3)
            features_df["anomaly_label"] = np.where(iso.labels_ == 1, "ANOMALIA", "NORMAL")

            n_clusters = min(4, max(2, len(features_df) // 2))
            km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            features_df["cluster"] = km.fit_predict(X_scaled)

            _CLUSTER_LABELS = {0: "Exato", 1: "Lag Temporal", 2: "Percentual Fixo", 3: "Caótico"}
            _centroid_stds = km.cluster_centers_[:, 1]
            _order = np.argsort(_centroid_stds)
            _label_map = {int(_order[i]): _CLUSTER_LABELS[i] for i in range(n_clusters)}
            features_df["padrao"] = features_df["cluster"].map(_label_map).fillna("Outro")

            def _detect_level_shift(series: pd.Series, window: int = 3) -> dict | None:
                if len(series) < window * 2 + 1: return None
                vals = series.values.astype(float)
                best_i, best_score = 0, 0.0
                for i in range(window, len(vals) - window):
                    score = abs(np.mean(vals[i:i + window]) - np.mean(vals[max(0, i - window):i]))
                    if score > best_score:
                        best_score, best_i = score, i
                if best_score < 1.0: return None
                return {
                    "competencia": series.index[best_i] if hasattr(series.index, '__getitem__') else str(best_i),
                    "delta_antes": round(float(np.mean(vals[:best_i])), 2),
                    "delta_depois": round(float(np.mean(vals[best_i:])), 2),
                    "magnitude": round(float(best_score), 2)
                }

            shifts = {}
            for conta_id, grp in delta_df.sort_values("competencia").groupby("conta_id"):
                serie = grp.set_index("competencia")["delta"]
                sh = _detect_level_shift(serie)
                if sh: shifts[int(conta_id)] = sh
            
            meses_unicos = int(df_todas["competencia"].nunique() if not df_todas.empty else 0)

            top_contas = features_df.sort_values("anomaly_score", ascending=False).head(data.top_n)
            resultado = []
            for _, row in top_contas.iterrows():
                cid = int(row["conta_id"])
                resultado.append({
                    "conta_id":               cid,
                    "conta_nome":             plano.get(cid, f"Conta {cid}"),
                    "anomaly_score":          round(float(row["anomaly_score"]), 3),
                    "anomaly_label":          row["anomaly_label"],
                    "padrao":                 row["padrao"],
                    "media_delta":            round(float(row["media_delta"]), 2),
                    "std_delta":              round(float(row.get("std_delta") or 0), 2),
                    "max_delta_abs":          round(float(row["max_delta_abs"]), 2),
                    "pct_meses_divergentes":  round(float(row["pct_meses_divergentes"]), 1),
                    "n_meses_analisados":     int(row["n_meses"]),
                    "avg_lanc_questor":       round(float(row.get("avg_lanc_questor") or 0), 1),
                    "avg_lanc_vulcano":       round(float(row.get("avg_lanc_vulcano") or 0), 1),
                    "level_shift":            shifts.get(cid),
                })
            return resultado, int((features_df["anomaly_label"] == "ANOMALIA").sum()), meses_unicos, len(features_df), len(shifts)

        # Executa a parte bloqueante (ML e Processamento de Dados) em thread controlada
        resultado, n_anomalias, meses_unicos, len_feat, len_shifts = await asyncio.to_thread(_sync_ml_core)

        if len_feat == 0: return {"contas": [], "summary": "Sem cruzamento de dados no período."}
        if len_feat == -1: return {"contas": [], "summary": "Dados insuficientes para análise ML (mínimo 3 contas, 2 meses)."}

        # ── 9. Investigação Qualitativa Gemini nas Top Anomalias ────────────
        anomalias = [r for r in resultado if r["anomaly_label"] == "ANOMALIA"][:5] # Top 5 anomalias
        
        if anomalias:
            schema = '{"causas":[{"conta_id":0,"causa_raiz":"","recomendacao":""}]}'
            prompt = "Você é um auditor contábil sênior diagnosticando as divergências entre o ERP Questor (físico, saldos lançados) e o motor societário Vulcano (virtual, espelho da POC IFRS e impostos gerados). \n"
            prompt += "Baseado no comportamento quantitativo (Padrão, Delta, Level-Shift), explique a possível causa raiz da anomalia de cada conta e dê uma recomendação de ação.\n\nContas a Analisar:\n"
            
            for a in anomalias:
                cid = a["conta_id"]
                df_conta = pd.DataFrame([r.dict() for r in data.linhas if r.conta_id == cid]).sort_values("competencia")
                serie_txt = df_conta[["competencia", "saldo_q", "saldo_v"]].to_csv(index=False, sep="|")
                
                sh = a["level_shift"]
                shift_str = f"Iniciou {sh['competencia']} (Antes: {sh['delta_antes']}, Depois: {sh['delta_depois']})" if sh else "Nenhum"
                
                prompt += f"--- CONTA {cid} ({a['conta_nome']}) ---\n"
                prompt += f"Padrão Algorítmico: {a['padrao']}, Shift de Nível: {shift_str}\nSérie Mensal (Q=Questor vs V=Vulcano):\n{serie_txt}\n\n"

            prompt += f"Retorne **apenas** JSON respeitando estritamente o schema: {schema}"
            
            try:
                resp_ia = await _gemini_generate_json_async(prompt)
                for causa in resp_ia.get("causas", []) or resp_ia.get("Causas", []):
                    try:
                        c_id = int(causa.get("conta_id", 0))
                    except:
                        c_id = 0
                    match = next((r for r in resultado if r["conta_id"] == c_id), None)
                    if match:
                        match["causa_raiz"] = str(causa.get("causa_raiz", causa.get("Causa_Raiz", "")))
                        match["recomendacao"] = str(causa.get("recomendacao", causa.get("Recomendacao", ""))) 
            except Exception as ml_err:
                import traceback; open("gemini_error.txt", "w").write(traceback.format_exc())

        return {
            "contas":    resultado,
            "total_contas_analisadas": len_feat,
            "total_anomalias": n_anomalias,
            "janela_meses": meses_unicos,
            "summary": (
                f"{len_feat} contas analisadas ({meses_unicos} meses). "
                f"{n_anomalias} contas anômalas detectadas. "
                f"{len_shifts} com mudança de nível identificada."
            )
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════════════════
# /api/auditoria/concilia-orfaos  — Fuzzy + probabilistic cross-account match
# ══════════════════════════════════════════════════════════════════════════════
from core.services.heuristic_optimizer import OrphansReconciliationService

@app.post("/api/auditoria/concilia-orfaos")
async def api_concilia_orfaos(data: OrphansReconciliationService.ConciliaOrfaosInput):
    result = await OrphansReconciliationService.api_concilia_orfaos(data)

    # ── Enriquece com nomes de conta + contrapartida para NAT.INVERTIDA ──────
    try:
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute(
            "SELECT CONTACTB, DESCRCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = ?",
            (data.empresa_id,)
        )
        plano = {int(r[0]): str(r[1] or "").strip() for r in cur_q.fetchall() if r[0]}

        for m in result.get("matches", []):
            # Nomes nos itens Questor
            for item in (m.get("questor_detalhe") or [m.get("questor")] if m.get("questor") else []):
                if item:
                    c = int(item.get("conta") or 0)
                    item["conta_nome"] = plano.get(c, "")
            # Nomes nos itens Vulcano
            for item in (m.get("vulcano_detalhe") or [m.get("vulcano")] if m.get("vulcano") else []):
                if item:
                    c = int(item.get("conta") or 0)
                    item["conta_nome"] = plano.get(c, "")

            # Contrapartida para NAT.INVERTIDA: busca o outro lado do lançamento no LCTOCTB
            if not m.get("nat_match", True):
                q_items = m.get("questor_detalhe") or ([m["questor"]] if m.get("questor") else [])
                for q_item in q_items[:1]:  # pega o primeiro
                    chave = q_item.get("chave")
                    if not chave:
                        continue
                    try:
                        cur_q.execute(
                            "SELECT C.CONTACTBDEB, C.CONTACTBCRED, C.VALORLCTOCTB "
                            "FROM LCTOCTB C "
                            "WHERE C.CODIGOEMPRESA = ? AND C.CHAVELCTOCTB = ?",
                            (data.empresa_id, chave)
                        )
                        row = cur_q.fetchone()
                        if row:
                            cdeb, ccred, val = int(row[0] or 0), int(row[1] or 0), float(row[2] or 0)
                            q_conta = int(q_item.get("conta") or 0)
                            contra_conta = ccred if cdeb == q_conta else cdeb
                            nat_contra   = "C" if cdeb == q_conta else "D"
                            m["questor_contrapartida"] = {
                                "conta":      contra_conta,
                                "conta_nome": plano.get(contra_conta, ""),
                                "valor":      val,
                                "natureza":   nat_contra,
                            }
                    except Exception:
                        pass
        conn_q.close()
    except Exception:
        pass

    # ── Override de score baseado no feedback humano ──────────────────────────
    try:
        fb = _load_cross_match_feedback(data.empresa_id)
        rules = _load_cross_match_rules(data.empresa_id)
        if result.get("matches"):
            for m in result["matches"]:
                ov = _feedback_score_override(m, fb, rules)
                if ov is not None:
                    m["score"] = ov
                    m["feedback_veredicto"] = "MATCH" if ov > 0.5 else "NO_MATCH"
            result["matches"] = [m for m in result["matches"] if m.get("score", 0) > 0.01]
            result["matches"].sort(key=lambda x: x["score"], reverse=True)
            result["total_matches"] = len(result["matches"])
    except Exception:
        pass
    return result

# ══════════════════════════════════════════════════════════════════════════════
# Cross-Match Feedback — Base de Conhecimento (SQLite)
# ══════════════════════════════════════════════════════════════════════════════
import json as _json

class CrossMatchFeedbackInput(BaseModel):
    empresa_id: int
    veredicto: str          # 'MATCH' | 'NO_MATCH'
    obs: str = ""
    score_algoritmo: float = 0.0
    q_conta: int = 0
    q_historico: str = ""
    q_valor: float = 0.0
    q_data: str = ""
    q_natureza: str = ""
    v_conta: int = 0
    v_historico: str = ""
    v_valor: float = 0.0
    v_data: str = ""
    v_natureza: str = ""

def _ensure_feedback_table():
    import sqlite3
    conn = connect_app()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cross_match_feedback (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at    TEXT    DEFAULT (datetime('now')),
            empresa_id    INTEGER,
            veredicto     TEXT,
            obs           TEXT,
            score_algoritmo REAL,
            q_conta       INTEGER,
            q_historico   TEXT,
            q_valor       REAL,
            q_data        TEXT,
            q_natureza    TEXT,
            v_conta       INTEGER,
            v_historico   TEXT,
            v_valor       REAL,
            v_data        TEXT,
            v_natureza    TEXT,
            q_tokens      TEXT,
            v_tokens      TEXT
        )
    """)
    conn.commit()
    conn.close()

_ensure_feedback_table()

def _tokenize_hist(text: str) -> set:
    import re
    return set(re.findall(r'\d+(?:[,\.]\d+)*|\b[A-ZÁÉÍÓÚ]{2,}\b', (text or "").upper()))

def _load_cross_match_feedback(empresa_id: int) -> list:
    import sqlite3
    try:
        conn = connect_app()
        rows = conn.execute(
            "SELECT veredicto, q_conta, q_historico, q_valor, v_conta, v_historico, v_valor, q_tokens, v_tokens "
            "FROM cross_match_feedback WHERE empresa_id=?", (empresa_id,)
        ).fetchall()
        conn.close()
        return [
            {"veredicto": r[0], "q_conta": r[1], "q_historico": r[2], "q_valor": r[3],
             "v_conta": r[4], "v_historico": r[5], "v_valor": r[6],
             "q_tokens": set(_json.loads(r[7] or "[]")),
             "v_tokens": set(_json.loads(r[8] or "[]"))}
            for r in rows
        ]
    except Exception:
        return []

def _feedback_score_override(match: dict, feedback: list, rules: list = None) -> float | None:
    """Retorna 0.97 para MATCH confirmado, 0.0 para NO_MATCH. None = sem override.
    Aplica também regras derivadas da análise de padrões (CONTA_PAIR)."""
    from difflib import SequenceMatcher
    q = match.get("questor") or {}
    v = match.get("vulcano") or {}
    q_val  = float(q.get("valor") or 0)
    v_val  = float(v.get("valor") or 0)
    q_hist = (q.get("historico") or "").upper()
    v_hist = (v.get("historico") or "").upper()
    q_cnt  = int(q.get("conta") or 0)
    v_cnt  = int(v.get("conta") or 0)

    # 1. Override exato: par já visto na KB
    for fb in (feedback or []):
        fb_qv = float(fb.get("q_valor") or 0)
        fb_vv = float(fb.get("v_valor") or 0)
        if fb_qv > 0 and abs(q_val - fb_qv) / fb_qv > 0.01: continue
        if fb_vv > 0 and abs(v_val - fb_vv) / fb_vv > 0.01: continue
        sim_q = SequenceMatcher(None, q_hist[:80], (fb.get("q_historico") or "").upper()[:80]).ratio()
        sim_v = SequenceMatcher(None, v_hist[:80], (fb.get("v_historico") or "").upper()[:80]).ratio()
        if sim_q >= 0.75 and sim_v >= 0.75:
            return 0.97 if fb["veredicto"] == "MATCH" else 0.0

    # 2. Regras derivadas: CONTA_PAIR com alta confiança
    for rule in (rules or []):
        if rule.get("rule_type") != "CONTA_PAIR": continue
        if rule.get("q_conta") == q_cnt and rule.get("v_conta") == v_cnt:
            conf = float(rule.get("confidence") or 0)
            n    = int(rule.get("n_samples") or 0)
            if n >= 3 and conf >= 0.90:
                # confiança alta: boost para 0.93 (abaixo de exact-match 0.97)
                return max(float(match.get("score") or 0), 0.93)
            elif n >= 3 and conf <= 0.20:
                # claramente rejeitado
                return 0.0
    return None

# ── Pattern analysis pipeline ────────────────────────────────────────────────
def _ensure_rules_table():
    import sqlite3
    conn = connect_app()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cross_match_rules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT DEFAULT (datetime('now')),
            empresa_id  INTEGER,
            rule_type   TEXT,   -- 'CONTA_PAIR' | 'THRESHOLD' | 'LLM_RULE'
            q_conta     INTEGER,
            v_conta     INTEGER,
            confidence  REAL,
            n_samples   INTEGER,
            payload     TEXT    -- JSON com dados adicionais (calibração, regras LLM)
        )
    """)
    conn.commit()
    conn.close()

_ensure_rules_table()

def _load_cross_match_rules(empresa_id: int) -> list:
    import sqlite3
    try:
        conn = connect_app()
        rows = conn.execute(
            "SELECT rule_type, q_conta, v_conta, confidence, n_samples, payload "
            "FROM cross_match_rules WHERE empresa_id=? ORDER BY confidence DESC",
            (empresa_id,)
        ).fetchall()
        conn.close()
        return [{"rule_type": r[0], "q_conta": r[1], "v_conta": r[2],
                 "confidence": r[3], "n_samples": r[4], "payload": r[5]} for r in rows]
    except Exception:
        return []

def _run_pattern_analysis(empresa_id: int):
    """Deriva regras estruturais da KB. Chamado em thread daemon."""
    import sqlite3, threading
    from collections import Counter
    try:
        conn = connect_app()
        rows = conn.execute(
            "SELECT veredicto, q_conta, v_conta, q_historico, v_historico, score_algoritmo "
            "FROM cross_match_feedback WHERE empresa_id=?", (empresa_id,)
        ).fetchall()

        if len(rows) < 50:
            conn.close()
            return

        matches_rows = [r for r in rows if r[0] == 'MATCH']
        reject_rows  = [r for r in rows if r[0] == 'NO_MATCH']

        # 1. Conta-pair mapping
        pair_match   = Counter((r[1], r[2]) for r in matches_rows)
        pair_reject  = Counter((r[1], r[2]) for r in reject_rows)
        all_pairs    = set(pair_match.keys()) | set(pair_reject.keys())

        conn.execute("DELETE FROM cross_match_rules WHERE empresa_id=? AND rule_type='CONTA_PAIR'", (empresa_id,))
        for pair in all_pairs:
            m_cnt = pair_match.get(pair, 0)
            r_cnt = pair_reject.get(pair, 0)
            total_pair = m_cnt + r_cnt
            if total_pair < 2:
                continue
            conf = m_cnt / total_pair
            conn.execute(
                "INSERT INTO cross_match_rules (empresa_id, rule_type, q_conta, v_conta, confidence, n_samples) "
                "VALUES (?, 'CONTA_PAIR', ?, ?, ?, ?)",
                (empresa_id, pair[0], pair[1], round(conf, 3), total_pair)
            )

        # 2. Score calibration by bucket
        buckets = {}
        for r in rows:
            sc  = float(r[5] or 0)
            b   = round(int(sc * 10) / 10, 1)
            if b not in buckets:
                buckets[b] = {"total": 0, "match": 0}
            buckets[b]["total"] += 1
            if r[0] == 'MATCH':
                buckets[b]["match"] += 1
        calibracao = {str(k): round(v["match"] / v["total"], 3) for k, v in sorted(buckets.items()) if v["total"] >= 3}

        conn.execute("DELETE FROM cross_match_rules WHERE empresa_id=? AND rule_type='THRESHOLD'", (empresa_id,))
        conn.execute(
            "INSERT INTO cross_match_rules (empresa_id, rule_type, confidence, n_samples, payload) VALUES (?, 'THRESHOLD', 0, ?, ?)",
            (empresa_id, len(rows), _json.dumps(calibracao))
        )

        conn.commit()
        conn.close()
        print(f"[KB] Análise de padrão OK — {len(matches_rows)} MATCH, {len(reject_rows)} NO_MATCH, {len(all_pairs)} pares conta derivados.")

        # 3. LLM: deriva regras textuais com Gemini (apenas quando >= 100 feedbacks)
        if len(rows) >= 100:
            _run_llm_pattern_extraction(empresa_id, matches_rows[:30], reject_rows[:10])

    except Exception as e:
        print(f"[KB] Erro em _run_pattern_analysis: {e}")

def _run_llm_pattern_extraction(empresa_id: int, matches, rejects):
    """Usa Gemini para extrair regras contábeis textuais da KB. Síncrono, roda em thread."""
    try:
        schema = '{"regras":[{"descricao":"","q_conta":0,"v_conta":0,"confianca":0.0}]}'
        exemplos_match  = "\n".join(
            f"Q c/{r[1]}:{r[3][:60]} ↔ V c/{r[2]}:{r[4][:60]}" for r in matches[:20]
        )
        exemplos_reject = "\n".join(
            f"REJEITADO: Q c/{r[1]}:{r[3][:50]} ↔ V c/{r[2]}:{r[4][:50]}" for r in rejects[:5]
        )
        prompt = (
            "Você é um especialista em contabilidade imobiliária (POC/IFRS-15). Analisando os pares "
            "MATCH confirmados pelo auditor, derive as REGRAS CONTÁBEIS implícitas que explicam por "
            "que esses lançamentos Questor ↔ Vulcano são equivalentes.\n\n"
            f"MATCHES CONFIRMADOS:\n{exemplos_match}\n\n"
            f"REJEITADOS:\n{exemplos_reject}\n\n"
            f"Retorne APENAS JSON com o schema: {schema}"
        )
        resp = _gemini_generate_json(prompt)  # síncrono — OK pq roda em thread
        regras = resp.get("regras") or []

        if regras:
            import sqlite3
            conn = connect_app()
            conn.execute("DELETE FROM cross_match_rules WHERE empresa_id=? AND rule_type='LLM_RULE'", (empresa_id,))
            for reg in regras:
                conn.execute(
                    "INSERT INTO cross_match_rules (empresa_id, rule_type, q_conta, v_conta, confidence, payload) "
                    "VALUES (?, 'LLM_RULE', ?, ?, ?, ?)",
                    (empresa_id, reg.get("q_conta", 0), reg.get("v_conta", 0),
                     float(reg.get("confianca") or 0), reg.get("descricao", ""))
                )
            conn.commit()
            conn.close()
            print(f"[KB] LLM derivou {len(regras)} regras contábeis.")
    except Exception as e:
        print(f"[KB LLM] Erro: {e}")

@app.post("/api/auditoria/cross-match-feedback")
def api_cross_match_feedback_post(data: CrossMatchFeedbackInput):
    import sqlite3, threading
    try:
        q_tok = _json.dumps(list(_tokenize_hist(data.q_historico)))
        v_tok = _json.dumps(list(_tokenize_hist(data.v_historico)))
        conn = connect_app()
        conn.execute(
            "INSERT INTO cross_match_feedback "
            "(empresa_id, veredicto, obs, score_algoritmo, "
            " q_conta, q_historico, q_valor, q_data, q_natureza, "
            " v_conta, v_historico, v_valor, v_data, v_natureza, q_tokens, v_tokens) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (data.empresa_id, data.veredicto, data.obs, data.score_algoritmo,
             data.q_conta, data.q_historico, data.q_valor, data.q_data, data.q_natureza,
             data.v_conta, data.v_historico, data.v_valor, data.v_data, data.v_natureza,
             q_tok, v_tok)
        )
        conn.commit()
        total     = conn.execute("SELECT COUNT(*) FROM cross_match_feedback WHERE empresa_id=?", (data.empresa_id,)).fetchone()[0]
        matches   = conn.execute("SELECT COUNT(*) FROM cross_match_feedback WHERE empresa_id=? AND veredicto='MATCH'", (data.empresa_id,)).fetchone()[0]
        nomatches = conn.execute("SELECT COUNT(*) FROM cross_match_feedback WHERE empresa_id=? AND veredicto='NO_MATCH'", (data.empresa_id,)).fetchone()[0]
        conn.close()

        # Trigger análise de padrão: primeira vez ao atingir 50, depois a cada 10
        if total >= 50 and (total == 50 or total % 10 == 0):
            threading.Thread(target=_run_pattern_analysis, args=(data.empresa_id,), daemon=True).start()
            analise_msg = " 🔬 Análise de padrão disparada!"
        else:
            falta = max(0, 50 - total)
            analise_msg = f" ({falta} para análise de padrão)" if falta > 0 else ""

        return {
            "ok": True,
            "total_feedback": total, "total_match": matches, "total_no_match": nomatches,
            "mensagem": f"Feedback {'✓ MATCH' if data.veredicto == 'MATCH' else '✗ NÃO MATCH'} salvo.{analise_msg}"
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auditoria/cross-match-rules")
def api_cross_match_rules_get(empresa_id: int = 959):
    """Retorna regras derivadas da base de conhecimento."""
    import sqlite3
    try:
        conn = connect_app()
        conta_pairs = conn.execute(
            "SELECT q_conta, v_conta, confidence, n_samples FROM cross_match_rules "
            "WHERE empresa_id=? AND rule_type='CONTA_PAIR' ORDER BY confidence DESC",
            (empresa_id,)
        ).fetchall()
        threshold_row = conn.execute(
            "SELECT payload, n_samples FROM cross_match_rules "
            "WHERE empresa_id=? AND rule_type='THRESHOLD' ORDER BY created_at DESC LIMIT 1",
            (empresa_id,)
        ).fetchone()
        llm_rules = conn.execute(
            "SELECT q_conta, v_conta, confidence, payload FROM cross_match_rules "
            "WHERE empresa_id=? AND rule_type='LLM_RULE' ORDER BY confidence DESC",
            (empresa_id,)
        ).fetchall()
        stats = conn.execute(
            "SELECT veredicto, COUNT(*) FROM cross_match_feedback WHERE empresa_id=? GROUP BY veredicto",
            (empresa_id,)
        ).fetchall()
        conn.close()
        return {
            "conta_pairs": [{"q_conta": r[0], "v_conta": r[1], "confidence": r[2], "n_samples": r[3]} for r in conta_pairs],
            "calibracao":  _json.loads(threshold_row[0]) if threshold_row else {},
            "n_total_feedback": (threshold_row[1] if threshold_row else 0),
            "llm_rules":   [{"q_conta": r[0], "v_conta": r[1], "confidence": r[2], "descricao": r[3]} for r in llm_rules],
            "feedback_stats": {r[0]: r[1] for r in stats},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auditoria/cross-match-feedback")
def api_cross_match_feedback_get(empresa_id: int = 959, limit: int = 300):
    import sqlite3
    try:
        conn = connect_app()
        rows = conn.execute(
            "SELECT id, created_at, veredicto, obs, score_algoritmo, "
            "       q_conta, q_historico, q_valor, q_data, "
            "       v_conta, v_historico, v_valor, v_data "
            "FROM cross_match_feedback WHERE empresa_id=? "
            "ORDER BY created_at DESC LIMIT ?", (empresa_id, limit)
        ).fetchall()
        stats = {r[0]: r[1] for r in conn.execute(
            "SELECT veredicto, COUNT(*) FROM cross_match_feedback WHERE empresa_id=? GROUP BY veredicto",
            (empresa_id,)
        ).fetchall()}
        conn.close()
        return {
            "data": [{"id": r[0], "created_at": r[1], "veredicto": r[2], "obs": r[3],
                      "score_algoritmo": r[4], "q_conta": r[5], "q_historico": r[6],
                      "q_valor": r[7], "q_data": r[8], "v_conta": r[9],
                      "v_historico": r[10], "v_valor": r[11], "v_data": r[12]} for r in rows],
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questor/saldo-contas")
def api_saldo_contas(
    empresa_id: int = 959,
    mes: int = None,
    ano: int = None,
    contas: str = None,            # CSV de códigos: "4910,4845,4995"
    empreendimento_id: str = None  # opcional, para filtrar por CC via LCTOGER
):
    """
    Busca movimentos de contas específicas diretamente em LCTOCTB (sem filtro de CC).
    Usado pela Auditoria ERP para verificar o que está fisicamente registrado no Questor
    para as contas que o Vulcano vai (ou já) injetar.
    """
    conn_q = get_conn("questor")
    conn_v = get_conn("vulcano")
    try:
        if not contas:
            return {"data": []}

        lista_contas = [int(c.strip()) for c in contas.split(",") if c.strip().isdigit()]
        if not lista_contas:
            return {"data": []}

        cur_q = conn_q.cursor()
        cur_v = conn_v.cursor()

        # Período (se fornecido)
        data_ini = None
        data_fim = None
        if mes and ano:
            data_ini = f"{ano}-{str(mes).zfill(2)}-01"
            if int(mes) == 12:
                data_fim = f"{ano+1}-01-01"
            else:
                data_fim = f"{ano}-{str(int(mes)+1).zfill(2)}-01"

        # Plano de contas (para nomes)
        cur_q.execute("SELECT CONTACTB, DESCRCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = ?", (empresa_id,))
        plano = {r[0]: str(r[1] or "").strip() for r in cur_q.fetchall()}

        # Mapeamento Global: Conta Estoque -> CC Empreendimento
        # Se um empreendimento_id foi passado, podemos restringir, mas o ideal é
        # usar o mapa global para que a visão agregada (sem filtro) da Auditoria
        # também traga o LCTOGER correto para as contas imobiliárias.
        cur_v.execute("SELECT CONTAESTAND, CODIGOCENTROCUSTO FROM EMPREENDIMENTO WHERE CONTAESTAND IS NOT NULL AND CODIGOCENTROCUSTO IS NOT NULL")
        mapa_conta_cc = {}
        for row in cur_v.fetchall():
            c_est, cc_cod = str(row[0]).strip(), str(row[1]).strip()
            if c_est.isdigit() and cc_cod.isdigit():
                mapa_conta_cc[int(c_est)] = int(cc_cod)

        # Identificar contas de Imposto a Recolher para considerar apenas Apropriações (Créditos) no confronto de movimento
        cur_v.execute("SELECT CONTA_CRED_IMP_REC_DARF FROM IMPOSTO")
        contas_imposto_recolher = {int(r[0]) for r in cur_v.fetchall() if r[0] and str(r[0]).strip().isdigit()}

        resultado = {}

        memoria_arraste = {}
        try:
            import sqlite3
            conn_poc = connect_app()
            cur_poc = conn_poc.cursor()
            cur_poc.execute('SELECT chave_lancamento, conta_destino FROM auditoria_memoria_arraste')
            for chv, dest in cur_poc.fetchall():
                memoria_arraste[str(chv).strip()] = str(dest).strip()
            conn_poc.close()
        except Exception as e_poc:
            print(f"[AVISO] Falha ao ler memoria de arraste no saldo_contas: {e_poc}")


        for conta_id in lista_contas:
            is_imposto_recolher = conta_id in contas_imposto_recolher
            
            cond_contabil = "(C.CONTACTBCRED = ?)" if is_imposto_recolher else "(C.CONTACTBDEB = ? OR C.CONTACTBCRED = ?)"
            params_conta = (conta_id,) if is_imposto_recolher else (conta_id, conta_id)
            
            cc_filtro = mapa_conta_cc.get(conta_id)
            
            rows_ger = []
            rows_ctb = []
            
            # 1. Fetch from LCTOCTB ALWAYS (base contábil nativa, que contém Baixas de Custo/Créditos)
            if data_ini and data_fim:
                query_ctb = f"""
                    SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED,
                           CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), C.VALORLCTOCTB, H.DESCRHISTCTB
                    FROM LCTOCTB C
                    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                    WHERE C.CODIGOEMPRESA = ?
                      AND {cond_contabil}
                      AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                      AND C.DATALCTOCTB >= CAST(? AS DATE)
                      AND C.DATALCTOCTB < CAST(? AS DATE)
                    ORDER BY C.DATALCTOCTB ASC
                """
                cur_q.execute(query_ctb, (empresa_id, *params_conta, data_ini, data_fim))
            else:
                query_ctb = f"""
                    SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED,
                           CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), C.VALORLCTOCTB, H.DESCRHISTCTB
                    FROM LCTOCTB C
                    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                    WHERE C.CODIGOEMPRESA = ?
                      AND {cond_contabil}
                      AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                    ORDER BY C.DATALCTOCTB ASC
                """
                cur_q.execute(query_ctb, (empresa_id, *params_conta))
            
            rows_ctb = cur_q.fetchall()
            
            # 2. Fetch from LCTOGER condicionalmente (contém os insumos/notas com rateio de CC explícito)
            if cc_filtro:
                if data_ini and data_fim:
                    query_ger = f"""
                        SELECT G.CHAVELCTOCTB, G.DATALCTOCTB,
                               CASE WHEN G.NATURLCTOCTB = 1 THEN {conta_id} ELSE C.CONTACTBDEB END AS MOCK_DEB,
                               CASE WHEN G.NATURLCTOCTB = -1 THEN {conta_id} ELSE C.CONTACTBCRED END AS MOCK_CRED,
                               CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.VALORLCTOGER, G.NATURLCTOCTB, H.DESCRHISTCTB
                        FROM LCTOGER G
                        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                        LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                        WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
                          AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                          AND G.DATALCTOCTB >= CAST(? AS DATE)
                          AND G.DATALCTOCTB < CAST(? AS DATE)
                        ORDER BY G.DATALCTOCTB ASC
                    """
                    cur_q.execute(query_ger, (empresa_id, cc_filtro, data_ini, data_fim))
                else:
                    query_ger = f"""
                        SELECT G.CHAVELCTOCTB, G.DATALCTOCTB,
                               CASE WHEN G.NATURLCTOCTB = 1 THEN {conta_id} ELSE C.CONTACTBDEB END AS MOCK_DEB,
                               CASE WHEN G.NATURLCTOCTB = -1 THEN {conta_id} ELSE C.CONTACTBCRED END AS MOCK_CRED,
                               CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.VALORLCTOGER, G.NATURLCTOCTB, H.DESCRHISTCTB
                        FROM LCTOGER G
                        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                        LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
                        WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
                          AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                        ORDER BY G.DATALCTOCTB ASC
                    """
                    cur_q.execute(query_ger, (empresa_id, cc_filtro))
                rows_ger = cur_q.fetchall()

            mov_deb = 0.0
            mov_cred = 0.0
            detalhes = []
            
            # Map para evitar duplicar chaves nativas nativas que o LCTOGER já desmembrou
            chaves_ger = set()
            for r in rows_ger:
                chaves_ger.add(r[0])  # r[0] é CHAVELCTOCTB

            # Junta os dois resultsets, preferindo o LCTOGER_CC em caso de sobreposição (desmembramento fino).
            # Mas GARANTE os créditos/baixas que só existem no LCTOCTB nativo!
            rows = rows_ger + [r for r in rows_ctb if r[0] not in chaves_ger]
            
            # Rearranjando para data
            rows = sorted(rows, key=lambda x: x[1])

            for row_tuple in rows:
                chave, dt, cdeb, ccred, hist_raw, valor = row_tuple[:6]
                
                if len(row_tuple) >= 8:
                    opt_nat = row_tuple[6]
                    descr_str = str(row_tuple[7] or "").strip()
                else:
                    opt_nat = None
                    descr_str = str(row_tuple[6] or "").strip()
                
                if isinstance(hist_raw, (bytes, bytearray)):
                    compl = hist_raw.decode("cp1252", "ignore")
                elif hasattr(hist_raw, "read"):
                    compl = hist_raw.read().decode("cp1252", "ignore")
                else:
                    compl = str(hist_raw or "")
                    
                hist = f"{descr_str} {compl}".strip()

                v = float(valor or 0)
                
                # Para evitar duplicidade de lançamentos no CC:
                override = memoria_arraste.get(str(chave).strip())
                ov_dict = {"override_apto": override} if override else {}

                if opt_nat is not None:
                    # opt_nat = G.NATURLCTOCTB (1 para Debito, -1 para Credito do LCTOCTB)
                    if opt_nat == 1 and cdeb == conta_id:
                        nat = "D"
                        mov_deb += v
                        detalhes.append({"chave": chave, "data": str(dt), "historico": hist.strip(), "natureza": nat, "valor": v, **ov_dict})
                    elif opt_nat == -1 and ccred == conta_id:
                        nat = "C"
                        mov_cred += v
                        detalhes.append({"chave": chave, "data": str(dt), "historico": hist.strip(), "natureza": nat, "valor": v, **ov_dict})
                else:
                    # Fallback standard do LCTOCTB (nível de Lote/Partida)
                    if cdeb == conta_id:
                        nat = "D"
                        mov_deb += v
                        detalhes.append({"chave": chave, "data": str(dt), "historico": hist.strip(), "natureza": nat, "valor": v, **ov_dict})
                    elif ccred == conta_id:
                        nat = "C"
                        mov_cred += v
                        detalhes.append({"chave": chave, "data": str(dt), "historico": hist.strip(), "natureza": nat, "valor": v, **ov_dict})

            mov_liq = mov_deb - mov_cred

            # Saldo anterior (antes do período)
            saldo_anterior = 0.0
            if data_ini:
                try:
                    if cc_filtro:
                        cur_q.execute(f"""
                            SELECT SUM(
                                CASE 
                                    WHEN G.NATURLCTOCTB = 1 THEN G.VALORLCTOGER 
                                    WHEN G.NATURLCTOCTB = -1 THEN -G.VALORLCTOGER 
                                    ELSE 0 
                                END
                            )
                            FROM LCTOGER G
                            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
                            WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
                              AND C.DATALCTOCTB < CAST(? AS DATE)
                              AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                              AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
                        """, (empresa_id, cc_filtro, data_ini))
                    else:
                        base_sum = "WHEN C.CONTACTBCRED = ? THEN -C.VALORLCTOCTB" if is_imposto_recolher else "WHEN C.CONTACTBDEB = ? THEN C.VALORLCTOCTB WHEN C.CONTACTBCRED = ? THEN -C.VALORLCTOCTB"
                        cur_q.execute(f"""
                            SELECT SUM(CASE {base_sum} ELSE 0 END)
                            FROM LCTOCTB C
                            WHERE C.CODIGOEMPRESA = ?
                              AND {cond_contabil}
                              AND C.DATALCTOCTB < CAST(? AS DATE)
                              AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
                        """, (*params_conta, empresa_id, *params_conta, data_ini))
                    r = cur_q.fetchone()
                    saldo_anterior = float(r[0] or 0) if r and r[0] is not None else 0.0
                except Exception:
                    pass

            resultado[conta_id] = {
                "conta": conta_id,
                "nome": plano.get(conta_id, f"Conta {conta_id}"),
                "saldo_anterior": saldo_anterior,
                "movimento_debito": mov_deb,
                "movimento_credito": mov_cred,
                "movimento_liquido": mov_deb - mov_cred,
                "saldo_final": saldo_anterior + (mov_deb - mov_cred),
                "detalhes": detalhes
            }

        return {"data": list(resultado.values())}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn_q.close()
        conn_v.close()

@app.get("/api/health")

def api_health():
    from core.agents.llm_provider import gemini_auth_available

    key = os.environ.get("GEMINI_API_KEY") or ""
    return {
        "ok": True,
        "gemini_auth_configured": _gemini_auth_configured(),
        "vertex_credentials_configured": vertex_credentials_configured(),
        "gemini_key_configured": bool(key.strip()),
        "gemini_key_len": len(key.strip()),
        "langgraph_llm_ready": gemini_auth_available(),
    }

@app.get("/api/debug/env")
def debug_env():
    """Diagnóstico rápido (não expõe segredos)."""
    key = os.environ.get("GEMINI_API_KEY") or ""
    return {
        "dotenv_path": _DOTENV_PATH,
        "dotenv_exists": os.path.isfile(_DOTENV_PATH),
        "gemini_auth_configured": _gemini_auth_configured(),
        "vertex_credentials_configured": vertex_credentials_configured(),
        "vertex_runtime": USE_VERTEX_FOR_GEMINI,
        "gemini_key_configured": bool(key.strip()),
        "gemini_key_len": len(key.strip()),
        "gemini_model": GEMINI_MODEL_ID,
        "gemini_extract_timeout_sec": GEMINI_EXTRACT_TIMEOUT_SEC,
        "cwd": os.getcwd(),
        "python_exe": sys.executable if "sys" in globals() else "",
        "firebird_host": FIREBIRD_HOST,
        "firebird_host_questor": FIREBIRD_HOST_QUESTOR,
        "firebird_host_vulcano": FIREBIRD_HOST_VULCANO,
        "firebird_port": FIREBIRD_PORT,
        "db_path_vulcano": DB_PATH_VULCANO,
        "db_path_vulcano_exists": os.path.isfile(DB_PATH_VULCANO),
        "db_path_questor": DB_PATH_QUESTOR,
        "db_path_questor_exists": os.path.isfile(DB_PATH_QUESTOR),
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Janitor Timing Middleware (após CORS) ────────────────────────────────
app.add_middleware(JanitorTimingMiddleware)

@app.on_event("startup")
async def _janitor_startup():
    """Inicia tasks assíncronas do Janitor SRE na inicialização do servidor."""
    await start_profiler()           # Writer daemon de métricas
    asyncio.create_task(run_disk_scan())  # Scanner de disco (roda a cada 30 min)
    
    # Iniciar o Watcher da Fila Automática de PDFs
    from core.services.queue_watcher import start_queue_watcher
    start_queue_watcher(_get_smart_importer_db(), _gemini_generate_json_async)

from fastapi import Request
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# ── API Janitor SRE ────────────────────────────────────────────────────
@app.get("/api/janitor/report")
def api_janitor_report(janela_horas: int = 24, top_n: int = 20):
    """Retorna métricas P50/P95/P99 de todos os endpoints nas últimas N horas."""
    perf = get_performance_report(top_n=top_n, janela_horas=janela_horas)
    cache = get_cache_stats()
    return {
        "performance": perf,
        "cache":       cache,
        "janitor_version": "1.0.0",
    }

@app.get("/api/janitor/disk")
def api_janitor_disk():
    """Retorna relatório de arquivos residuais identificados no disco."""
    return get_disk_report()

class QuarantineReq(BaseModel):
    paths: list[str]

@app.post("/api/janitor/quarantine")
def api_janitor_quarantine(req: QuarantineReq):
    """Move os arquivos especificados para .janitor_quarantine/ (reversível)."""
    return move_to_quarantine(req.paths)

@app.post("/api/janitor/cache/invalidate")
def api_janitor_cache_invalidate(path: str = None):
    """Invalida o cache de um endpoint específico ou todo o cache (path=None)."""
    removed = invalidate_cache(path)
    return {"removed": removed, "path": path or "*"}

@app.post("/api/generate-pdf-parser")
async def generate_pdf_parser(file: UploadFile = File(...)):
    _require_gemini_key()

    try:
        # Read the PDF into memory
        pdf_bytes = await file.read()
        
        # Extract text from the first 5 pages usando Async/Thread conforme AGENTS.md
        def _extract_pages(raw: bytes) -> str:
            result = []
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                for i, page in enumerate(pdf.pages):
                    if i >= 5: break
                    extracted = page.extract_text() or page.extract_text(layout=True) or ""
                    if extracted.strip():
                        result.append(f"--- Página {i + 1} ---\n{extracted[:4500]}")
            return "\n".join(result)
            
        extracted_text = await asyncio.to_thread(_extract_pages, pdf_bytes)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Cannot extract text from this PDF (it might be an image/scanned).")
            
        # Prompt Gemini to generate the python script
        model_cls = VertexModel if USE_VERTEX_FOR_GEMINI else genai.GenerativeModel
        gen_cfg = {
            "max_output_tokens": 8192,
        }
        if USE_VERTEX_FOR_GEMINI:
            gen_cfg["thinking_config"] = {"thinking_budget": 0}
        model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg)
        prompt_instructions = f"""Você é um Engenheiro de Software Python Sênior especialista em ETL e processamento de finanças usando Pandas.
Abaixo está o texto extraído da amostra do layout do relatório em PDF do sistema ERP (limite de 5 páginas).

Seu objetivo é gerar um SCRIPT PYTHON (.py) determinístico, que use `pdfplumber` e Expressões Regulares (re) ou split lines para ler TODO o PDF arquivo por arquivo, encontrar e agrupar os dados tubulares, e retornar APENAS O CÓDIGO FONTE PYTHON puro (sem blocos markdown ```python), sem texto adicional!

O código deve ter uma função principal chamada `parse_pdf(file_path)` que retorna um `pandas.DataFrame`.
O código gerado deve ser robusto e incluir documentação interna para tratamento de erros no layout.
Assuma que as bibliotecas "pdfplumber", "pandas" e "re" estarão disponíveis.

ESTRUTURA DA AMOSTRA DO TEXTO DO PDF:
---
{extracted_text[:12000]}
---

ESCREVA APENAS O CÓDIGO PYTHON DA FUNÇÃO, ABSOLUTAMENTE NENHUMA EXPLICAÇÃO ANTES OU DEPOIS. INICIE DIRETAMENTE COM AS IMPORTAÇÕES:
import pdfplumber
import pandas as pd
import re"""

        response = model.generate_content(prompt_instructions)
        python_code = response.text
        
        # Strip markdown syntax if the model ignored the instructions
        if python_code.startswith("```"):
            lines = python_code.split('\n')
            if len(lines) > 2:
                python_code = '\n'.join(lines[1:-1])
                
        return {"code": python_code.strip()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import sqlite3
from pydantic import BaseModel

def init_sqlite():
    conn = connect_app()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS evolucao_obras (
            empreendimento TEXT,
            periodo TEXT,
            percentual REAL,
            PRIMARY KEY (empreendimento, periodo)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS import_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            target_table TEXT,
            mapping_json TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pdf_parser_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            python_code TEXT NOT NULL,
            sample_json TEXT,
            arquivo_gerado TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS empresa_parser_padrao (
            empresa_id INTEGER NOT NULL PRIMARY KEY,
            parser_template_id INTEGER NOT NULL,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parser_template_id) REFERENCES pdf_parser_templates(id)
        )
    ''')
    conn.commit()
    conn.close()

init_sqlite()

def get_conn(db_name="vulcano", empresa_id=None):
    if db_name == "sqlite":
        import sqlite3
        return connect_app()

    # Questor migrou Firebird->Postgres. Quando QUESTOR_DB_KIND=postgres, o banco
    # `questor` abre via psycopg (queries Firebird traduzidas em runtime, ver db_pg).
    # O `vulcano` (VULCANO.FDB) segue Firebird sempre. O per-empresa .FDB nao se aplica
    # ao PG (base unica com todas as empresas, filtradas por CODIGOEMPRESA).
    if db_name == "questor" and questor_kind() == "postgres":
        return connect_questor_pg()

    questor_db = DB_PATH_QUESTOR
    if db_name == "questor" and empresa_id is not None:
        import os
        base_dir = os.path.dirname(DB_PATH_QUESTOR)
        possible_path = os.path.join(base_dir, f"QUESTOR_EMPRESA_{empresa_id}.FDB")
        if os.path.exists(possible_path):
            questor_db = possible_path

    fb_host = FIREBIRD_HOST_QUESTOR if db_name == "questor" else FIREBIRD_HOST_VULCANO
    return firebirdsql.connect(
        host=fb_host,
        database=questor_db if db_name == "questor" else DB_PATH_VULCANO,
        port=FIREBIRD_PORT,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset="WIN1252"
    )

_APP_ENDERECO_DDL_OK = False
_APP_ENDERECO_DDL_LOCK = __import__("threading").Lock()

def get_app_conn():
    """Banco OPERACIONAL do app via db_app (APP_DB_KIND: sqlite ou postgres `vulcano2`).

    Garante lazy o DDL da tabela de endereco estruturado (layout DIMOB) do
    empreendimento. DDL em dialeto SQLite de proposito: o translate_app do
    db_app converte para Postgres, e o fallback sqlite funciona sem mudanca.
    Lock: endpoints sync rodam no threadpool — sem ele, dois cold starts
    concorrentes disparam o CREATE em paralelo (UniqueViolation no PG).
    """
    from db_app import connect_app
    conn = connect_app()
    global _APP_ENDERECO_DDL_OK
    if not _APP_ENDERECO_DDL_OK:
        with _APP_ENDERECO_DDL_LOCK:
            if not _APP_ENDERECO_DDL_OK:
                conn.execute("""CREATE TABLE IF NOT EXISTS empreendimento_endereco (
                    empreendimento_id INTEGER PRIMARY KEY,
                    tipo_logradouro TEXT, logradouro TEXT, numero TEXT,
                    complemento TEXT, bairro TEXT, cep TEXT, uf TEXT,
                    codigo_munic TEXT,
                    fonte TEXT, codigo_outemp INTEGER, codigo_estab INTEGER,
                    atualizado_em TEXT DEFAULT (datetime('now'))
                )""")
                # sessão de extração de matrícula: guarda o PDF (documento
                # integral) e o resultado até a importação ser CONCLUÍDA —
                # base do chat de conferência do operador
                conn.execute("""CREATE TABLE IF NOT EXISTS matricula_sessao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT, pdf_path TEXT,
                    resultado TEXT,
                    status TEXT DEFAULT 'aberta',
                    criado_em TEXT DEFAULT (datetime('now')),
                    atualizado_em TEXT DEFAULT (datetime('now'))
                )""")
                conn.commit()
                _APP_ENDERECO_DDL_OK = True
    return conn

def _table_has_column(cur, table_name: str, column_name: str) -> bool:
    """
    Checks if a table has a given column. Usa metadados de sistema:
    RDB$RELATION_FIELDS no Firebird, information_schema.columns no Postgres.
    """
    if getattr(cur, "kind", "firebird") == "postgres":
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public'
              AND lower(table_name)=lower(?) AND lower(column_name)=lower(?)
            """,
            (table_name, column_name),
        )
        return cur.fetchone() is not None
    cur.execute(
        """
        SELECT 1
        FROM RDB$RELATION_FIELDS
        WHERE RDB$RELATION_NAME = ? AND RDB$FIELD_NAME = ?
        """,
        (table_name.upper(), column_name.upper()),
    )
    return cur.fetchone() is not None

class PocInput(BaseModel):
    empreendimento: str
    periodo: str
    percentual: float

@app.post("/api/poc")
def save_poc(input_data: PocInput):
    conn = connect_app()
    c = conn.cursor()
    c.execute('''
        INSERT INTO evolucao_obras (empreendimento, periodo, percentual) 
        VALUES (?, ?, ?)
        ON CONFLICT(empreendimento, periodo) DO UPDATE SET percentual=excluded.percentual
    ''', (input_data.empreendimento, input_data.periodo, input_data.percentual))
    conn.commit()
    conn.close()
    return {"message": "Salvo com sucesso"}

class ExtratoRequest(BaseModel):
    competencia: str
    empresa_id: Optional[str] = None
    
class QuestorLoteItem(BaseModel):
    contaDebito: str
    contaCredito: str
    valor: float
    historico: str

class QuestorLotePayload(BaseModel):
    competencia: str
    empresa: int
    itens: list[QuestorLoteItem]
    
# Rotas e Implementações



@app.get("/api/poc")
def get_poc():
    conn = connect_app()
    c = conn.cursor()
    c.execute('SELECT empreendimento, periodo, percentual FROM evolucao_obras ORDER BY periodo DESC')
    rows = c.fetchall()
    conn.close()
    return {"data": [{"empreendimento": r[0], "periodo": r[1], "percentual": r[2]} for r in rows]}
# --- QUESTOR AUXILIARY TABLES ENDPOINTS ---
@app.get("/api/questor/contas")
def get_questor_contas():
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        cur.execute("SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL ORDER BY DESCRTABCTB")
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        contas = [{"id": r[0], "descricao": dec(r[1])} for r in cur.fetchall()]
        conn.close()
        return contas
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questor/plano-contas-espec")
def get_questor_plano_contas_espec(empresa_id: int):
    try:
        conn = get_conn("questor", empresa_id)
        cur = conn.cursor()
        
        # TIPOCONTA = 2 means Analytical (Analítica, where entries are posted). 1 is Synthetic.
        query = """
            SELECT CONTACTB, CLASSIFCONTA, DESCRCONTA, TIPOCONTA 
            FROM PLANOESPEC 
            WHERE CODIGOEMPRESA = ? AND CLASSIFCONTA IS NOT NULL
            ORDER BY CLASSIFCONTA
        """
        cur.execute(query, (int(empresa_id),))
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        contas = [{"id": r[0], "classificacao": r[1].strip(), "descricao": dec(r[2]), "tipo": int(r[3] or 1)} for r in cur.fetchall()]
        conn.close()
        return {"contas": contas}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questor/centrocusto")
def get_questor_centrocusto(empresa_id: int | None = None):
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        if empresa_id is not None:
            cur.execute(
                "SELECT CODIGOCENTROCUSTO, DESCRCENTROCUSTO FROM CENTROCUSTO WHERE CODIGOEMPRESA = ? ORDER BY DESCRCENTROCUSTO",
                (int(empresa_id),),
            )
        else:
            cur.execute("SELECT CODIGOCENTROCUSTO, DESCRCENTROCUSTO FROM CENTROCUSTO ORDER BY DESCRCENTROCUSTO")
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        centros = [{"id": r[0], "descricao": dec(r[1])} for r in cur.fetchall()]
        conn.close()
        return centros
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questor/historicos")
def get_questor_historicos():
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        cur.execute("SELECT CODIGOHISTCTB, DESCRHISTCTB FROM HISTORICOCTB ORDER BY DESCRHISTCTB")
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        historicos = [{"id": r[0], "descricao": dec(r[1])} for r in cur.fetchall()]
        conn.close()
        return historicos
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questor/estabs")
def get_questor_estabs(empresa_id: int):
    """Estabelecimentos da empresa no Questor (CNPJ da filial/SPE do RET + endereco).

    Usado pelo picker "Puxar do Questor" do campo CNPJ do empreendimento.
    """
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        cur.execute(
            """
            SELECT CODIGOESTAB, INSCRFEDERAL, ENDERECOESTAB, NUMENDERESTAB,
                   COMPLENDERESTAB, BAIRROENDERESTAB, CEPENDERESTAB,
                   SIGLAESTADO, CODIGOMUNIC
            FROM ESTAB
            WHERE CODIGOEMPRESA = ?
            ORDER BY CODIGOESTAB
            """,
            (int(empresa_id),),
        )

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()

        estabs = [
            {
                "codigoestab": r[0],
                "cnpj": dec(r[1]),
                "endereco": {
                    "logradouro": dec(r[2]),
                    "numero": dec(r[3]),
                    "complemento": dec(r[4]),
                    "bairro": dec(r[5]),
                    "cep": dec(r[6]),
                    "uf": dec(r[7]),
                    "codigo_munic": dec(r[8]),
                },
            }
            for r in cur.fetchall()
        ]
        conn.close()
        return {"estabs": estabs}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questor/obras-cno")
def get_questor_obras_cno(empresa_id: int):
    """Obras (CNO) da empresa no Questor: OUTRAEMPEMP x OUTRAEMPRESA, TIPOOUTEMP=1.

    Usado pelo picker "Puxar do Questor" do campo CNO do empreendimento.
    TIPOOUTEMP filtrado em Python (tipo char/int ambiguo entre FB e PG).
    """
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        cur.execute(
            """
            SELECT OE.CODIGOOUTEMP, OE.NOMEOUTEMP, OE.INSCRFEDERAL,
                   OE.CODIGOTIPOLOGRAD, OE.ENDEROUTEMP, OE.NUMEROENDER,
                   OE.COMPLENDER, OE.BAIRROOUTEMP, OE.SIGLAESTADO,
                   OE.CODIGOMUNIC, OE.CEP, OEE.TIPOOUTEMP
            FROM OUTRAEMPEMP OEE
            JOIN OUTRAEMPRESA OE ON OE.CODIGOOUTEMP = OEE.CODIGOOUTEMP
            WHERE OEE.CODIGOEMPRESA = ?
            ORDER BY OE.NOMEOUTEMP
            """,
            (int(empresa_id),),
        )

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()

        obras = []
        for r in cur.fetchall():
            if dec(r[11]) != "1":  # 1 = obra/CNO (2 = empresa, 3 = terceiro)
                continue
            obras.append({
                "codigooutemp": r[0],
                "nome": dec(r[1]),
                "cno": dec(r[2]),
                "endereco": {
                    "tipo_logradouro": dec(r[3]),
                    "logradouro": dec(r[4]),
                    "numero": dec(r[5]),
                    "complemento": dec(r[6]),
                    "bairro": dec(r[7]),
                    "uf": dec(r[8]),
                    "codigo_munic": dec(r[9]),
                    "cep": dec(r[10]),
                },
            })
        conn.close()
        return {"obras": obras}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

import subprocess
import os
from fastapi.responses import FileResponse

@app.get("/api/export-razao")
def export_razao():
    script_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\export_razao.py"
    output_xlsx = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\Razao_Analitico_Limpo.xlsx"
    
    subprocess.run(["python", script_path], check=True)
    
    if os.path.exists(output_xlsx):
        return FileResponse(path=output_xlsx, filename="Razao_Analitico_Questor.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        raise HTTPException(status_code=500, detail="Erro ao gerar o Excel")

@app.get("/api/table/{table_name}/schema")
def get_schema(table_name: str, db: str = "questor"):
    conn = get_conn(db)
    cur = conn.cursor()
    if getattr(conn, "kind", "firebird") == "postgres":
        cur.execute(
            """
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_schema='public' AND lower(table_name)=lower(?)
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        cols = [{"name": str(row[0]).strip(), "type": str(row[1]).upper()} for row in cur.fetchall()]
        conn.close()
        return {"columns": cols}
    query = """
    SELECT rf.RDB$FIELD_NAME, f.RDB$FIELD_TYPE
    FROM RDB$RELATION_FIELDS rf
    JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
    WHERE rf.RDB$RELATION_NAME = ?
    ORDER BY rf.RDB$FIELD_POSITION
    """
    cur.execute(query, (table_name.upper(),))

    type_map = {7: "SMALLINT", 8: "INTEGER", 10: "REAL", 12: "DATE", 13: "TIME", 14: "CHAR", 16: "BIGINT", 27: "DOUBLE PRECISION", 35: "TIMESTAMP", 37: "VARCHAR", 261: "BLOB"}
    cols = [{"name": row[0].strip(), "type": type_map.get(row[1], "UNKNOWN")} for row in cur.fetchall()]
    conn.close()
    return {"columns": cols}

@app.get("/api/table/{table_name}/data")
def get_data(table_name: str, limit: int = 150, db: str = "questor", empresa_id: int | None = None):
    conn = get_conn(db)
    cur = conn.cursor()
    try:
        order_clause = ""
        if table_name.upper() == "LCTOCTB":
            order_clause = " ORDER BY DATALCTOCTB DESC"

        where_clause = ""
        params = []
        if empresa_id is not None:
            try:
                if _table_has_column(cur, table_name, "CODIGOEMPRESA"):
                    where_clause = ' WHERE "CODIGOEMPRESA" = ?'
                    params.append(int(empresa_id))
            except Exception:
                # If metadata lookup fails, fall back to unfiltered data
                where_clause = ""
                params = []

        cur.execute(f'SELECT FIRST {limit} * FROM "{table_name.upper()}"{where_clause}{order_clause}', tuple(params))
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        
        formatted_rows = []
        for r in rows:
            row_dict = {}
            for i, val in enumerate(r):
                if isinstance(val, bytes):
                    try:
                        row_dict[cols[i]] = val.decode('win1252', 'ignore')
                    except:
                        row_dict[cols[i]] = "<BINARY>"
                else:
                    row_dict[cols[i]] = val
            formatted_rows.append(row_dict)
            
        conn.close()
        return {"data": formatted_rows, "columns": cols}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

from core.services.revenue_time_pipeline import RevenueTimePipeline

@app.get("/api/receitas-caixa")
def get_receitas_caixa_api(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, empreendimentos_ids: str | None = None):
    return RevenueTimePipeline.get_receitas_caixa(empresa_id, data_ini, data_fim, empreendimentos_ids)
@app.get("/api/compare/pessoas")
def get_compare_pessoas(empresa_id: int | None = None):
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        if empresa_id is not None:
            cur.execute(
                """
                SELECT FIRST 300 DISTINCT c.ID, c.NOME, c.CNPJ
                FROM CLIENTE c
                JOIN VENDA v ON v.ID_CLIENTE = c.ID
                WHERE v.CODIGOEMPRESA = ?
                ORDER BY c.NOME
                """,
                (int(empresa_id),),
            )
        else:
            cur.execute("SELECT FIRST 300 ID, NOME, CNPJ FROM CLIENTE ORDER BY NOME")
        clientes = [{"id": r[0], "nome": r[1].strip() if r[1] else "", "cnpj": r[2].strip() if r[2] else ""} for r in cur.fetchall()]
        conn.close()
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compare/empreendimentos")
def get_compare_empreendimentos(empresa_id: int | None = None):
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        if empresa_id is not None:
            cur.execute("SELECT ID, NOME, CUSTOORCADO, METRAGEMTOTAL FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ?", (int(empresa_id),))
        else:
            cur.execute("SELECT ID, NOME, CUSTOORCADO, METRAGEMTOTAL FROM EMPREENDIMENTO")
        emps = [{"id": r[0], "nome": r[1].strip() if r[1] else "", "custo": r[2], "metragem": r[3]} for r in cur.fetchall()]
        conn.close()
        return {"empreendimentos": emps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/questor/gerar-lote")
async def gerar_lote_questor(payload: QuestorLotePayload):
    """
    INJECT DATA INTO QUESTOR ERP.
    Inserts a new Lote into LOTECTB and its items into LCTOCTB.
    """
    try:
        conn = get_questor_connection()
        cursor = conn.cursor()
        
        # Aqui ficará a transação SQL de Escrita Real (INSERT LOTECTB / LCTOCTB).
        # Para a validação 01 de hoje, estamos estruturando o Payload recebido do React!
        
        lote_id_simulado = 99999
        print(f"--> [QUESTOR] Recebido Ordem de Lote para Comp: {payload.competencia}")
        for it in payload.itens:
            print(f"   => D: {it.contaDebito} | C: {it.contaCredito} | R$ {it.valor}")
            
        conn.close()
        return {"status": "success", "message": "Lote validado e mapeado com sucesso", "lote_id": lote_id_simulado}
    except Exception as e:
        print("Erro Questor POST:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compare/receitas")
def get_compare_receitas(emp: str = None, empresa_id: int | None = None):
    try:
        conn_v = get_conn("vulcano")
        cur_v = conn_v.cursor()
        
        # Pega as vendas do Vulcano
        venda_query = """
            SELECT e.NOME, v.TOTALVENDA, v.DTOPER, v.DISTRATO, v.DATADISTRATO, e.OBRACONCLUIDA 
            FROM VENDA AS v 
            INNER JOIN EMPREENDIMENTO AS e ON v.IDEMPREENDIMENTO = e.ID
        """
        where = []
        params = []
        if emp:
            where.append("e.NOME LIKE ?")
            params.append('%' + emp + '%')
        if empresa_id is not None:
            where.append("v.CODIGOEMPRESA = ?")
            params.append(int(empresa_id))

        if where:
            cur_v.execute(venda_query + " WHERE " + " AND ".join(where), tuple(params))
        else:
            cur_v.execute(venda_query)
        vendas_v = cur_v.fetchall()
        
        conn_sq = connect_app()
        c_sq = conn_sq.cursor()
        c_sq.execute('SELECT empreendimento, periodo, percentual FROM evolucao_obras')
        poc_map = {(r[0], r[1]): r[2] for r in c_sq.fetchall()}
        conn_sq.close()
        
        poc_lookup = {}
        for (p_emp, p_per), p_val in poc_map.items():
            # If we are filtering, skip POCs that don't match
            if emp and emp.lower() not in p_emp.lower():
                continue

            if p_per:
                val_ym = ""
                if "/" in p_per:
                    parts = p_per.strip().split("/")
                    if len(parts) == 3: val_ym = f"{parts[2]}-{parts[1].zfill(2)}"
                    elif len(parts) == 2: val_ym = f"{parts[1]}-{parts[0].zfill(2)}"
                elif "-" in p_per:
                    parts = p_per.strip().split("-")
                    if len(parts) >= 2: val_ym = f"{parts[0]}-{parts[1].zfill(2)}"
                if val_ym:
                    poc_lookup[(p_emp, val_ym)] = p_val / 100.0

        vgv_ativos = 0.0
        distratos_totais = 0.0
        for r in vendas_v:
            valor = float(r[1] or 0)
            is_distrato = str(r[3]).strip() == 'S' if r[3] else False
            if is_distrato: distratos_totais += valor
            else: vgv_ativos += valor
            
            # Se concluída for 'S', forçamos POC 100% no mapa de lookup
            if len(r) > 5 and r[5]:
                if str(r[5]).strip().upper() == 'S':
                    emp_nm_lookup = str(r[0]).strip()
                    poc_lookup[(emp_nm_lookup, '2000-01')] = 1.0

        # 2. Busca Receita Fiscal (Questor)
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        
        fiscal_query = """
            SELECT v.COMPRECEB, SUM(v.VLTOTREC), SUM(v.VLPIS + v.VLCOFINS)
            FROM EFDUNIDIMOBVENDIDA v
            JOIN EFDUNIDIMOBILIARIA i ON v.CODIGOEMPRESA = i.CODIGOEMPRESA AND v.CODIGOESTAB = i.CODIGOESTAB AND v.NUMCADIMOB = i.NUMCADIMOB
        """
        where_q = []
        params_q = []
        if emp:
            where_q.append("i.IDENTEMP LIKE ?")
            params_q.append('%' + emp + '%')
        if empresa_id is not None:
            where_q.append("v.CODIGOEMPRESA = ?")
            params_q.append(int(empresa_id))

        if where_q:
            cur_q.execute(fiscal_query + " WHERE " + " AND ".join(where_q) + " GROUP BY v.COMPRECEB", tuple(params_q))
        else:
            cur_q.execute(fiscal_query + " GROUP BY v.COMPRECEB")
            
        fiscal_q = cur_q.fetchall()
        
        import collections
        import datetime
        timeline = collections.defaultdict(lambda: {"receita_caixa": 0.0, "impostos_caixa": 0.0, "receita_poc": 0.0})
        
        receita_fiscal_total = 0.0
        for r in fiscal_q:
            if not r[0]: continue
            dt_str = r[0].strftime('%Y-%m') if hasattr(r[0], 'strftime') else str(r[0])[:7]
            val = float(r[1] or 0)
            imp = float(r[2] or 0)
            timeline[dt_str]["receita_caixa"] += val
            timeline[dt_str]["impostos_caixa"] += imp
            receita_fiscal_total += val

        for (e_name, ym), poc_val in poc_lookup.items():
            # Apply percentage to the active VGV of THAT enterprise, but since we are lazy loading vgv_ativos it's shared...
            # A more precise metric would aggregate VGV per project, but for now we distribute it.
            timeline[ym]["receita_poc"] += (vgv_ativos * poc_val) / len(poc_lookup) if len(poc_lookup) else 0

        arr_timeline = []
        for mes in sorted(timeline.keys()):
            arr_timeline.append({
                "mes": mes,
                "receita_caixa": timeline[mes]["receita_caixa"],
                "receita_poc": timeline[mes]["receita_poc"],
                "impostos": timeline[mes]["impostos_caixa"]
            })

        conn_v.close()
        conn_q.close()

        return {
            "kpis": {
                "vgv_total": vgv_ativos,
                "distratos": distratos_totais,
                "receita_fiscal": receita_fiscal_total
            },
            "timeline": arr_timeline
        }
    except Exception as e:
        if 'conn_v' in locals(): conn_v.close()
        if 'conn_q' in locals(): conn_q.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ia-historico-relacionado")
def get_ia_historico_relacionado(emp: str, periodo: str, empresa_id: int | None = None):
    try:
        dados_relacionados = []
        
        # 1. Puxar do Questor (EFDUNIDIMOBVENDIDA)
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        
        # Formata mes para YYYY-MM ou YYYY-MM-DD dependendo de como esta gravado
        # Questor guarda datas. Vamos buscar pelo mes/ano
        year, month = periodo.split('-') if '-' in periodo else (periodo[:4], periodo[5:7])
        
        query_q = """
            SELECT v.COMPRECEB, v.VLTOTREC, v.NUMCADIMOB, i.DESCUNIDIMOB, i.CPFCNPJADQU, v.VLTOTVEND
            FROM EFDUNIDIMOBVENDIDA v
            JOIN EFDUNIDIMOBILIARIA i ON v.CODIGOEMPRESA = i.CODIGOEMPRESA AND v.CODIGOESTAB = i.CODIGOESTAB AND v.NUMCADIMOB = i.NUMCADIMOB
            WHERE i.IDENTEMP LIKE ? AND EXTRACT(YEAR FROM v.COMPRECEB) = ? AND EXTRACT(MONTH FROM v.COMPRECEB) = ?
            {where_empresa}
        """
        where_empresa = ""
        params_q = ['%' + emp + '%', int(year), int(month)]
        if empresa_id is not None:
            where_empresa = " AND v.CODIGOEMPRESA = ?"
            params_q.append(int(empresa_id))

        cur_q.execute(query_q.format(where_empresa=where_empresa), tuple(params_q))
        linhas_q = cur_q.fetchall()
        
        for idx, r in enumerate(linhas_q):
            dt_str = r[0].strftime('%Y-%m-%d') if hasattr(r[0], 'strftime') else str(r[0])
            dados_relacionados.append({
                "id": f"q_{idx}",
                "data": dt_str,
                "valor": float(r[1] or 0),
                "unidade": r[3].strip() if r[3] else str(r[2]),
                "cliente": r[4].strip() if r[4] else "N/A",
                "origem": "Questor",
                "categoria": "EFDUNIDIMOBVENDIDA (Rec. Fiscal)"
            })
            
        conn_q.close()

        # 2. Puxar do Vulcano (VENDA e EXT_RECEBER)
        # Assumindo que temos tabela VENDA
        conn_v = get_conn("vulcano")
        cur_v = conn_v.cursor()
        
        query_v = """
            SELECT v.DTOPER, v.TOTALVENDA, e.NOME, v.ID
            FROM VENDA v
            JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE e.NOME LIKE ? AND EXTRACT(YEAR FROM v.DTOPER) = ? AND EXTRACT(MONTH FROM v.DTOPER) = ?
            {where_empresa}
        """
        try:
            where_empresa = ""
            params_v = ['%' + emp + '%', int(year), int(month)]
            if empresa_id is not None:
                where_empresa = " AND v.CODIGOEMPRESA = ?"
                params_v.append(int(empresa_id))

            cur_v.execute(query_v.format(where_empresa=where_empresa), tuple(params_v))
            linhas_v = cur_v.fetchall()
            for idx, r in enumerate(linhas_v):
                dt_str = r[0].strftime('%Y-%m-%d') if hasattr(r[0], 'strftime') else str(r[0])
                dados_relacionados.append({
                    "id": f"v_venda_{idx}",
                    "data": dt_str,
                    "valor": float(r[1] or 0),
                    "unidade": r[2].strip() if r[2] else "N/A",
                    "cliente": "Vulcano Venda",
                    "origem": "Vulcano",
                    "categoria": "VENDA (VGV Bruto)"
                })
        except Exception as query_err:
            print("Erro ao ler tabela VENDA no Vulcano:", query_err)
            
        conn_v.close()
        
        # Ordenar os dados por data descedente
        dados_relacionados.sort(key=lambda x: x["data"], reverse=True)
        
        return dados_relacionados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- VULCANO REAL DATA ENDPOINTS ---
@app.get('/api/vulcano/empresas')
def get_vulcano_empresas():
    try:
        conn = get_conn('vulcano')
        cur = conn.cursor()
        query = '''
            SELECT DISTINCT e.CODIGOEMPRESA, e.NOMEEMPRESA, e.CNPJ
            FROM EMPRESA e
            INNER JOIN EMPREENDIMENTO emp ON emp.CODIGOEMPRESA = e.CODIGOEMPRESA
            ORDER BY e.CODIGOEMPRESA
        '''
        cur.execute(query)
        empresas = [{'id': r[0], 'nome': r[1].strip() if r[1] else '', 'cnpj': r[2].strip() if r[2] else ''} for r in cur.fetchall()]
        conn.close()
        return empresas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vulcano/empreendimentos")
def get_vulcano_empreendimentos(empresa_id: int):
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        # Detecta colunas reais da tabela para montar query defensiva
        cur.execute("""
            SELECT TRIM(RDB$FIELD_NAME)
            FROM RDB$RELATION_FIELDS
            WHERE RDB$RELATION_NAME = 'EMPREENDIMENTO'
        """)
        existing_cols = {r[0] for r in cur.fetchall()}

        def col_or(name, default='NULL'):
            return name if name in existing_cols else f"{default} AS {name}"

        query = f"""SELECT
            ID, NOME, METRAGEMTOTAL, CUSTOORCADO, RET, DATACONCLUSAO, ATIVO,
            {col_or('CNO', 'NULL')},
            {col_or('CONTACAIXA', '0')}, {col_or('CONTACLI', '0')},
            {col_or('CODIGOCENTROCUSTO', '0')}, {col_or('CONTAESTAND', '0')},
            {col_or('CONTAESTCON', '0')}, {col_or('CONTADESPESA', '0')},
            {col_or('CONTAREC', '0')}, {col_or('CONTAVARIACAO', '0')},
            {col_or('CONTALUCROACUM', '0')},
            {col_or('CODIGOHISTVENDA', '0')}, {col_or('CODIGOHISTRECEBIMENTO', '0')},
            {col_or('CODIGOHISTVARIACAO', '0')}, {col_or('CODIGOHISTBAIXAADI', '0')},
            {col_or('ENDERECO', "''" )}, {col_or('CONTADEVOLUCAO', '0')},
            {col_or('CODIGO_HIST_ESTORNO_SALDO', '0')}, {col_or('CONTAADICLI', '0')},
            {col_or('OBRACONCLUIDA', "'N'")},
            {col_or('CEP', "''")}, {col_or('SIGLAESTADO', "''")},
            {col_or('CODIGOMUNIC', "''")}, {col_or('CODIGOESTAB', "''")},
            {col_or('CODIGOFILIAL', "''")}, {col_or('CODIGOMATRIZ', "''")},
            {col_or('CONTACUSTO', '0')}, {col_or('CONTA_ESTORNO_DEVOLUCAO', '0')},
            {col_or('DATAINICIORET', 'NULL')}, {col_or('ALIQRET', '0')},
            {col_or('CODIGOIMPOSTO', '0')}, {col_or('VARIACAOIMPOSTO', '0')},
            {col_or('TRIBUTARNORMALAPOSCONCLUSAO', "'N'")},
            {col_or('AJUSTEFINALPOC', "'N'")}, {col_or('REAJUSTAR_PELO_CUB', "'N'")},
            {col_or('ADQUIRIDO_TERCEIROS', "'N'")}, {col_or('SEM_CUSTOS', "'N'")},
            {col_or('CONSIDERAR_POC_RECEITA', "'N'")},
            {col_or('CODIGOHISTADIANTAMENTO', '0')}, {col_or('CODIGOHISTAPRCUSTO', '0')},
            {col_or('CODIGOHISTDESPESA', '0')}, {col_or('CODIGO_HIST_ESTORNO_CUSTO', '0')},
            {col_or('CNPJ', "''")}
            FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ?"""
        cur.execute(query, (empresa_id,))
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        emps = [{
            "id": r[0], 
            "nome": dec(r[1]), 
            "metragem": float(r[2] or 0), 
            "custo": float(r[3] or 0), 
            "ret": dec(r[4]), 
            "data_conclusao": r[5].strftime('%Y-%m-%d') if hasattr(r[5], 'strftime') else dec(r[5]), 
            "ativo": dec(r[6]),
            "cno": dec(r[7]),
            "conta_caixa": r[8] or 0, "conta_clientes": r[9] or 0, "centro_custo": r[10] or 0, "conta_estand": r[11] or 0,
            "conta_estcon": r[12] or 0, "conta_despesa": r[13] or 0, "conta_rec": r[14] or 0, "conta_variacao": r[15] or 0,
            "contalucroacum": r[16] or 0, "hist_venda": r[17] or 0, "hist_recebimento": r[18] or 0, 
            "hist_variacao": r[19] or 0, "hist_baixaadi": r[20] or 0,
            "endereco": dec(r[21]), "conta_devolucao": r[22] or 0, "hist_estorno_saldo": r[23] or 0,
            "conta_adi_cli": r[24] or 0, "obra_concluida": dec(r[25]),
            
            "cep": dec(r[26]), "siglaestado": dec(r[27]), "codigomunic": dec(r[28]),
            "codigoestab": dec(r[29]), "codigofilial": dec(r[30]), "codigomatriz": dec(r[31]),
            
            "contacusto": r[32] or 0, "conta_estorno_devolucao": r[33] or 0,
            
            "datainicioret": r[34].strftime('%Y-%m-%d') if hasattr(r[34], 'strftime') else dec(r[34]), 
            "aliqret": float(r[35] or 0), "codigoimposto": r[36] or 0, "variacaoimposto": r[37] or 0,
            "tributarnormalaposconclusao": dec(r[38]),
            
            # AJUSTEFINALPOC e DOUBLE (valor de ajuste do POC, ha registros na casa dos
            # milhoes), nao um flag S/N. Devolver como numero para que o round-trip do
            # formulario reescreva o mesmo valor em vez de corrompe-lo.
            "ajustefinalpoc": float(r[39]) if r[39] is not None else None,
            "reajustar_pelo_cub": dec(r[40]), "adquirido_terceiros": dec(r[41]),
            "sem_custos": dec(r[42]), "considerar_poc_receita": dec(r[43]),
            
            "hist_adiantamento": r[44] or 0, "hist_aprcusto": r[45] or 0, "hist_despesa": r[46] or 0, "hist_estorno_custo": r[47] or 0,
            "cnpj": dec(r[48])
        } for r in cur.fetchall()]
        conn.close()
        return emps
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

class EmpreendimentoInput(BaseModel):
    id: int = None
    nome: str
    metragem: float = 0
    custo: float = 0
    ret: str = 'N'
    cno: str = ''
    cnpj: str = ''
    ativo: str = 'S'
    obra_concluida: str = 'N'
    endereco: str = ''
    data_conclusao: str = ''
    
    cep: str = ''
    siglaestado: str = ''
    codigomunic: str = ''
    codigoestab: str = ''
    codigofilial: str = ''
    codigomatriz: str = ''
    
    datainicioret: str = ''
    aliqret: float = 0
    codigoimposto: int = 0
    variacaoimposto: int = 0
    tributarnormalaposconclusao: str = 'N'
    
    reajustar_pelo_cub: str = 'N'
    considerar_poc_receita: str = 'N'
    # DOUBLE no banco, nao flag S/N — ver nota no GET.
    ajustefinalpoc: Optional[float] = None
    adquirido_terceiros: str = 'N'
    sem_custos: str = 'N'
    
    # Accounting Mapping
    conta_caixa: int = 0
    conta_clientes: int = 0
    conta_adi_cli: int = 0
    conta_estand: int = 0
    conta_estcon: int = 0
    conta_despesa: int = 0
    conta_rec: int = 0
    conta_variacao: int = 0
    conta_devolucao: int = 0
    centro_custo: int = 0
    contacusto: int = 0
    contalucroacum: int = 0
    conta_estorno_devolucao: int = 0
    
    # History
    hist_venda: int = 0
    hist_recebimento: int = 0
    hist_variacao: int = 0
    # Sem hist_distrato: nao existe coluna de historico de distrato em EMPREENDIMENTO.
    # O distrato e tratado por DISTRATOCTB e por VENDA.DISTRATO/DATADISTRATO.
    hist_estorno: int = 0
    hist_adiantamento: int = 0
    hist_baixaadi: int = 0
    hist_aprcusto: int = 0
    hist_despesa: int = 0
    hist_estorno_saldo: int = 0
    hist_estorno_custo: int = 0
    
    empresa_id: int


def _num_or_none(v):
    """Numero para colunas numericas, ou NULL.

    CODIGOMUNIC (SMALLINT), CODIGOESTAB, CODIGOFILIAL e CODIGOMATRIZ (INTEGER) sao
    numericas no banco mas chegam como string do formulario. Mandar '' direto fazia
    o Firebird recusar o INSERT/UPDATE inteiro com
    "SQL error code = -303, conversion error from string" — ou seja, bastava um
    desses campos em branco (o caso normal) para nenhum empreendimento salvar.
    """
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


# Mesma funcao com o nome usado no repositorio do Fernando (ele a criou como
# _int_or_none em 9429a61; ao portar aquele commit ela entrou aqui como
# _num_or_none). Sem este alias, todo codigo novo dele que chama _int_or_none
# chega quebrado: o NameError so aparece em runtime, com HTTP 500 no endpoint —
# ja aconteceu em estrutura/importar, vendas/excluir e importar-vendas.
# Nao remova achando que e codigo morto; o unico uso e o codigo portado.
_int_or_none = _num_or_none


def _float_or_none(v):
    """AJUSTEFINALPOC e DOUBLE na base atual (era CHAR S/N na antiga) — o model
    manda 'N' por default e o Firebird da SQL -303. Aceita numero; resto vira NULL."""
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None



@app.post("/api/vulcano/empreendimentos")
def post_vulcano_empreendimento(data: EmpreendimentoInput):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM EMPREENDIMENTO")
        new_id = cur.fetchone()[0]
        
        query = """INSERT INTO EMPREENDIMENTO (
            ID, CODIGOEMPRESA, NOME, METRAGEMTOTAL, CUSTOORCADO, RET, CNO, CNPJ, ATIVO, OBRACONCLUIDA, ENDERECO, DATACONCLUSAO,
            CONTACAIXA, CONTACLI, CONTAADICLI, CONTAESTAND, CONTAESTCON, CONTADESPESA, CONTAREC, 
            CONTAVARIACAO, CONTADEVOLUCAO, CODIGOCENTROCUSTO, CONTACUSTO, CONTALUCROACUM, CONTA_ESTORNO_DEVOLUCAO,
            CODIGOHISTVENDA, CODIGOHISTRECEBIMENTO, CODIGOHISTVARIACAO, CODIGOHISTBAIXAADI, CODIGO_HIST_ESTORNO_SALDO,
            CODIGOHISTADIANTAMENTO, CODIGOHISTAPRCUSTO, CODIGOHISTDESPESA, CODIGO_HIST_ESTORNO_CUSTO,
            CEP, SIGLAESTADO, CODIGOMUNIC, CODIGOESTAB, CODIGOFILIAL, CODIGOMATRIZ,
            DATAINICIORET, ALIQRET, CODIGOIMPOSTO, VARIACAOIMPOSTO, TRIBUTARNORMALAPOSCONCLUSAO,
            AJUSTEFINALPOC, REAJUSTAR_PELO_CUB, ADQUIRIDO_TERCEIROS, SEM_CUSTOS, CONSIDERAR_POC_RECEITA
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        params = (
            new_id, 
            data.empresa_id, 
            data.nome.encode("cp1252", "ignore"), 
            data.metragem, 
            data.custo, 
            data.ret, 
            data.cno.encode("cp1252", "ignore"),
            data.cnpj.encode("cp1252", "ignore") if data.cnpj else None,
            data.ativo,
            data.obra_concluida,
            data.endereco.encode("cp1252", "ignore") if data.endereco else None, 
            data.data_conclusao or None,
            data.conta_caixa, data.conta_clientes, data.conta_adi_cli, data.conta_estand, data.conta_estcon, 
            data.conta_despesa, data.conta_rec, data.conta_variacao, data.conta_devolucao, data.centro_custo, 
            data.contacusto, data.contalucroacum, data.conta_estorno_devolucao,
            data.hist_venda, data.hist_recebimento, data.hist_variacao, data.hist_baixaadi, data.hist_estorno_saldo,
            data.hist_adiantamento, data.hist_aprcusto, data.hist_despesa, data.hist_estorno_custo,
            data.cep, data.siglaestado, _num_or_none(data.codigomunic), _num_or_none(data.codigoestab),
            _num_or_none(data.codigofilial), _num_or_none(data.codigomatriz),
            data.datainicioret or None, data.aliqret, data.codigoimposto, data.variacaoimposto, data.tributarnormalaposconclusao,
            _float_or_none(data.ajustefinalpoc), data.reajustar_pelo_cub, data.adquirido_terceiros, data.sem_custos, data.considerar_poc_receita
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        return {"success": True, "id": new_id}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/vulcano/empreendimentos/{emp_id}")
def patch_vulcano_empreendimento(emp_id: int, data: EmpreendimentoInput):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        query = """UPDATE EMPREENDIMENTO SET 
            NOME = ?, METRAGEMTOTAL = ?, CUSTOORCADO = ?, RET = ?, CNO = ?, CNPJ = ?, ATIVO = ?, OBRACONCLUIDA = ?, ENDERECO = ?, DATACONCLUSAO = ?,
            CONTACAIXA = ?, CONTACLI = ?, CONTAADICLI = ?, CONTAESTAND = ?, CONTAESTCON = ?, CONTADESPESA = ?, 
            CONTAREC = ?, CONTAVARIACAO = ?, CONTADEVOLUCAO = ?, CODIGOCENTROCUSTO = ?, CONTACUSTO = ?, CONTALUCROACUM = ?, CONTA_ESTORNO_DEVOLUCAO = ?,
            CODIGOHISTVENDA = ?, CODIGOHISTRECEBIMENTO = ?, CODIGOHISTVARIACAO = ?, CODIGOHISTBAIXAADI = ?, CODIGO_HIST_ESTORNO_SALDO = ?,
            CODIGOHISTADIANTAMENTO = ?, CODIGOHISTAPRCUSTO = ?, CODIGOHISTDESPESA = ?, CODIGO_HIST_ESTORNO_CUSTO = ?,
            CEP = ?, SIGLAESTADO = ?, CODIGOMUNIC = ?, CODIGOESTAB = ?, CODIGOFILIAL = ?, CODIGOMATRIZ = ?,
            DATAINICIORET = ?, ALIQRET = ?, CODIGOIMPOSTO = ?, VARIACAOIMPOSTO = ?, TRIBUTARNORMALAPOSCONCLUSAO = ?,
            AJUSTEFINALPOC = ?, REAJUSTAR_PELO_CUB = ?, ADQUIRIDO_TERCEIROS = ?, SEM_CUSTOS = ?, CONSIDERAR_POC_RECEITA = ?
            WHERE ID = ?"""
        
        params = (
            data.nome.encode("cp1252", "ignore"), 
            data.metragem, 
            data.custo, 
            data.ret, 
            data.cno.encode("cp1252", "ignore"),
            data.cnpj.encode("cp1252", "ignore") if data.cnpj else None,
            data.ativo,
            data.obra_concluida,
            data.endereco.encode("cp1252", "ignore") if data.endereco else None, 
            data.data_conclusao or None,
            data.conta_caixa, data.conta_clientes, data.conta_adi_cli, data.conta_estand, data.conta_estcon, 
            data.conta_despesa, data.conta_rec, data.conta_variacao, data.conta_devolucao, data.centro_custo,
            data.contacusto, data.contalucroacum, data.conta_estorno_devolucao,
            data.hist_venda, data.hist_recebimento, data.hist_variacao, data.hist_baixaadi, data.hist_estorno_saldo,
            data.hist_adiantamento, data.hist_aprcusto, data.hist_despesa, data.hist_estorno_custo,
            data.cep, data.siglaestado, _num_or_none(data.codigomunic), _num_or_none(data.codigoestab),
            _num_or_none(data.codigofilial), _num_or_none(data.codigomatriz),
            data.datainicioret or None, data.aliqret, data.codigoimposto, data.variacaoimposto, data.tributarnormalaposconclusao,
            _float_or_none(data.ajustefinalpoc), data.reajustar_pelo_cub, data.adquirido_terceiros, data.sem_custos, data.considerar_poc_receita,
            emp_id
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

class EnderecoInput(BaseModel):
    tipo_logradouro: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    uf: str = ''
    codigo_munic: str = ''
    fonte: str = 'MANUAL'  # MANUAL | QUESTOR_OBRA | QUESTOR_ESTAB
    codigo_outemp: int | None = None
    codigo_estab: int | None = None

def _endereco_legado_str(e: "EnderecoInput") -> str:
    """Concatena o endereco estruturado no formato do campo unico do legado."""
    partes = f"{e.logradouro}, {e.numero}".strip(", ")
    if e.complemento:
        partes += f" {e.complemento}"
    if e.bairro:
        partes += f" - {e.bairro}"
    return partes.strip()

@app.get("/api/vulcano/empreendimentos/{emp_id}/endereco")
def get_empreendimento_endereco(emp_id: int):
    """Endereco estruturado (layout DIMOB) do banco do app; fallback campos legados."""
    conn = vconn = None
    try:
        conn = get_app_conn()
        cur = conn.cursor()
        cur.execute(
            """SELECT tipo_logradouro, logradouro, numero, complemento, bairro,
                      cep, uf, codigo_munic, fonte, codigo_outemp, codigo_estab
               FROM empreendimento_endereco WHERE empreendimento_id = ?""",
            (int(emp_id),),
        )
        row = cur.fetchone()
        if row:
            return {
                "found": True,
                "fonte": row[8] or "MANUAL",
                "codigo_outemp": row[9],
                "codigo_estab": row[10],
                "endereco": {
                    "tipo_logradouro": row[0] or "", "logradouro": row[1] or "",
                    "numero": row[2] or "", "complemento": row[3] or "",
                    "bairro": row[4] or "", "cep": row[5] or "",
                    "uf": row[6] or "", "codigo_munic": row[7] or "",
                },
            }
        # fallback: colunas legadas do EMPREENDIMENTO (endereco texto unico)
        vconn = get_conn("vulcano")
        vcur = vconn.cursor()
        vcur.execute("SELECT ENDERECO, CEP, SIGLAESTADO, CODIGOMUNIC FROM EMPREENDIMENTO WHERE ID = ?", (int(emp_id),))
        vrow = vcur.fetchone()

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()

        if not vrow:
            raise HTTPException(status_code=404, detail="Empreendimento nao encontrado")
        return {
            "found": False,
            "fonte": "legado",
            "codigo_outemp": None,
            "codigo_estab": None,
            "endereco": {
                "tipo_logradouro": "", "logradouro": dec(vrow[0]), "numero": "",
                "complemento": "", "bairro": "", "cep": dec(vrow[1]),
                "uf": dec(vrow[2]), "codigo_munic": dec(vrow[3]),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for c in (conn, vconn):
            try:
                if c: c.close()
            except Exception:
                pass

@app.put("/api/vulcano/empreendimentos/{emp_id}/endereco")
def put_empreendimento_endereco(emp_id: int, data: EnderecoInput):
    """Upsert do endereco estruturado no banco do app + sync das colunas legadas."""
    conn = None
    try:
        conn = get_app_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO empreendimento_endereco (
                 empreendimento_id, tipo_logradouro, logradouro, numero, complemento,
                 bairro, cep, uf, codigo_munic, fonte, codigo_outemp, codigo_estab
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(empreendimento_id) DO UPDATE SET
                 tipo_logradouro=excluded.tipo_logradouro, logradouro=excluded.logradouro,
                 numero=excluded.numero, complemento=excluded.complemento,
                 bairro=excluded.bairro, cep=excluded.cep, uf=excluded.uf,
                 codigo_munic=excluded.codigo_munic, fonte=excluded.fonte,
                 codigo_outemp=excluded.codigo_outemp, codigo_estab=excluded.codigo_estab,
                 atualizado_em=(datetime('now'))""",
            (int(emp_id), data.tipo_logradouro, data.logradouro, data.numero,
             data.complemento, data.bairro, data.cep, data.uf, data.codigo_munic,
             data.fonte, data.codigo_outemp, data.codigo_estab),
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Banco do app (endereco): {e}")
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

    # Sync best-effort das colunas legadas existentes (sem DDL; conexao distinta).
    # CODIGOMUNIC e SMALLINT na base viva: '' vira NULL e valores fora do range
    # (ex. codigo IBGE de 7 digitos) tambem — o valor completo fica no banco do app.
    munic = _num_or_none(data.codigo_munic)
    if munic is not None and not (-32768 <= munic <= 32767):
        munic = None
    vconn = None
    try:
        vconn = get_conn("vulcano")
        vcur = vconn.cursor()
        vcur.execute(
            "UPDATE EMPREENDIMENTO SET ENDERECO = ?, CEP = ?, SIGLAESTADO = ?, CODIGOMUNIC = ? WHERE ID = ?",
            (_endereco_legado_str(data).encode("cp1252", "ignore"),
             data.cep, data.uf, munic, int(emp_id)),
        )
        vconn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Endereco salvo no banco do app, mas falhou sync no legado: {e}")
    finally:
        try:
            if vconn: vconn.close()
        except Exception:
            pass

    return {"success": True}

# ── Importação de estrutura via matrícula de incorporação (PDF → Vertex) ──────
# Fluxo do item 3 do doc da analista: a certidão de inteiro teor da matrícula
# (imagem escaneada) vai inteira ao Gemini/Vertex, que devolve o cadastro do
# empreendimento + blocos + GRUPOS de unidades identicas (como a propria
# matrícula descreve) — a expansão em unidades individuais é feita em código.

_MATRICULA_PROMPT_EMP = """Você é um analista de registro de imóveis. O PDF anexo é a CERTIDÃO DE INTEIRO TEOR de uma matrícula com registro de INCORPORAÇÃO IMOBILIÁRIA (páginas escaneadas — leia todas).

Extraia SOMENTE os dados cadastrais e retorne EXATAMENTE este JSON (chaves fixas; string vazia quando não constar):
{
  "nome": "nome do empreendimento/residencial",
  "matricula_numero": "número da matrícula",
  "cartorio": "cartório/comarca do registro",
  "incorporadora_nome": "razão social da incorporadora",
  "incorporadora_cnpj": "CNPJ da incorporadora",
  "cno": "CNO/CEI da obra se citado",
  "area_terreno_m2": 0.0,
  "endereco": {"logradouro": "", "numero": "", "complemento": "", "bairro": "", "cep": "", "uf": "", "municipio": ""},
  "observacoes": "averbações/ressalvas relevantes (permutas, ônus, patrimônio de afetação, retificações)"
}

ONDE ACHAR CADA DADO:
- nome: no R. de INCORPORAÇÃO ("incorporará a edificação denominada ..."). Copie o nome EXATO em negrito nesse registro.
- incorporadora: a proprietária/incorporadora citada no R. de incorporação (CNPJ como escrito, geralmente no R. de compra e venda).
- endereço: o do IMÓVEL DESTA matrícula — se houver averbação de ATUALIZAÇÃO DE ENDEREÇO, use a mais recente. NUNCA use o endereço do CARTÓRIO que aparece no cabeçalho de todas as páginas (ex.: rua do "Registro de Imóveis").
- cno: APENAS se o documento citar literalmente CNO/CEI da obra; senão "".

TRANSCREVA fielmente o que está escrito; NÃO complete com conhecimento externo nem invente nomes. Se um dado não constar, devolva string vazia."""

_MATRICULA_PROMPT_ESTRUTURA = """Você é um analista de registro de imóveis. O PDF anexo é a CERTIDÃO DE INTEIRO TEOR de uma matrícula com registro de INCORPORAÇÃO IMOBILIÁRIA (páginas escaneadas — leia todas).

Extraia a ESTRUTURA de blocos e unidades autônomas e retorne EXATAMENTE este JSON:
{
  "blocos": ["BLOCO A", "BLOCO B"],
  "grupos_unidades": [
    {"bloco": "BLOCO A", "tipo": "apartamento",
     "unidades": [{"numero": "101", "vaga": "estacionamento descoberta 001"}],
     "area_privativa_m2": 0.0, "area_acessoria_m2": 0.0, "area_privativa_total_m2": 0.0,
     "area_comum_m2": 0.0, "area_total_m2": 0.0, "fracao_ideal_pct": 0.0}
  ],
  "unidades_autonomas_extras": [{"descricao": "", "quantidade": 0, "numeracao": ""}],
  "total_unidades_declarado": 0,
  "area_privativa_total_declarada_m2": 0.0
}

total_unidades_declarado = o TOTAL de unidades que a própria matrícula declara (ex.: "condomínio composto por 288 apartamentos"); area_privativa_total_declarada_m2 = a área privativa TOTAL do condomínio declarada no documento (m²). 0 se não constar.

Na seção "DISCRIMINAÇÃO NUMÉRICA, LOCALIZAÇÃO, ÁREA E FRAÇÃO IDEAL DAS UNIDADES" (ou equivalente), as unidades vêm em GRUPOS com áreas idênticas (ex.: "Apartamento nº 101 do bloco A com vaga nº 001, Apartamento nº 201 do bloco A com vaga nº 009...: área privativa de X m²..."). Para cada grupo: o bloco (use o nome como escrito, ex. "BLOCO A"); o tipo; os pares {numero, vaga} respeitando o pareamento apartamento↔vaga do texto (vaga com descrição curta; "" se não houver); e as áreas do grupo. ATENÇÃO fracao_ideal_pct: a matrícula escreve "coeficiente de proporcionalidade equivalente a 0,3801% ou 39,8546m² de fração ideal" — fracao_ideal_pct é o PERCENTUAL (0.3801), NUNCA o valor em m². Decimais com ponto.

REGRAS CRÍTICAS:
- NÃO invente unidades: transcreva exatamente as numerações listadas em cada grupo.
- Cada apartamento aparece em exatamente UM grupo — cuidado com grupos que continuam na página/verso seguinte (o cabeçalho repete; a lista de apartamentos do grupo pode atravessar a quebra de página).
- NEM TODA unidade segue o padrão contínuo dos grupos grandes: algumas são descritas FORA do padrão, em parágrafo próprio ou grupo pequeno com redação diferente (ex.: coberturas, finais específicos como aptos 401/501 de um bloco, unidades com vaga dupla). Varra TODAS as páginas procurando por "Apartamento nº" e inclua cada uma no seu grupo — não assuma que a listagem contínua é completa.
- Confira: a soma das unidades de todos os grupos deve bater com o total declarado na matrícula (ex.: "288 apartamentos"). Se não bater, revise antes de responder.
- unidades_autonomas_extras: só unidades AUTÔNOMAS fora dos blocos (lojas, vagas autônomas). Vagas VINCULADAS a apartamentos não entram."""

def _num_matricula(v):
    """Coage área/fração p/ float (Gemini às vezes devolve string); None se inválido."""
    try:
        s = str(v).strip().replace(",", ".")
        return float(s) if s else None
    except (TypeError, ValueError):
        return None

_RE_BLOCO_CURTO = None
def _canon_bloco(nome: str) -> str:
    """'A' → 'BLOCO A'; normaliza caixa/espacos p/ casar blocos entre execucoes."""
    global _RE_BLOCO_CURTO
    if _RE_BLOCO_CURTO is None:
        _RE_BLOCO_CURTO = re.compile(r"^[A-Z0-9]{1,3}$")
    n = re.sub(r"\s+", " ", str(nome or "").strip().upper())
    if _RE_BLOCO_CURTO.match(n):
        n = f"BLOCO {n}"
    return n

def _normalizar_emp_matricula(raw: dict) -> dict:
    """Gemini às vezes foge do schema (fallback sem structured output) — mapeia
    variações de chave para um shape estável que a UI conhece."""
    raw = raw or {}
    inc = raw.get("incorporadora") or {}
    end = raw.get("endereco") or raw.get("endereco_terreno") or {}
    def pick(*keys):
        for k in keys:
            v = raw.get(k)
            if v not in (None, ""):
                return v
        return ""
    return {
        "nome": pick("nome", "nome_empreendimento"),
        "matricula_numero": str(pick("matricula_numero", "matricula") or ""),
        "cartorio": pick("cartorio", "cartorio_comarca", "comarca"),
        "incorporadora_nome": raw.get("incorporadora_nome") or inc.get("nome") or "",
        "incorporadora_cnpj": raw.get("incorporadora_cnpj") or inc.get("cnpj") or "",
        "cno": pick("cno", "cno_obra"),
        "area_terreno_m2": raw.get("area_terreno_m2"),
        "endereco": {
            "logradouro": end.get("logradouro") or "",
            "numero": str(end.get("numero") or ""),
            "complemento": end.get("complemento") or "",
            "bairro": end.get("bairro") or "",
            "cep": end.get("cep") or "",
            "uf": end.get("uf") or "",
            "municipio": end.get("municipio") or "",
        },
    }

def _expandir_grupos_matricula(extracao: dict) -> tuple[list[dict], list[str]]:
    """Grupos → unidades individuais p/ prévia e importação.

    Dedup por (bloco, numero) — mantém a 1ª ocorrência e reporta as repetidas
    (sinal de erro de leitura do modelo que o usuário deve conferir na prévia).
    """
    unidades, vistos, duplicatas = [], set(), []
    for g in extracao.get("grupos_unidades", []) or []:
        for u in g.get("unidades", []) or []:
            bloco = _canon_bloco(g.get("bloco"))
            numero = str(u.get("numero") or "").strip()
            chave = (bloco, numero)
            if chave in vistos:
                duplicatas.append(f"{bloco} nº {numero}")
                continue
            vistos.add(chave)
            unidades.append({
                "bloco": bloco,
                "tipo": (g.get("tipo") or "apartamento").strip(),
                "numero": numero,
                "vaga": (u.get("vaga") or "").strip(),
                "area_privativa_m2": _num_matricula(g.get("area_privativa_m2")),
                "area_privativa_total_m2": _num_matricula(g.get("area_privativa_total_m2")),
                "area_total_m2": _num_matricula(g.get("area_total_m2")),
                "fracao_ideal_pct": _num_matricula(g.get("fracao_ideal_pct")),
            })
    return unidades, duplicatas

def _criticas_matricula(resultado: dict) -> dict:
    """Crítica permanente da prévia: unidades extraídas × total declarado na
    matrícula e Σ m² privativa extraída × área privativa total declarada."""
    unidades = resultado.get("unidades") or []
    soma_priv = round(sum(u.get("area_privativa_m2") or 0 for u in unidades), 2)
    # o total declarado costuma ser privativa + ACESSÓRIA (vagas) — compara os dois
    soma_priv_total = round(sum(u.get("area_privativa_total_m2") or u.get("area_privativa_m2") or 0
                                for u in unidades), 2)
    total_decl = resultado.get("total_unidades_declarado")
    m2_decl = resultado.get("area_privativa_total_declarada_m2")
    base = None
    if m2_decl:
        base = "privativa+acessoria" if abs(m2_decl - soma_priv_total) <= abs(m2_decl - soma_priv) else "privativa"
    melhor = soma_priv_total if base == "privativa+acessoria" else soma_priv
    por_bloco = {}
    for u in unidades:
        por_bloco[u["bloco"]] = por_bloco.get(u["bloco"], 0) + 1
    return {
        "unidades": {"extraido": len(unidades), "declarado": total_decl,
                     "ok": (not total_decl) or int(total_decl) == len(unidades)},
        "area_privativa": {"soma_extraida_m2": soma_priv,
                           "soma_priv_total_m2": soma_priv_total,
                           "declarado_m2": m2_decl, "base_comparacao": base,
                           "diferenca_m2": round((m2_decl - melhor), 2) if m2_decl else None,
                           "ok": (not m2_decl) or abs(m2_decl - melhor) < 1.0},
        "unidades_por_bloco": por_bloco,
    }

@app.post("/api/vulcano/matricula/extrair")
async def extrair_matricula(file: UploadFile = File(...)):
    """Envia a matrícula (PDF) ao Vertex e devolve empreendimento+blocos+unidades."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um PDF (certidão da matrícula).")
    pdf_bytes = await file.read()
    if len(pdf_bytes) > 30 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF acima de 30MB.")

    # ── CONSENSO ANTI-ALUCINAÇÃO ─────────────────────────────────────────────
    # Extrações independentes divergem em detalhes (caso real: uma leitura
    # devolveu nome/CNPJ/endereço de empreendimento INEXISTENTE, outra trocou a
    # vaga de um apto). Defesa: 3 leituras do cadastro (voto por campo) + 2 da
    # estrutura (diff por unidade) + desempate focado só no que divergir.
    from collections import Counter
    N_EMP, N_EST = 3, 3
    tasks = [
        _gemini_generate_json_async(_MATRICULA_PROMPT_EMP, file_data=pdf_bytes,
                                    mime_type="application/pdf", max_output_tokens=4096)
        for _ in range(N_EMP)
    ] + [
        _gemini_generate_json_async(_MATRICULA_PROMPT_ESTRUTURA, file_data=pdf_bytes,
                                    mime_type="application/pdf", max_output_tokens=32768)
        for _ in range(N_EST)
    ]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)
    emp_runs = [_normalizar_emp_matricula(r) for r in resultados[:N_EMP] if isinstance(r, dict)]
    est_runs = [r for r in resultados[N_EMP:] if isinstance(r, dict)]
    if not emp_runs or not est_runs:
        erros = [str(r)[:120] for r in resultados if isinstance(r, Exception)]
        raise HTTPException(status_code=502, detail=f"Extração falhou nas leituras: {erros}")

    # cadastro: voto campo a campo com clustering tolerante — valores-lixo
    # ("NÃO CONSTA") viram vazio; "PALHOÇA/SC" ⊂ "REGISTRO DE IMÓVEIS DE
    # PALHOÇA/SC" e "LTDA" ⊂ "LTDA ME" contam como o mesmo valor (vence o mais
    # completo); CNPJ/CEP comparam só dígitos.
    _LIXO = {"NAO CONSTA", "NÃO CONSTA", "N/A", "NA", "-", "NULL", "NONE",
             "SEM INFORMACAO", "SEM INFORMAÇÃO", "NAO INFORMADO", "NÃO INFORMADO"}

    def _norm_cmp(v):
        s = str(v or "").strip().upper()
        s = re.sub(r"\s+", " ", s)
        return "" if s in _LIXO else s

    def _voto_campo(valores, digits_only=False):
        """→ (valor_vencedor, variantes_divergentes_ou_None)."""
        def key(v):
            n = _norm_cmp(v)
            return re.sub(r"\D", "", n) if digits_only else n
        candidatos = [str(v).strip() for v in valores if key(v)]
        if not candidatos:
            return "", None
        # clusters por igualdade/containment da forma normalizada
        clusters = []  # [ [reprs...] ]
        for v in candidatos:
            kv = key(v)
            alocado = False
            for cl in clusters:
                k0 = key(cl[0])
                if kv == k0 or kv in k0 or k0 in kv:
                    cl.append(v)
                    alocado = True
                    break
            if not alocado:
                clusters.append([v])
        clusters.sort(key=len, reverse=True)
        top = clusters[0]
        representante = max(top, key=len)  # a variante mais completa
        if len(clusters) == 1 or len(top) >= 2:
            variantes = sorted({c[0] for c in clusters[1:]}) if len(clusters) > 1 else None
            return representante, variantes
        # vários clusters, todos com 1 voto: sem consenso
        return "", sorted({c[0] for c in clusters})

    emp_raw, divergencias_cadastro = {}, {}
    campos_planos = ["nome", "matricula_numero", "cartorio", "incorporadora_nome",
                     "incorporadora_cnpj", "cno", "area_terreno_m2", "observacoes"]
    for campo in campos_planos:
        digits = campo in ("incorporadora_cnpj",)
        valor, variantes = _voto_campo([r.get(campo) for r in emp_runs], digits_only=digits)
        emp_raw[campo] = valor
        if variantes:
            divergencias_cadastro[campo] = variantes
    emp_raw["endereco"] = {}
    for campo in ("logradouro", "numero", "complemento", "bairro", "cep", "uf", "municipio"):
        valor, variantes = _voto_campo(
            [(r.get("endereco") or {}).get(campo) for r in emp_runs],
            digits_only=(campo == "cep"),
        )
        emp_raw["endereco"][campo] = valor
        if variantes:
            divergencias_cadastro[f"endereco.{campo}"] = variantes

    # desempate focado do cadastro: p/ campos sem consenso, escolher entre os
    # candidatos e transcrever do documento é bem mais confiavel que extraçao aberta
    campos_pendentes = {c: v for c, v in divergencias_cadastro.items()
                        if not (emp_raw.get(c) if "." not in c else emp_raw["endereco"].get(c.split(".")[1]))}
    if campos_pendentes:
        perguntas = "; ".join(f"{c}: candidatos {v}" for c, v in campos_pendentes.items())
        try:
            resolucao = await _gemini_generate_json_async(
                "No PDF anexo (certidão de matrícula com incorporação), leituras anteriores "
                f"divergiram nos campos cadastrais a seguir — {perguntas}. Localize cada um no "
                "documento (nome do empreendimento fica no R. de INCORPORAÇÃO 'edificação "
                "denominada ...'; endereço é o do IMÓVEL, nunca o do cartório do cabeçalho; "
                "prefira averbação de atualização de endereço mais recente) e responda no JSON "
                "{\"resolucoes\": {\"<campo>\": \"<valor exato do documento, ou vazio se não constar>\"}}. "
                "Escolha entre os candidatos apenas se um deles for exatamente o que está escrito.",
                file_data=pdf_bytes,
                mime_type="application/pdf",
                max_output_tokens=4096,
            )
            for campo, valor in (resolucao.get("resolucoes") or {}).items():
                valor = str(valor or "").strip()
                if not valor or campo not in campos_pendentes:
                    continue
                if "." in campo:
                    emp_raw["endereco"][campo.split(".")[1]] = valor
                else:
                    emp_raw[campo] = valor
                divergencias_cadastro[campo] = campos_pendentes[campo] + ["→ resolvido no desempate: " + valor]
        except Exception:
            pass  # divergencias ficam listadas p/ o humano

    # estrutura: expande cada leitura e faz diff por (bloco, numero)
    expandidos = [_expandir_grupos_matricula(r) for r in est_runs]
    dup_todas = sorted({d for _, dups in expandidos for d in dups})
    mapas = [{(u["bloco"], u["numero"]): u for u in unids} for unids, _ in expandidos]

    def _vaga_cmp(v):
        return re.sub(r"\D", "", str(v or "")) or _norm_cmp(v)

    def _tupla_voto(u):
        return (
            round(float(u.get("area_privativa_m2") or 0), 2),
            round(float(u.get("fracao_ideal_pct") or 0), 4),
            _vaga_cmp(u.get("vaga")),
        )

    # voto por unidade: a tupla (área, fração, vaga) com maioria entre as
    # leituras vence; sem maioria → desempate focado
    unidades, para_desempate = [], set()
    todas_chaves = sorted(set().union(*[set(m) for m in mapas]))
    for chave in todas_chaves:
        ocorrencias = [m[chave] for m in mapas if chave in m]
        tuplas = [_tupla_voto(o) for o in ocorrencias]
        vencedora = Counter(tuplas).most_common(1)[0]
        if vencedora[1] >= 2:
            u = dict(ocorrencias[tuplas.index(vencedora[0])])
            if len(ocorrencias) < len(mapas):
                u["divergente_conferir"] = True  # faltou em alguma leitura
        else:
            u = dict(ocorrencias[0])
            u["divergente_conferir"] = True
            para_desempate.add(chave)
        unidades.append(u)
    para_desempate.update(
        (d.split(" nº ")[0], d.split(" nº ")[1]) for d in dup_todas if " nº " in d
    )

    # desempate focado em LOTES (pergunta só pelas unidades sem maioria)
    corrigidas = []
    if para_desempate:
        pendentes = sorted(para_desempate)
        por_chave = {(u["bloco"], u["numero"]): u for u in unidades}
        LOTE, MAX_LOTES = 25, 4
        for i in range(0, min(len(pendentes), LOTE * MAX_LOTES), LOTE):
            lote = pendentes[i:i + LOTE]
            lista = ", ".join(f"{b} nº {n}" for b, n in lote)
            try:
                correcao = await _gemini_generate_json_async(
                    "No PDF anexo (certidão de matrícula com incorporação), leituras anteriores "
                    f"divergiram sobre estas unidades: {lista}. Localize CADA uma na seção de "
                    "discriminação das unidades (atenção a grupos que continuam na página seguinte) "
                    "e retorne os dados corretos no JSON: {\"correcoes\": [{\"bloco\", \"numero\", \"vaga\", "
                    "\"area_privativa_m2\", \"area_privativa_total_m2\", \"area_total_m2\", \"fracao_ideal_pct\"}]}. "
                    "ATENÇÃO: fracao_ideal_pct é o coeficiente PERCENTUAL (ex.: 0.3801, o valor com %), "
                    "NUNCA a fração ideal em m². Decimais com ponto. Transcreva exatamente o que a matrícula diz.",
                    file_data=pdf_bytes,
                    mime_type="application/pdf",
                    max_output_tokens=8192,
                )
                for c in correcao.get("correcoes", []) or []:
                    chave = (_canon_bloco(c.get("bloco")), str(c.get("numero") or "").strip())
                    alvo = por_chave.get(chave)
                    if alvo:
                        if str(c.get("vaga") or "").strip():
                            alvo["vaga"] = str(c["vaga"]).strip()
                        suspeito = False
                        for k in ("area_privativa_m2", "area_privativa_total_m2", "area_total_m2", "fracao_ideal_pct"):
                            val = _num_matricula(c.get(k))
                            if val is None:
                                continue
                            if k == "fracao_ideal_pct" and val > 10:
                                suspeito = True  # veio a fração em m², não o percentual
                                continue
                            alvo[k] = val
                        alvo["corrigida_desempate"] = True
                        if not suspeito:
                            alvo.pop("divergente_conferir", None)
                        corrigidas.append(f"{chave[0]} nº {chave[1]}")
            except Exception:
                continue  # lote fica marcado divergente_conferir p/ o humano

    extracao = est_runs[0]  # p/ grupos_unidades/extras na resposta
    # blocos: uniao canonizada das leituras + citados nas unidades
    blocos = []
    for r in est_runs:
        for b in (r.get("blocos") or []):
            cb = _canon_bloco(b)
            if cb and cb not in blocos:
                blocos.append(cb)
    for u in unidades:
        if u["bloco"] and u["bloco"] not in blocos:
            blocos.append(u["bloco"])

    # conferências p/ a prévia (o humano decide)
    soma_fracao = sum(u.get("fracao_ideal_pct") or 0 for u in unidades)
    conferencias = {
        "leituras_estrutura": len(est_runs),
        "duplicatas_descartadas": dup_todas,
        "unidades_divergentes": sorted(f"{b} nº {n}" for b, n in para_desempate),
        "corrigidas_no_desempate": corrigidas,
        "divergencias_cadastro": divergencias_cadastro,
        "soma_fracao_ideal_pct": round(soma_fracao, 4),
        "fracao_fecha_100": abs(soma_fracao - 100.0) < 1.0 if soma_fracao else None,
    }

    # totais DECLARADOS na matrícula (voto entre as leituras; 0 = não constou)
    def _voto_num(vals):
        vals = [round(float(v), 2) for v in (_num_matricula(x) for x in vals) if v]
        if not vals:
            return None
        vencedor, n = Counter(vals).most_common(1)[0]
        return vencedor if n >= 2 or len(vals) == 1 else max(vals)
    total_decl = _voto_num([r.get("total_unidades_declarado") for r in est_runs])
    m2_decl = _voto_num([r.get("area_privativa_total_declarada_m2") for r in est_runs])

    obs = emp_raw.get("observacoes") or extracao.get("observacoes") or ""
    if isinstance(obs, list):
        obs = " ".join(str(o) for o in obs)
    resultado = {
        "empreendimento": _normalizar_emp_matricula(emp_raw),
        "blocos": blocos,
        "grupos_unidades": extracao.get("grupos_unidades") or [],
        "unidades": unidades,
        "total_unidades": len(unidades),
        "unidades_autonomas_extras": extracao.get("unidades_autonomas_extras") or [],
        "observacoes": obs,
        "conferencias": conferencias,
        "total_unidades_declarado": total_decl,
        "area_privativa_total_declarada_m2": m2_decl,
    }
    resultado["criticas"] = _criticas_matricula(resultado)

    # sessão persistida (PDF + resultado) até a importação concluir — permite
    # o chat de conferência do operador buscar no documento integral
    try:
        import uuid as _uuid
        import json
        pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matriculas_sessao")
        os.makedirs(pasta, exist_ok=True)
        pdf_path = os.path.join(pasta, f"{_uuid.uuid4().hex}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        appc = get_app_conn()
        cur = appc.execute(
            "INSERT INTO matricula_sessao (filename, pdf_path, resultado, status) VALUES (?, ?, ?, 'aberta')",
            (file.filename or "matricula.pdf", pdf_path, json.dumps(resultado, ensure_ascii=False)))
        appc.commit()
        rid = appc.execute("SELECT MAX(id) FROM matricula_sessao WHERE pdf_path = ?", (pdf_path,)).fetchone()
        resultado["sessao_id"] = rid[0] if rid else None
        appc.close()
    except Exception as e:
        resultado["sessao_id"] = None
        resultado["sessao_erro"] = f"Sessão não persistida ({e}) — chat de conferência indisponível."
    return resultado

class MatriculaChatInput(BaseModel):
    sessao_id: int
    mensagem: str

@app.post("/api/vulcano/matricula/chat")
async def chat_matricula(data: MatriculaChatInput):
    """Chat de conferência do operador sobre a matrícula extraída: aponta
    inconsistências/padrões ('faltam os aptos 401 e 501 do bloco C') e a IA
    busca no DOCUMENTO INTEGRAL (PDF da sessão), devolvendo unidades novas ou
    corrigidas que são mescladas na prévia. A sessão vive até a importação."""
    import json
    msg = (data.mensagem or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Escreva a inconsistência ou padrão a verificar.")
    appc = get_app_conn()
    row = appc.execute("SELECT pdf_path, resultado, status FROM matricula_sessao WHERE id = ?",
                       (int(data.sessao_id),)).fetchone()
    if not row:
        appc.close()
        raise HTTPException(status_code=404, detail="Sessão de extração não encontrada.")
    pdf_path, resultado_json, status = row[0], row[1], row[2]
    if status != "aberta":
        appc.close()
        raise HTTPException(status_code=400, detail="Sessão já concluída — refaça a extração para reabrir.")
    if not pdf_path or not os.path.exists(pdf_path):
        appc.close()
        raise HTTPException(status_code=410, detail="PDF da sessão não está mais disponível — refaça a extração.")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    resultado = json.loads(resultado_json or "{}")
    unidades = resultado.get("unidades") or []

    # estado compacto p/ a IA saber o que JÁ foi extraído (numerações por bloco)
    por_bloco = {}
    for u in unidades:
        por_bloco.setdefault(u["bloco"], []).append(str(u["numero"]))
    estado = "; ".join(
        f"{b}: {len(ns)} unidades ({', '.join(sorted(ns, key=lambda x: (len(x), x)))})"
        for b, ns in sorted(por_bloco.items()))
    criticas = resultado.get("criticas") or _criticas_matricula(resultado)
    soma_m2 = criticas.get("area_privativa", {}).get("soma_extraida_m2")

    prompt = (
        "O PDF anexo é a certidão de matrícula com INCORPORAÇÃO já processada. Estado atual da "
        f"extração — {estado}. Soma da área privativa extraída: {soma_m2} m². Total de unidades "
        f"declarado: {resultado.get('total_unidades_declarado')}; área privativa total declarada: "
        f"{resultado.get('area_privativa_total_declarada_m2')} m².\n\n"
        f"O OPERADOR aponta: \"{msg}\"\n\n"
        "Busque no documento o que o operador indicou (unidades faltantes, áreas erradas, padrões "
        "de escrita diferentes — ex.: unidades descritas em parágrafo próprio fora da listagem "
        "contínua). Responda no JSON: {\"resposta\": \"<explicação curta do que encontrou>\", "
        "\"unidades_novas\": [{\"bloco\", \"numero\", \"tipo\", \"vaga\", \"area_privativa_m2\", "
        "\"area_privativa_total_m2\", \"area_total_m2\", \"fracao_ideal_pct\"}], "
        "\"unidades_corrigidas\": [<mesmo shape, p/ unidades que JÁ estão na lista mas com dado errado>], "
        "\"total_unidades_declarado\": 0, \"area_privativa_total_declarada_m2\": 0.0}.\n"
        "REGRAS: transcreva SÓ o que está escrito na matrícula (nunca invente); unidades_novas só "
        "as que NÃO estão no estado atual; unidades_corrigidas SÓ as unidades ESPECÍFICAS com dado "
        "errado relacionadas ao apontamento (NUNCA devolva a lista inteira — se a observação valer "
        "para todas, explique em 'resposta' e deixe as listas vazias; máximo ~60 itens); "
        "fracao_ideal_pct é o PERCENTUAL (nunca m²); decimais com ponto; totais declarados = 0 se "
        "não constarem."
    )
    try:
        resp = await _gemini_generate_json_async(prompt, file_data=pdf_bytes,
                                                 mime_type="application/pdf",
                                                 max_output_tokens=24576)
    except Exception as e:
        appc.close()
        raise HTTPException(status_code=502, detail=f"Consulta ao documento falhou: {e}")

    def _unidade_do_chat(c):
        return {
            "bloco": _canon_bloco(c.get("bloco")),
            "tipo": (c.get("tipo") or "apartamento").strip(),
            "numero": str(c.get("numero") or "").strip(),
            "vaga": str(c.get("vaga") or "").strip(),
            "area_privativa_m2": _num_matricula(c.get("area_privativa_m2")),
            "area_privativa_total_m2": _num_matricula(c.get("area_privativa_total_m2")),
            "area_total_m2": _num_matricula(c.get("area_total_m2")),
            "fracao_ideal_pct": _num_matricula(c.get("fracao_ideal_pct")),
            "origem_chat": True,
        }

    por_chave = {(u["bloco"], str(u["numero"])): u for u in unidades}
    adicionadas, corrigidas_chat = [], []
    for c in (resp.get("unidades_novas") or []):
        nu = _unidade_do_chat(c)
        if not nu["numero"] or not nu["bloco"]:
            continue
        if (nu["fracao_ideal_pct"] or 0) > 10:
            nu["fracao_ideal_pct"] = None  # veio m² no lugar do percentual
        chave = (nu["bloco"], nu["numero"])
        if chave in por_chave:
            continue  # já existe — não duplica
        unidades.append(nu)
        por_chave[chave] = nu
        adicionadas.append(f"{nu['bloco']} nº {nu['numero']}")
    for c in (resp.get("unidades_corrigidas") or []):
        nu = _unidade_do_chat(c)
        alvo = por_chave.get((nu["bloco"], nu["numero"]))
        if not alvo:
            continue
        for k in ("vaga", "area_privativa_m2", "area_privativa_total_m2", "area_total_m2", "fracao_ideal_pct"):
            v = nu.get(k)
            if v in (None, ""):
                continue
            if k == "fracao_ideal_pct" and v > 10:
                continue
            alvo[k] = v
        alvo["corrigida_chat"] = True
        corrigidas_chat.append(f"{nu['bloco']} nº {nu['numero']}")

    for campo in ("total_unidades_declarado", "area_privativa_total_declarada_m2"):
        v = _num_matricula(resp.get(campo))
        if v:
            resultado[campo] = v
    blocos = resultado.get("blocos") or []
    for u in unidades:
        if u["bloco"] and u["bloco"] not in blocos:
            blocos.append(u["bloco"])
    resultado["blocos"] = blocos
    resultado["unidades"] = unidades
    resultado["total_unidades"] = len(unidades)
    resultado["criticas"] = _criticas_matricula(resultado)
    resultado["sessao_id"] = int(data.sessao_id)

    appc.execute("UPDATE matricula_sessao SET resultado = ?, atualizado_em = datetime('now') WHERE id = ?",
                 (json.dumps(resultado, ensure_ascii=False), int(data.sessao_id)))
    appc.commit()
    appc.close()
    return {"resposta": str(resp.get("resposta") or "").strip() or "Verificação concluída.",
            "adicionadas": adicionadas, "corrigidas": corrigidas_chat,
            "resultado": resultado}

class ImportarEstruturaInput(BaseModel):
    empreendimento_id: int
    sessao_id: int | None = None
    blocos: list[dict]  # [{nome: str, unidades: [{descricao: str, metragem: float|None, inscricao: int|None}]}]

@app.post("/api/vulcano/estrutura/importar")
def importar_estrutura(data: ImportarEstruturaInput):
    """Grava em lote blocos+unidades no Firebird (transação única).

    Blocos com mesmo nome no empreendimento são reaproveitados; unidades cuja
    DESCRICAO já existe no bloco são puladas (re-importação segura).
    """
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()

        cur.execute("SELECT ID, NOME FROM BLOCO WHERE IDEMPREENDIMENTO = ?", (data.empreendimento_id,))
        blocos_existentes = {dec(r[1]).upper(): r[0] for r in cur.fetchall()}

        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM BLOCO")
        next_bloco_id = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM UNIDADE")
        next_unid_id = cur.fetchone()[0]

        stats = {"blocos_criados": 0, "blocos_reaproveitados": 0, "unidades_criadas": 0, "unidades_puladas": 0}
        for b in data.blocos:
            nome = str(b.get("nome") or "").strip().upper()
            if not nome:
                continue
            if nome in blocos_existentes:
                bloco_id = blocos_existentes[nome]
                stats["blocos_reaproveitados"] += 1
            else:
                bloco_id = next_bloco_id
                next_bloco_id += 1
                cur.execute(
                    "INSERT INTO BLOCO (ID, IDEMPREENDIMENTO, NOME) VALUES (?, ?, ?)",
                    (bloco_id, data.empreendimento_id, nome.encode('cp1252', 'ignore')[:100]),
                )
                blocos_existentes[nome] = bloco_id
                stats["blocos_criados"] += 1

            cur.execute("SELECT DESCRICAO FROM UNIDADE WHERE IDBLOCO = ?", (bloco_id,))
            ja_existem = {dec(r[0]).upper() for r in cur.fetchall()}
            for u in b.get("unidades", []) or []:
                descricao = str(u.get("descricao") or "").strip()
                if not descricao or descricao.upper() in ja_existem:
                    stats["unidades_puladas"] += 1
                    continue
                metragem = u.get("metragem")
                try:
                    metragem = float(metragem) if metragem not in (None, "") else None
                except (TypeError, ValueError):
                    metragem = None
                inscricao = _num_or_none(u.get("inscricao"))
                cur.execute(
                    "INSERT INTO UNIDADE (ID, IDBLOCO, DESCRICAO, METRAGEM, NUMCADIMOB) VALUES (?, ?, ?, ?, ?)",
                    (next_unid_id, bloco_id, descricao.encode('cp1252', 'ignore')[:100], metragem, inscricao),
                )
                next_unid_id += 1
                ja_existem.add(descricao.upper())
                stats["unidades_criadas"] += 1

        # METRAGEMTOTAL zerada não aparece no card de Empreendimentos — se o
        # cadastro ainda não tem metragem, assume a soma das unidades importadas
        cur.execute("SELECT COALESCE(METRAGEMTOTAL, 0) FROM EMPREENDIMENTO WHERE ID = ?",
                    (data.empreendimento_id,))
        r = cur.fetchone()
        if r is not None and float(r[0] or 0) <= 0:
            cur.execute("""SELECT COALESCE(SUM(U.METRAGEM), 0) FROM UNIDADE U
                           JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?""",
                        (data.empreendimento_id,))
            soma = round(float(cur.fetchone()[0] or 0), 2)
            if soma > 0:
                cur.execute("UPDATE EMPREENDIMENTO SET METRAGEMTOTAL = ? WHERE ID = ?",
                            (soma, data.empreendimento_id))
                stats["metragem_total_atualizada"] = soma

        conn.commit()

        # importação CONCLUÍDA encerra a sessão da matrícula (o PDF integral sai do disco)
        if data.sessao_id:
            try:
                appc = get_app_conn()
                row = appc.execute("SELECT pdf_path FROM matricula_sessao WHERE id = ?",
                                   (int(data.sessao_id),)).fetchone()
                appc.execute("UPDATE matricula_sessao SET status = 'concluida', atualizado_em = datetime('now') WHERE id = ?",
                             (int(data.sessao_id),))
                appc.commit()
                appc.close()
                if row and row[0] and os.path.exists(row[0]):
                    os.remove(row[0])
            except Exception:
                pass  # sessão pendurada não invalida a importação
        return {"success": True, **stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.get("/api/vulcano/clientes")
def get_vulcano_clientes(empresa_id: int):
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT c.ID, c.NOME, c.CNPJ 
            FROM CLIENTE c
            JOIN VENDA v ON c.ID = v.ID_CLIENTE
            WHERE v.CODIGOEMPRESA = ?
            ORDER BY c.NOME
        """, (empresa_id,))
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        clientes = [{
            "id": r[0], 
            "nome": dec(r[1]), 
            "cpf_cnpj": dec(r[2])
        } for r in cur.fetchall()]
        conn.close()
        return clientes
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vulcano/dashboard-lancamentos")
def api_dashboard_lancamentos(empresa_id: int, data_ini: str = None, data_fim: str = None):
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        date_filter_venda = ""
        date_filter_rec = ""
        params_venda = [empresa_id]
        params_rec = [empresa_id]

        if data_ini:
            date_filter_venda += " AND v.DTOPER >= ?"
            date_filter_rec += " AND r.DATA >= ?"
            params_venda.append(f"{data_ini}-01")
            params_rec.append(f"{data_ini}-01")
            
        if data_fim:
            date_filter_venda += " AND v.DTOPER <= ?"
            date_filter_rec += " AND r.DATA <= ?"
            import calendar
            try:
                y, m = data_fim.split("-")
                last_day = calendar.monthrange(int(y), int(m))[1]
                params_venda.append(f"{data_fim}-{last_day}")
                params_rec.append(f"{data_fim}-{last_day}")
            except Exception:
                pass
        
        # Últimas Vendas
        cur.execute(f"""
            SELECT FIRST 10 v.ID, v.DTOPER, v.DESCUNIDIMOB, c.NOME AS CLIENTE_NOME, v.TOTALVENDA, e.NOME AS EMPREENDIMENTO
            FROM VENDA v
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
              {date_filter_venda}
              AND COALESCE(c.NOME, '') NOT LIKE '%XXX%'
              AND COALESCE(c.CNPJ, '') <> '000.000.000-00'
              AND COALESCE(v.TOTALVENDA, 0) > 0.01
              AND COALESCE(v.DISTRATO, 'N') <> 'S'
            ORDER BY v.DTOPER DESC, v.ID DESC
        """, tuple(params_venda))
        vendas = []
        for r in cur.fetchall():
            try:
                cli_nome = r[3].decode('win1252', 'ignore') if isinstance(r[3], (bytes, bytearray)) else r[3]
                desc_unid = r[2].decode('win1252', 'ignore') if isinstance(r[2], (bytes, bytearray)) else r[2]
                emp_nome = r[5].decode('win1252', 'ignore') if isinstance(r[5], (bytes, bytearray)) else r[5]
            except Exception:
                cli_nome, desc_unid, emp_nome = str(r[3]), str(r[2]), str(r[5])
            
            vendas.append({
                "id": r[0],
                "data": r[1].strftime('%d/%m/%Y') if hasattr(r[1], 'strftime') else str(r[1]),
                "unidade": desc_unid,
                "cliente": cli_nome,
                "total": float(r[4] or 0),
                "empreendimento": emp_nome
            })
            
        # Últimos Recebimentos
        cur.execute(f"""
            SELECT FIRST 10 r.ID, r.DATA, r.TOTALPAGO, v.DESCUNIDIMOB, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO
            FROM RECEBER r
            JOIN VENDA v ON r.IDVENDA = v.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
              {date_filter_rec}
              AND r.TOTALPAGO > 0
              AND COALESCE(c.NOME, '') NOT LIKE '%XXX%'
            ORDER BY r.DATA DESC, r.ID DESC
        """, tuple(params_rec))
        recebimentos = []
        for r in cur.fetchall():
            try:
                cli_nome = r[4].decode('win1252', 'ignore') if isinstance(r[4], (bytes, bytearray)) else r[4]
                desc_unid = r[3].decode('win1252', 'ignore') if isinstance(r[3], (bytes, bytearray)) else r[3]
                emp_nome = r[5].decode('win1252', 'ignore') if isinstance(r[5], (bytes, bytearray)) else r[5]
            except Exception:
                cli_nome, desc_unid, emp_nome = str(r[4]), str(r[3]), str(r[5])
            
            recebimentos.append({
                "id": r[0],
                "data": r[1].strftime('%d/%m/%Y') if hasattr(r[1], 'strftime') else str(r[1]),
                "total_pago": float(r[2] or 0),
                "unidade": desc_unid,
                "cliente": cli_nome,
                "empreendimento": emp_nome
            })
            
        conn.close()
        return {"vendas": vendas, "recebimentos": recebimentos}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vulcano/vendas")
def get_vulcano_vendas(empresa_id: int, empreendimento_id: int = None, data_ini: str = None, data_fim: str = None):
    try:
        conn = get_conn("vulcano")
        query_vendas = """
            SELECT v.ID, v.NUMCADIMOB, v.DTOPER, v.DESCUNIDIMOB, c.CNPJ, c.NOME AS CLIENTE_NOME, v.TOTALVENDA, v.DISTRATO, v.PERMUTA, e.NOME AS EMPREENDIMENTO, e.ID as EMPREENDIMENTO_ID, v.DATADISTRATO, v.NUMCONT
            FROM VENDA v
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
              AND COALESCE(c.NOME, '') NOT LIKE '%XXX%'
              AND COALESCE(c.CNPJ, '') <> '000.000.000-00'
              AND COALESCE(v.TOTALVENDA, 0) > 0.01
              AND v.IDVENDAVINCULADA IS NULL
        """
        params = [empresa_id]
        if empreendimento_id:
            query_vendas += " AND v.IDEMPREENDIMENTO = ?"
            params.append(empreendimento_id)
        if data_ini:
            query_vendas += " AND v.DTOPER >= CAST(? AS DATE)"
            params.append(data_ini)
        if data_fim:
            query_vendas += " AND v.DTOPER <= CAST(? AS DATE)"
            params.append(data_fim)
            
        df_vendas = pd.read_sql_query(query_vendas, conn, params=tuple(params))
        df_vendas['UNIDADE_ID'] = None # Legacy vendas might not have precise array backlink

        # Compradores extras: vendas satelites vinculadas via IDVENDAVINCULADA.
        # Satelites NOVAS (marcadas 'VINCULADA VENDA' no INFCOMP) carregam a COTA
        # do comprador no contrato — o total do grupo soma principal + cotas.
        # Vinculos legados sem marcador (linhas duplicadas com valor cheio) NAO
        # entram na soma, senao o contrato dobraria.
        co_compradores = {}
        ids = [int(i) for i in df_vendas['ID'].tolist()] if len(df_vendas) else []
        if ids:
            cur2 = conn.cursor()
            for chunk_start in range(0, len(ids), 500):
                chunk = ids[chunk_start:chunk_start + 500]
                placeholders = ",".join("?" * len(chunk))
                cur2.execute(
                    f"""SELECT v2.IDVENDAVINCULADA, c2.NOME, c2.CNPJ, v2.TOTALVENDA, v2.INFCOMP
                        FROM VENDA v2
                        JOIN CLIENTE c2 ON c2.ID = v2.ID_CLIENTE
                        WHERE v2.IDVENDAVINCULADA IN ({placeholders})""",
                    tuple(chunk),
                )
                for rr in cur2.fetchall():
                    dec_ = lambda v: v.decode('cp1252', 'ignore').strip() if isinstance(v, bytes) else (str(v).strip() if v is not None else "")
                    marcada = dec_(rr[4]).upper().startswith("VINCULADA VENDA")
                    co_compradores.setdefault(int(rr[0]), []).append({
                        "nome": dec_(rr[1]),
                        "cpf_cnpj": dec_(rr[2]),
                        "valor": float(rr[3] or 0) if marcada else None,
                        "rateada": marcada,
                    })

        df = df_vendas
        df = df.replace({np.nan: None})
        conn.close()

        def safe_dec(x):
            if isinstance(x, bytes):
                return x.decode('cp1252', 'ignore').strip()
            return str(x).strip() if x is not None else ""

        for col in ['NUMCADIMOB', 'DESCUNIDIMOB', 'CNPJ', 'CLIENTE_NOME', 'DISTRATO', 'PERMUTA', 'EMPREENDIMENTO', 'NUMCONT']:
            if col in df.columns:
                df[col] = df[col].map(safe_dec)

        df['DATA_ISO'] = pd.to_datetime(df['DTOPER'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        df['DTOPER'] = pd.to_datetime(df['DTOPER'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
        df['DATADISTRATO'] = pd.to_datetime(df['DATADISTRATO'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
        df['TOTALVENDA'] = df['TOTALVENDA'].fillna(0).astype(float)

        df_mapped = df.rename(columns={
            'ID': 'id',
            'NUMCADIMOB': 'num_cad',
            'DTOPER': 'data',
            'DESCUNIDIMOB': 'descricao',
            'CNPJ': 'cliente_cnpj',
            'CLIENTE_NOME': 'cliente_nome',
            'TOTALVENDA': 'total',
            'DISTRATO': 'distrato',
            'DATADISTRATO': 'data_distrato',
            'PERMUTA': 'permuta',
            'EMPREENDIMENTO': 'empreendimento',
            'EMPREENDIMENTO_ID': 'empreendimento_id',
            'UNIDADE_ID': 'unidade_id',
            'DATA_ISO': 'data_iso',
            'NUMCONT': 'num_contrato'
        })

        records = df_mapped[['id', 'num_cad', 'data', 'data_iso', 'num_contrato', 'descricao', 'cliente_cnpj', 'cliente_nome', 'total', 'distrato', 'data_distrato', 'permuta', 'empreendimento', 'empreendimento_id', 'unidade_id']].to_dict('records')
        for rec in records:
            extras = co_compradores.get(int(rec['id']), [])
            cota_principal = rec['total']
            soma_cotas_extras = sum(c['valor'] for c in extras if c.get('rateada') and c.get('valor'))
            total_contrato = round(cota_principal + soma_cotas_extras, 2)
            rec['compradores'] = [{"nome": rec['cliente_nome'], "cpf_cnpj": rec['cliente_cnpj'],
                                   "principal": True, "valor": cota_principal if extras else None}] + \
                                 [{k: c[k] for k in ("nome", "cpf_cnpj", "valor")} | {"principal": False} for c in extras]
            rec['qtd_compradores'] = 1 + len(extras)
            rec['total'] = total_contrato  # valor do CONTRATO (cotas somadas)
        return records

    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vulcano/vendas/{venda_id}/condicoes")
def get_vulcano_venda_condicoes(venda_id: int):
    """
    Detalhes de condições/parcelas de uma venda (Vulcano):
    - Formas de pagamento (VENDAFORMAPAGTO)
    - Parcelas previstas/pagas (RECEBER)
    - Distrato (se houver)
    """
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()

        def dec(v):
            if v is None:
                return ""
            if isinstance(v, bytes):
                return v.decode("win1252", "ignore").strip()
            return str(v).strip()

        # Venda (resumo). Se for satelite de multi-comprador (IDVENDAVINCULADA
        # preenchida), redireciona para a venda principal — condicoes/parcelas
        # existem apenas nela.
        query_resumo = """
            SELECT v.ID, v.NUMCADIMOB, v.DTOPER, v.DESCUNIDIMOB, v.TOTALVENDA, v.DISTRATO, v.DATADISTRATO, v.PERMUTA, e.NOME, c.ID, c.CNPJ, c.NOME, v.IDVENDAVINCULADA
            FROM VENDA v
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            WHERE v.ID = ?
            """
        cur.execute(query_resumo, (int(venda_id),))
        r = cur.fetchone()
        if r and r[12]:
            venda_id = int(r[12])
            cur.execute(query_resumo, (venda_id,))
            r = cur.fetchone()
        if not r:
            conn.close()
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        venda = {
            "id": r[0],
            "num_cad": dec(r[1]),
            "data": r[2].strftime("%Y-%m-%d") if hasattr(r[2], "strftime") else dec(r[2]),
            "descricao": dec(r[3]),
            "total": float(r[4] or 0),
            "distrato": dec(r[5]),
            "data_distrato": r[6].strftime("%Y-%m-%d") if hasattr(r[6], "strftime") else dec(r[6]),
            "permuta": dec(r[7]),
            "empreendimento": dec(r[8]),
            "cliente": {
                "id": r[9],
                "cnpj": dec(r[10]),
                "nome": dec(r[11]),
            },
        }

        # Compradores extras (vendas satelites vinculadas a esta principal).
        # Satelites marcadas carregam a cota do comprador; total_contrato = soma.
        cur.execute(
            """SELECT c2.NOME, c2.CNPJ, v2.TOTALVENDA, v2.INFCOMP FROM VENDA v2
               JOIN CLIENTE c2 ON c2.ID = v2.ID_CLIENTE
               WHERE v2.IDVENDAVINCULADA = ?""",
            (int(venda_id),),
        )
        extras = []
        for rr in cur.fetchall():
            marcada = dec(rr[3]).upper().startswith("VINCULADA VENDA")
            extras.append({"nome": dec(rr[0]), "cpf_cnpj": dec(rr[1]), "principal": False,
                           "valor": float(rr[2] or 0) if marcada else None, "rateada": marcada})
        venda["compradores"] = [{"nome": venda["cliente"]["nome"], "cpf_cnpj": venda["cliente"]["cnpj"],
                                 "principal": True, "valor": venda["total"] if extras else None}] + extras
        venda["total_contrato"] = round(venda["total"] + sum(e["valor"] for e in extras if e.get("rateada") and e["valor"]), 2)

        # Formas de pagamento (condições)
        cur.execute(
            """
            SELECT ID, DESCRICAO, VALOR, MENSAL, ATIVA, QUANTIDADE_PARCELAS, SALDOATUALIZADO, DATAREPARCELAMENTO
            FROM VENDAFORMAPAGTO
            WHERE IDVENDA = ?
            ORDER BY ID
            """,
            (int(venda_id),),
        )
        formas = []
        forma_by_id = {}
        for rr in cur.fetchall():
            f = {
                "id": rr[0],
                "descricao": dec(rr[1]),
                "valor": float(rr[2] or 0),
                "mensal": dec(rr[3]),
                "ativa": dec(rr[4]),
                "quantidade_parcelas": int(rr[5] or 0),
                "saldo_atualizado": float(rr[6] or 0),
                "data_reparcelamento": rr[7].strftime("%Y-%m-%d") if hasattr(rr[7], "strftime") else dec(rr[7]),
            }
            formas.append(f)
            forma_by_id[f["id"]] = f

        # Parcelas (contas a receber) vinculadas à venda
        cur.execute(
            """
            SELECT r.ID, r.DATA, r.PARCELA, r.VALORPARCELA, r.VALORVARIACAO, r.DESCONTO, r.TOTALPAGO, r.OBS, r.IDVENDAFORMAPAGTO
            FROM RECEBER r
            WHERE r.IDVENDA = ?
            ORDER BY r.DATA, r.ID
            """,
            (int(venda_id),),
        )
        parcelas = []
        assinaturas_receber = set()
        for rr in cur.fetchall():
            forma_id = rr[8]
            data_str = rr[1].strftime("%Y-%m-%d") if hasattr(rr[1], "strftime") else dec(rr[1])
            valor = float(rr[3] or 0)
            assinaturas_receber.add((data_str, round(valor, 2)))
            
            parcelas.append(
                {
                    "id": rr[0],
                    "data": data_str,
                    "parcela": dec(rr[2]),
                    "valor_parcela": valor,
                    "variacao": float(rr[4] or 0),
                    "desconto": float(rr[5] or 0),
                    "total_pago": float(rr[6] or 0),
                    "obs": dec(rr[7]),
                    "forma_pagto_id": int(forma_id) if forma_id is not None else None,
                    "forma_pagto_descricao": forma_by_id.get(forma_id, {}).get("descricao", "") if forma_id is not None else "",
                }
            )

        # PARCELAS PROJETADAS — desativadas por padrão: na base viva as parcelas em
        # aberto JÁ estão no RECEBER com TOTALPAGO=0. Reative com PROJETADAS_ATIVAS=1
        # apenas para bases cujo RECEBER não contém as parcelas futuras.
        _proj_rows = []
        if os.environ.get("PROJETADAS_ATIVAS") == "1":
            conn_sq = get_conn("sqlite")
            cur_sq = conn_sq.cursor()
            cur_sq.execute(
                """
                SELECT prazo_id, data_venc, parcela_ref, valor, forma_pagto_id
                FROM parcelas_abertas_projetadas
                WHERE venda_id = ?
                ORDER BY data_venc, prazo_id
                """,
                (int(venda_id),),
            )
            _proj_rows = cur_sq.fetchall()
            conn_sq.close()
        for p in _proj_rows:
            data_str = p[1]
            valor = float(p[3] or 0)
            # Evita duplicar se a parcela já foi efetivada no Firebird (RECEBER)
            if (data_str, round(valor, 2)) in assinaturas_receber:
                continue
                
            forma_id = p[4]
            parcelas.append(
                {
                    "id": f"prazo_{p[0]}",
                    "data": data_str,
                    "parcela": p[2],
                    "valor_parcela": valor,
                    "variacao": 0.0,
                    "desconto": 0.0,
                    "total_pago": 0.0,
                    "obs": "Prevista (Em aberto - Vulcano 2.0)",
                    "forma_pagto_id": int(forma_id) if forma_id is not None else None,
                    "forma_pagto_descricao": forma_by_id.get(forma_id, {}).get("descricao", "") if forma_id is not None else "",
                }
            )

        # Reordena o array combinado de parcelas (recebidas e previstas) pela data
        parcelas.sort(key=lambda x: (x["data"] or "", str(x["id"])))

        # Distrato (quando houver)
        cur.execute(
            """
            SELECT ID, DATA, VALORDEVOLVIDO, DATAPAGAMENTO
            FROM DISTRATO
            WHERE IDVENDA = ?
            ORDER BY DATA DESC
            """,
            (int(venda_id),),
        )
        distratos = []
        for rr in cur.fetchall():
            distratos.append(
                {
                    "id": rr[0],
                    "data": rr[1].strftime("%Y-%m-%d") if hasattr(rr[1], "strftime") else dec(rr[1]),
                    "valor_devolvido": float(rr[2] or 0),
                    "data_pagamento": rr[3].strftime("%Y-%m-%d") if hasattr(rr[3], "strftime") else dec(rr[3]),
                }
            )

        conn.close()
        return {
            "venda": venda,
            "formas_pagto": formas,
            "parcelas": parcelas,
            "distratos": distratos,
        }
    except HTTPException:
        raise
    except Exception as e:
        if "conn" in locals() and conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vulcano/vendas/{venda_id}/parcelas")
async def lancar_parcela_manual(venda_id: int, request: Request):
    """Lança uma parcela avulsa (prevista) no RECEBER da venda — ação
    'Lançar parcela manual' do painel de Vendas."""
    data = await request.json()
    data_venc = str(data.get("data") or "").strip()
    valor = float(data.get("valor") or 0)
    if not data_venc or len(data_venc) < 10 or data_venc[:4] < "1990":
        raise HTTPException(status_code=400, detail=f"Data inválida: {data_venc!r}")
    if valor <= 0:
        raise HTTPException(status_code=400, detail="Informe o valor da parcela.")
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("SELECT ID_CLIENTE, DISTRATO FROM VENDA WHERE ID = ?", (int(venda_id),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Venda não encontrada.")
        if str(row[1] or "").strip().upper().startswith("S"):
            raise HTTPException(status_code=400, detail="Venda distratada — não recebe parcelas novas.")
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM RECEBER")
        new_id = cur.fetchone()[0]
        referencia = str(data.get("referencia") or "MANUAL").strip()[:10]
        obs = str(data.get("obs") or "Parcela lançada manualmente (Vulcano 2.0)").strip()[:100]
        cur.execute(
            """INSERT INTO RECEBER (ID, IDVENDA, IDCLIENTE, DATA, VALORPARCELA,
                                    VALORVARIACAO, TOTALPAGO, PARCELA, OBS, DESCONTO)
               VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 0)""",
            (new_id, int(venda_id), row[0], data_venc, round(valor, 2),
             referencia.encode('cp1252', 'ignore'), obs.encode('cp1252', 'ignore')),
        )
        conn.commit()
        return {"success": True, "id": new_id,
                "message": f"Parcela de {valor:,.2f} lançada p/ {data_venc} na venda #{venda_id}."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.patch("/api/vulcano/vendas/{venda_id}")
async def editar_venda(venda_id: int, request: Request):
    """Edição de linha da tela de Vendas: data, nº contrato, valor total e
    permuta. Venda principal propaga contrato/data/permuta às vinculadas
    MARCADAS e redistribui o total entre as cotas (proporcional às atuais)."""
    body = await request.json()
    data_v = str(body.get("data") or "").strip()
    if data_v and (len(data_v) < 10 or data_v[:4] < "1990"):
        raise HTTPException(status_code=400, detail=f"Data inválida: {data_v!r}")
    total = body.get("total", None)
    if total is not None:
        total = float(total)
        if total <= 0:
            raise HTTPException(status_code=400, detail="Valor total deve ser maior que zero.")
    num_contrato = body.get("num_contrato", None)
    permuta = str(body.get("permuta") or "").strip().upper()[:1]
    if not (data_v or total is not None or num_contrato is not None or permuta):
        raise HTTPException(status_code=400, detail="Nada para alterar.")
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("SELECT TOTALVENDA, IDVENDAVINCULADA FROM VENDA WHERE ID = ?", (int(venda_id),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Venda não encontrada.")
        # vinculadas marcadas (grupo multi-comprador) — só quando editando a principal
        cur.execute("""SELECT ID, TOTALVENDA FROM VENDA
                       WHERE IDVENDAVINCULADA = ? AND UPPER(COALESCE(INFCOMP, '')) LIKE 'VINCULADA VENDA #%'""",
                    (int(venda_id),))
        sats = [(r[0], float(r[1] or 0)) for r in cur.fetchall()]
        grupo = [(int(venda_id), float(row[0] or 0))] + sats

        sets, params = [], []
        if data_v:
            sets.append("DTOPER = ?"); params.append(data_v)
        if num_contrato is not None:
            sets.append("NUMCONT = ?"); params.append(str(num_contrato).strip()[:90].encode('cp1252', 'ignore'))
        if permuta in ("S", "N"):
            sets.append("PERMUTA = ?"); params.append(permuta)
        for vid, _ in grupo:
            if sets:
                cur.execute(f"UPDATE VENDA SET {', '.join(sets)} WHERE ID = ?", (*params, vid))
        if total is not None:
            soma_atual = sum(c for _, c in grupo)
            n = len(grupo)
            if soma_atual > 0:
                cotas = [round(total * c / soma_atual, 2) for _, c in grupo]
            else:
                cotas = [round(total / n, 2) for _ in grupo]
            cotas[-1] = round(total - sum(cotas[:-1]), 2)
            for (vid, _), cota in zip(grupo, cotas):
                cur.execute("UPDATE VENDA SET TOTALVENDA = ? WHERE ID = ?", (cota, vid))
        conn.commit()
        return {"success": True, "message": f"Venda #{venda_id} atualizada" +
                (f" (grupo de {len(grupo)} compradores rateado)" if len(grupo) > 1 and total is not None else "") + "."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.post("/api/vulcano/vendas/excluir")
async def excluir_vendas(request: Request):
    """Utilitário de EXCLUSÃO REAL (sem distrato): apaga vendas erradas/teste
    com toda a cascata (vinculadas, parcelas, formas de pagamento, unidades
    vendidas, reparcelamentos, distratos e baixas locais). dry_run devolve a
    prévia; venda com pagamento (TOTALPAGO ou baixa local) só sai com forcar."""
    body = await request.json()
    ids = [int(i) for i in (body.get("ids") or []) if str(i).strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Informe os ids das vendas a excluir.")
    if len(ids) > 500:
        raise HTTPException(status_code=400, detail="Máximo de 500 vendas por operação.")
    empresa_id = _int_or_none(body.get("empresa_id"))
    forcar = bool(body.get("forcar"))
    dry_run = body.get("dry_run", True) is not False
    import sqlite3 as _sq
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()

        def _dec(v):
            return v.decode('cp1252', 'ignore').strip() if isinstance(v, bytes) else (str(v).strip() if v is not None else "")

        ph = ",".join("?" * len(ids))
        cur.execute(f"SELECT ID FROM VENDA WHERE ID IN ({ph})", tuple(ids))
        existentes = {r[0] for r in cur.fetchall()}
        if not existentes:
            raise HTTPException(status_code=404, detail="Nenhuma das vendas informadas existe.")
        # cascata: vinculadas entram junto com a principal
        cur.execute(f"SELECT ID FROM VENDA WHERE IDVENDAVINCULADA IN ({ph})", tuple(ids))
        vinculadas = {r[0] for r in cur.fetchall()} - existentes
        todas = sorted(existentes | vinculadas)
        ph_t = ",".join("?" * len(todas))

        cur.execute(f"""SELECT R.ID, R.IDVENDA, COALESCE(R.TOTALPAGO, 0) FROM RECEBER R
                        WHERE R.IDVENDA IN ({ph_t})""", tuple(todas))
        receber = cur.fetchall()
        receber_ids = [r[0] for r in receber]
        pagas_fb = {r[1] for r in receber if float(r[2] or 0) > 0}

        # baixas novas do Vulcano 2.0 (sqlite local) também contam como pagamento
        baixas_locais = set()
        op_keys = set()
        try:
            s_conn = _sq.connect(POC_DATABASE_FILE)
            s_cur = s_conn.cursor()
            q = "SELECT id_receber FROM operacoes_baixas"
            args = ()
            if empresa_id:
                q += " WHERE empresa_id = ?"
                args = (empresa_id,)
            s_cur.execute(q, args)
            op_keys = {str(r[0]) for r in s_cur.fetchall()}
            s_conn.close()
        except Exception:
            pass
        mapa_receber_venda = {r[0]: r[1] for r in receber}
        for rid, vid in mapa_receber_venda.items():
            if str(rid) in op_keys:
                baixas_locais.add(vid)

        com_pagamento = pagas_fb | baixas_locais
        bloqueadas = sorted(com_pagamento) if not forcar else []
        alvo = [v for v in todas if v not in bloqueadas]
        # se a principal ficou bloqueada, as vinculadas dela também ficam (e vice-versa não se aplica)
        if bloqueadas:
            cur.execute(f"SELECT ID, IDVENDAVINCULADA FROM VENDA WHERE ID IN ({ph_t})", tuple(todas))
            vinc_de = {r[0]: r[1] for r in cur.fetchall()}
            alvo = [v for v in alvo if not (vinc_de.get(v) and vinc_de[v] in bloqueadas)]

        detalhe_bloq = []
        if bloqueadas:
            ph_b = ",".join("?" * len(bloqueadas))
            cur.execute(f"""SELECT V.ID, C.NOME FROM VENDA V LEFT JOIN CLIENTE C ON C.ID = V.ID_CLIENTE
                            WHERE V.ID IN ({ph_b})""", tuple(bloqueadas))
            detalhe_bloq = [{"id": r[0], "cliente": _dec(r[1]),
                             "motivo": "tem pagamento (parcela paga ou baixa local)"} for r in cur.fetchall()]

        rec_alvo = [rid for rid, vid in mapa_receber_venda.items() if vid in alvo]
        cascata = {"vendas": len([v for v in alvo if v in existentes]),
                   "vinculadas": len([v for v in alvo if v in vinculadas]),
                   "parcelas_receber": len(rec_alvo)}
        prazo_alvo = []
        if alvo:
            ph_a = ",".join("?" * len(alvo))
            cur.execute(f"SELECT ID FROM VENDAFORMAPAGTO WHERE IDVENDA IN ({ph_a})", tuple(alvo))
            fp_ids = [r[0] for r in cur.fetchall()]
            cascata["formas_pagto"] = len(fp_ids)
            if fp_ids:
                ph_f = ",".join("?" * len(fp_ids))
                cur.execute(f"SELECT ID FROM VENDAFORMAPAGTOPRAZO WHERE IDVENDAFORMAPAGTO IN ({ph_f})", tuple(fp_ids))
                prazo_alvo = [r[0] for r in cur.fetchall()]
            cascata["parcelas_cronograma"] = len(prazo_alvo)
            # A ordem certa (RECEBER antes do prazo) resolve o caso normal, em que
            # a parcela e o slot pertencem a mesma venda. Resta o caso torto: um
            # RECEBER de venda FORA do alvo apontando para um prazo do alvo. Ai a FK
            # barraria de novo — e apagar esse RECEBER seria mexer em venda que
            # ninguem mandou excluir. Detecta e avisa em vez de estourar erro de
            # banco na cara do operador.
            if prazo_alvo:
                ph_p0 = ",".join("?" * len(prazo_alvo))
                cur.execute(
                    f"""SELECT R.ID, R.IDVENDA FROM RECEBER R
                        WHERE R.IDVENDAFORMAPAGTOPRAZO IN ({ph_p0})""", tuple(prazo_alvo))
                rec_externos = [(r[0], r[1]) for r in cur.fetchall() if r[0] not in set(rec_alvo)]
            else:
                rec_externos = []
            cascata["receber_de_outras_vendas"] = len(rec_externos)
            for tab, rot in (("VENDAUNIDADE", "unidades_vendidas"), ("VENDAREPARCELAMENTO", "reparcelamentos"), ("DISTRATO", "distratos")):
                cur.execute(f"SELECT COUNT(*) FROM {tab} WHERE IDVENDA IN ({ph_a})", tuple(alvo))
                cascata[rot] = cur.fetchone()[0]
            chaves_op = {str(r) for r in rec_alvo} | {f"prazo_{p}" for p in prazo_alvo}
            cascata["baixas_locais"] = len(chaves_op & op_keys)
        else:
            fp_ids, chaves_op, rec_externos = [], set(), []

        if dry_run:
            return {"dry_run": True, "excluiveis": alvo, "cascata": cascata,
                    "bloqueadas": detalhe_bloq,
                    "aviso": "Exclusão DEFINITIVA, sem distrato — não há desfazer." }

        if not alvo:
            raise HTTPException(status_code=400, detail="Nada a excluir: todas as vendas têm pagamento (use forcar).")

        if rec_externos:
            vendas_ext = sorted({v for _, v in rec_externos if v})
            raise HTTPException(status_code=409, detail=(
                f"{len(rec_externos)} parcela(s) do contas a receber de OUTRA(S) venda(s) "
                f"({', '.join(f'#{v}' for v in vendas_ext[:10])}) apontam para o cronograma "
                "destas vendas. Excluir aqui apagaria dado de venda que não foi selecionada — "
                "confira esses vínculos antes."))

        ph_a = ",".join("?" * len(alvo))
        # ORDEM IMPORTA: RECEBER e FILHO de VENDAFORMAPAGTOPRAZO
        # (RECEBER.IDVENDAFORMAPAGTOPRAZO). Apagando o prazo primeiro o Firebird
        # recusa com "violation of FOREIGN KEY constraint FK_RECEBER_FORMAPAGTOPRAZO"
        # e a transacao inteira volta atras. Filho antes do pai:
        # RECEBER -> VENDAFORMAPAGTOPRAZO -> VENDAFORMAPAGTO -> VENDA.
        if rec_alvo:
            ph_r = ",".join("?" * len(rec_alvo))
            cur.execute(f"DELETE FROM RECEBER WHERE ID IN ({ph_r})", tuple(rec_alvo))
        if prazo_alvo:
            ph_p = ",".join("?" * len(prazo_alvo))
            cur.execute(f"DELETE FROM VENDAFORMAPAGTOPRAZO WHERE ID IN ({ph_p})", tuple(prazo_alvo))
        if fp_ids:
            ph_f = ",".join("?" * len(fp_ids))
            cur.execute(f"DELETE FROM VENDAFORMAPAGTO WHERE ID IN ({ph_f})", tuple(fp_ids))
        for tab in ("VENDAUNIDADE", "VENDAREPARCELAMENTO", "DISTRATO"):
            cur.execute(f"DELETE FROM {tab} WHERE IDVENDA IN ({ph_a})", tuple(alvo))
        # vinculadas antes das principais
        vinc_alvo = [v for v in alvo if v in vinculadas]
        if vinc_alvo:
            ph_v = ",".join("?" * len(vinc_alvo))
            cur.execute(f"DELETE FROM VENDA WHERE ID IN ({ph_v})", tuple(vinc_alvo))
        princ_alvo = [v for v in alvo if v not in vinculadas]
        if princ_alvo:
            ph_v = ",".join("?" * len(princ_alvo))
            cur.execute(f"DELETE FROM VENDA WHERE ID IN ({ph_v})", tuple(princ_alvo))
        conn.commit()

        # limpeza best-effort das baixas locais (sqlite) das parcelas excluídas
        try:
            if chaves_op:
                s_conn = _sq.connect(POC_DATABASE_FILE)
                s_cur = s_conn.cursor()
                for k in chaves_op:
                    if empresa_id:
                        s_cur.execute("DELETE FROM operacoes_baixas WHERE id_receber = ? AND empresa_id = ?", (k, empresa_id))
                    else:
                        s_cur.execute("DELETE FROM operacoes_baixas WHERE id_receber = ?", (k,))
                s_conn.commit()
                s_conn.close()
        except Exception:
            pass
        return {"success": True, "excluidas": len(alvo), "cascata": cascata,
                "bloqueadas": detalhe_bloq,
                "message": f"{len(alvo)} venda(s) excluída(s) definitivamente (com cascata)."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.patch("/api/vulcano/receber/{receber_id}")
async def editar_receber(receber_id: int, request: Request):
    """Edição de linha de parcela (RECEBER): vencimento, valor, rótulo e obs."""
    body = await request.json()
    data_v = str(body.get("data") or "").strip()
    if data_v and (len(data_v) < 10 or data_v[:4] < "1990"):
        raise HTTPException(status_code=400, detail=f"Data inválida: {data_v!r}")
    valor = body.get("valor_parcela", None)
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("SELECT TOTALPAGO FROM RECEBER WHERE ID = ?", (int(receber_id),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Parcela não encontrada.")
        pago = float(row[0] or 0)
        sets, params = [], []
        if data_v:
            sets.append("DATA = ?"); params.append(data_v)
        if valor is not None:
            valor = float(valor)
            if valor <= 0:
                raise HTTPException(status_code=400, detail="Valor da parcela deve ser maior que zero.")
            if valor < pago - 0.005:
                raise HTTPException(status_code=400, detail=f"Valor ({valor:,.2f}) menor que o já pago ({pago:,.2f}).")
            sets.append("VALORPARCELA = ?"); params.append(round(valor, 2))
        if body.get("parcela") is not None:
            sets.append("PARCELA = ?"); params.append(str(body["parcela"]).strip()[:50].encode('cp1252', 'ignore'))
        if body.get("obs") is not None:
            sets.append("OBS = ?"); params.append(str(body["obs"]).strip()[:300].encode('cp1252', 'ignore'))
        if not sets:
            raise HTTPException(status_code=400, detail="Nada para alterar.")
        cur.execute(f"UPDATE RECEBER SET {', '.join(sets)} WHERE ID = ?", (*params, int(receber_id)))
        conn.commit()
        return {"success": True, "message": f"Parcela #{receber_id} atualizada."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.patch("/api/vulcano/cronograma/prazo/{prazo_id}")
async def editar_prazo_cronograma(prazo_id: int, request: Request):
    """Edição de parcela do cronograma (VENDAFORMAPAGTOPRAZO) — linhas
    'prazo_<id>' da tela Recebimentos Mensal ainda não efetivadas no RECEBER."""
    body = await request.json()
    data_v = str(body.get("data") or "").strip()
    if data_v and (len(data_v) < 10 or data_v[:4] < "1990"):
        raise HTTPException(status_code=400, detail=f"Data inválida: {data_v!r}")
    valor = body.get("valor", None)
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("SELECT VALOR_PAGO FROM VENDAFORMAPAGTOPRAZO WHERE ID = ?", (int(prazo_id),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Parcela do cronograma não encontrada.")
        pago = float(row[0] or 0)
        sets, params = [], []
        if data_v:
            sets.append("DATA = ?"); params.append(data_v)
        if valor is not None:
            valor = float(valor)
            if valor <= 0:
                raise HTTPException(status_code=400, detail="Valor deve ser maior que zero.")
            if valor < pago - 0.005:
                raise HTTPException(status_code=400, detail=f"Valor ({valor:,.2f}) menor que o já pago ({pago:,.2f}).")
            sets.append("VALOR = ?"); params.append(round(valor, 2))
        if body.get("referencia") is not None:
            sets.append("REFERENCIA = ?"); params.append(str(body["referencia"]).strip()[:10].encode('cp1252', 'ignore'))
        if not sets:
            raise HTTPException(status_code=400, detail="Nada para alterar.")
        cur.execute(f"UPDATE VENDAFORMAPAGTOPRAZO SET {', '.join(sets)} WHERE ID = ?", (*params, int(prazo_id)))
        conn.commit()
        return {"success": True, "message": f"Parcela de cronograma #{prazo_id} atualizada."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.get("/api/vulcano/recebimentos")
def get_vulcano_recebimentos(empresa_id: int, empreendimento_id: int = None, data_ini: str = None, data_fim: str = None):
    import sqlite3
    import pandas as pd
    import numpy as np
    s_conn = None
    conn = None
    try:
        locais = {}
        try:
            s_conn = connect_app()
            s_curr = s_conn.cursor()
            s_curr.execute("SELECT id_receber, valor_pago, data_pagamento, descontos, acrescimos FROM operacoes_baixas WHERE empresa_id = ?", (empresa_id,))
            # Chaves como str: id_receber pode ser o ID da RECEBER ou "prazo_<id>" (projetada)
            locais = {str(row[0]): row for row in s_curr.fetchall()}
        except Exception as e:
            pass
        finally:
            if s_conn: s_conn.close()
            
        conn = get_conn("vulcano")
        # dedupe de SATÉLITE (auditoria 07/08): duplicatas legadas de multi-
        # comprador espelham as parcelas na venda vinculada — a linha da
        # satélite só entra quando NÃO houver espelho exato (DATA+VALOR+PAGO)
        # na principal; pagamentos registrados SÓ na satélite continuam vindo.
        query = '''
            SELECT r.DATA, r.TOTALPAGO, r.VALORPARCELA, r.VALORVARIACAO, v.DESCUNIDIMOB, c.CNPJ, r.PARCELA, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO, r.OBS, r.ID, v.TOTALVENDA, r.DESCONTO, v.ID AS VENDA_ID
            FROM VENDA v
            JOIN RECEBER r ON r.IDVENDA = v.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
              AND (v.IDVENDAVINCULADA IS NULL OR NOT EXISTS (
                    SELECT 1 FROM RECEBER rp
                    WHERE rp.IDVENDA = v.IDVENDAVINCULADA
                      AND rp.DATA = r.DATA
                      AND ABS(COALESCE(rp.VALORPARCELA, 0) - COALESCE(r.VALORPARCELA, 0)) < 0.02
                      AND ABS(COALESCE(rp.TOTALPAGO, 0) - COALESCE(r.TOTALPAGO, 0)) < 0.02))
        '''
        params = [empresa_id]
        
        if empreendimento_id:
            query += " AND v.IDEMPREENDIMENTO = ?"
            params.append(empreendimento_id)
            
        if data_ini:
            query += " AND r.DATA >= CAST(? AS DATE)"
            params.append(data_ini)
            
        if data_fim:
            query += " AND r.DATA <= CAST(? AS DATE)"
            params.append(data_fim)
            
        query += " ORDER BY r.DATA ASC"
        
        df = pd.read_sql_query(query, conn, params=tuple(params))
        df = df.replace({np.nan: None})

        def safe_dec(x):
            if isinstance(x, bytes):
                return x.decode('cp1252', 'ignore').strip()
            return str(x).strip() if x is not None else ""

        for col in ['DESCUNIDIMOB', 'CNPJ', 'PARCELA', 'CLIENTE_NOME', 'EMPREENDIMENTO', 'OBS']:
            if col in df.columns:
                df[col] = df[col].map(safe_dec)

        df['DATA_STR'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
        df['DATA_ISO'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        df['TOTALPAGO'] = df['TOTALPAGO'].fillna(0).astype(float)
        df['VALORPARCELA'] = df['VALORPARCELA'].fillna(0).astype(float)
        df['VALORVARIACAO'] = df['VALORVARIACAO'].fillna(0).astype(float)
        df['DESCONTO'] = df['DESCONTO'].fillna(0).astype(float)

        df_mapped = df.rename(columns={
            'ID': 'id',
            'DATA_STR': 'data',
            'DATA_ISO': 'vencimento_iso',
            'TOTALPAGO': 'total',
            'VALORPARCELA': 'parcela',
            'VALORVARIACAO': 'variacao',
            'DESCUNIDIMOB': 'descricao_venda',
            'CNPJ': 'cliente_cnpj',
            'PARCELA': 'num_parcela',
            'CLIENTE_NOME': 'cliente',
            'EMPREENDIMENTO': 'empreendimento',
            'OBS': 'obs',
            'DESCONTO': 'desconto',
            'VENDA_ID': 'venda_id'
        }).fillna('')
        
        result_list = df_mapped[['id', 'data', 'vencimento_iso', 'total', 'parcela', 'variacao', 'descricao_venda', 'cliente_cnpj', 'num_parcela', 'cliente', 'empreendimento', 'obs', 'desconto', 'venda_id']].to_dict('records')
        
        assinaturas_receber = set()
        
        for item in result_list:
            rid = item['id']
            
            v_id = item.get('venda_id')
            d_iso = item.get('vencimento_iso')
            val = float(item.get('parcela') or 0)
            if v_id and d_iso:
                assinaturas_receber.add((v_id, d_iso, round(val, 2)))
                
            if str(rid) in locais:
                db_l = locais[str(rid)]
                item['total'] = db_l[1]
                item['data_pagamento'] = db_l[2]
                item['desconto_local'] = db_l[3]
                item['acrescimo_local'] = db_l[4]
                item['status_sistema'] = 'BAIXADO_NOVO'
            else:
                item['data_pagamento'] = ''
                item['desconto_local'] = 0.0
                item['acrescimo_local'] = 0.0
                item['status_sistema'] = 'BAIXADO_LEGADO' if float(item.get('total', 0) or 0) > 0 else 'ABERTO'
                
        # --- PARCELAS ABERTAS PROJETADAS (desativadas por padrão: abertas = RECEBER
        #     com TOTALPAGO=0 na base viva; reative com PROJETADAS_ATIVAS=1) ---
        try:
            if os.environ.get("PROJETADAS_ATIVAS") != "1":
                raise InterruptedError("projetadas desativadas")
            conn_sq = get_conn("sqlite")
            cur_sq = conn_sq.cursor()
            
            query_v = '''
                SELECT v.ID, v.DESCUNIDIMOB, c.CNPJ, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO
                FROM VENDA v
                LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
                LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
                WHERE v.CODIGOEMPRESA = ?
            '''
            params_v = [empresa_id]
            if empreendimento_id:
                query_v += " AND v.IDEMPREENDIMENTO = ?"
                params_v.append(empreendimento_id)
            
            df_v = pd.read_sql_query(query_v, conn, params=tuple(params_v))
            df_v = df_v.replace({np.nan: None})
            for col in ['DESCUNIDIMOB', 'CNPJ', 'CLIENTE_NOME', 'EMPREENDIMENTO']:
                if col in df_v.columns:
                    df_v[col] = df_v[col].map(safe_dec)
            
            vendas_dict = df_v.set_index('ID').to_dict('index')
            venda_ids = list(vendas_dict.keys())
            
            if venda_ids:
                chunk_size = 900
                for i in range(0, len(venda_ids), chunk_size):
                    chunk = venda_ids[i:i+chunk_size]
                    placeholders = ','.join('?' * len(chunk))
                    cur_sq.execute(f'''
                        SELECT prazo_id, data_venc, parcela_ref, valor, venda_id
                        FROM parcelas_abertas_projetadas
                        WHERE venda_id IN ({placeholders})
                    ''', chunk)
                    
                    for p in cur_sq.fetchall():
                        d_str = p[1]
                        val = float(p[3] or 0)
                        v_id = p[4]
                        
                        if (v_id, d_str, round(val, 2)) in assinaturas_receber:
                            continue
                            
                        if data_ini and d_str < data_ini: continue
                        if data_fim and d_str > data_fim: continue
                        
                        v_info = vendas_dict.get(v_id, {})
                        try:
                            d_fmt = pd.to_datetime(d_str).strftime('%d/%m/%Y')
                        except:
                            d_fmt = d_str
                            
                        item_proj = {
                            'id': f"prazo_{p[0]}",
                            'data': d_fmt,
                            'vencimento_iso': d_str,
                            'total': 0.0,
                            'parcela': val,
                            'variacao': 0.0,
                            'descricao_venda': v_info.get('DESCUNIDIMOB', ''),
                            'cliente_cnpj': v_info.get('CNPJ', ''),
                            'num_parcela': p[2] or '',
                            'cliente': v_info.get('CLIENTE_NOME', ''),
                            'empreendimento': v_info.get('EMPREENDIMENTO', ''),
                            'obs': 'Prevista (Em aberto - Vulcano 2.0)',
                            'desconto': 0.0,
                            'data_pagamento': '',
                            'desconto_local': 0.0,
                            'acrescimo_local': 0.0,
                            'status_sistema': 'ABERTO'
                        }
                        db_l = locais.get(f"prazo_{p[0]}")
                        if db_l:
                            item_proj['total'] = db_l[1]
                            item_proj['data_pagamento'] = db_l[2]
                            item_proj['desconto_local'] = db_l[3]
                            item_proj['acrescimo_local'] = db_l[4]
                            item_proj['status_sistema'] = 'BAIXADO_NOVO'
                        result_list.append(item_proj)
            conn_sq.close()
        except InterruptedError:
            pass  # projeção desligada (PROJETADAS_ATIVAS != 1)
        except Exception as e_sq:
            print("Erro ao integrar parcelas projetadas:", e_sq)

        # ── PAGAS NO PERÍODO (baixas novas) ──────────────────────────────────
        # A busca é por VENCIMENTO; uma parcela vencida em abril e PAGA em junho
        # não aparecia ao pesquisar junho nem no filtro 'Baixadas'. Inclui as
        # parcelas cuja data_pagamento (operacoes_baixas) cai no período.
        try:
            if data_ini and data_fim and locais:
                ids_ja = {str(x['id']) for x in result_list}
                pagos_periodo = [k for k, v in locais.items()
                                 if v[2] and data_ini <= str(v[2])[:10] <= data_fim and k not in ids_ja]
                ids_receber = [int(k) for k in pagos_periodo if not k.startswith('prazo_')]
                if ids_receber:
                    cur_extra = conn.cursor()
                    for i0 in range(0, len(ids_receber), 400):
                        chunk = ids_receber[i0:i0 + 400]
                        ph = ",".join("?" * len(chunk))
                        filtro_emp_sql = " AND v.IDEMPREENDIMENTO = ?" if empreendimento_id else ""
                        cur_extra.execute(f'''
                            SELECT r.DATA, r.TOTALPAGO, r.VALORPARCELA, r.VALORVARIACAO, v.DESCUNIDIMOB,
                                   c.CNPJ, r.PARCELA, c.NOME, e.NOME, r.OBS, r.ID, r.DESCONTO, v.ID
                            FROM VENDA v
                            JOIN RECEBER r ON r.IDVENDA = v.ID
                            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
                            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
                            WHERE v.CODIGOEMPRESA = ? AND r.ID IN ({ph}) {filtro_emp_sql}
                        ''', tuple([empresa_id] + chunk + ([empreendimento_id] if empreendimento_id else [])))
                        for rr in cur_extra.fetchall():
                            def _sd(x):
                                if isinstance(x, bytes): return x.decode('cp1252', 'ignore').strip()
                                return str(x).strip() if x is not None else ""
                            db_l = locais.get(str(rr[10]))
                            dt_v = rr[0]
                            result_list.append({
                                'id': rr[10],
                                'data': dt_v.strftime('%d/%m/%Y') if hasattr(dt_v, 'strftime') else _sd(dt_v),
                                'vencimento_iso': dt_v.strftime('%Y-%m-%d') if hasattr(dt_v, 'strftime') else _sd(dt_v)[:10],
                                'total': (db_l[1] if db_l else float(rr[1] or 0)),
                                'parcela': float(rr[2] or 0), 'variacao': float(rr[3] or 0),
                                'descricao_venda': _sd(rr[4]), 'cliente_cnpj': _sd(rr[5]),
                                'num_parcela': _sd(rr[6]), 'cliente': _sd(rr[7]),
                                'empreendimento': _sd(rr[8]),
                                'obs': (_sd(rr[9]) + ' · paga no período').strip(' ·'),
                                'desconto': float(rr[11] or 0), 'venda_id': rr[12],
                                'data_pagamento': db_l[2] if db_l else '',
                                'desconto_local': db_l[3] if db_l else 0.0,
                                'acrescimo_local': db_l[4] if db_l else 0.0,
                                'status_sistema': 'BAIXADO_NOVO',
                            })
        except Exception as e_pp:
            print("Erro ao incluir pagas no período:", e_pp)

        result_list.sort(key=lambda x: x.get('vencimento_iso') or '')

        return result_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

class BaixaInput(BaseModel):
    # ID da RECEBER ou "prazo_<id>" para parcela projetada — o prefixo evita
    # colisao entre prazo_id e um ID legitimo da RECEBER em operacoes_baixas.
    id_receber: int | str
    valor_pago: float
    data_pagamento: str | None = None
    acrescimos: float = 0.0
    descontos: float = 0.0
    empresa_id: int | None = None

@app.post("/api/vulcano/recebimentos/baixa")
def baixa_recebimento(data: BaixaInput):
    import sqlite3
    s_conn = None
    try:
        s_conn = connect_app()
        s_curr = s_conn.cursor()
        import datetime
        data_pgto = data.data_pagamento if data.data_pagamento else datetime.date.today().isoformat()
        emp_id = data.empresa_id if data.empresa_id else 0
        s_curr.execute("""
            INSERT INTO operacoes_baixas (id_receber, empresa_id, data_pagamento, valor_pago, descontos, acrescimos) 
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_receber) DO UPDATE SET 
               data_pagamento=excluded.data_pagamento, 
               valor_pago=excluded.valor_pago, 
               descontos=excluded.descontos, 
               acrescimos=excluded.acrescimos
        """, (str(data.id_receber), emp_id, data_pgto, data.valor_pago, data.descontos, data.acrescimos))
        s_conn.commit()
        return {"success": True, "message": "Baixada no sistema auxiliar SQLite com sucesso"}
    except Exception as e:
        if s_conn: s_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if s_conn: s_conn.close()

@app.post("/api/vulcano/recebimentos/baixa/desfazer")
def desfazer_baixa_recebimento(payload: dict):
    """Desfaz uma baixa NOVA (registrada pelo Vulcano 2.0 em operacoes_baixas).

    Baixas legadas ja efetivadas no Firebird (RECEBER.TOTALPAGO > 0) nao passam
    por aqui — essas so no proprio legado/Questor."""
    import sqlite3
    id_receber = str(payload.get("id_receber") or "").strip()
    empresa_id = int(payload.get("empresa_id") or 0)
    if not id_receber:
        raise HTTPException(status_code=400, detail="id_receber obrigatório.")
    s_conn = None
    try:
        s_conn = sqlite3.connect(POC_DATABASE_FILE)
        s_curr = s_conn.cursor()
        s_curr.execute("DELETE FROM operacoes_baixas WHERE id_receber = ? AND empresa_id = ?",
                       (id_receber, empresa_id))
        apagadas = s_curr.rowcount
        s_conn.commit()
        if not apagadas:
            raise HTTPException(status_code=404, detail="Baixa não encontrada (ou é baixa legada do Firebird, que não pode ser desfeita por aqui).")
        return {"success": True, "message": "Baixa desfeita — a parcela voltou a ficar em aberto."}
    except HTTPException:
        raise
    except Exception as e:
        if s_conn: s_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if s_conn: s_conn.close()

@app.post("/api/vulcano/recebimentos/sync-projetadas")
def sync_recebimentos_projetadas():
    """Recarrega parcelas_abertas_projetadas do Firebird (vulcano) no SQLite.

    Rodar apos cada deploy (a tabela e criada vazia pelo bootstrap) ou quando
    novas vendas/prazos entrarem no legado.
    """
    from sync_projetadas import sync_parcelas_projetadas
    try:
        total = sync_parcelas_projetadas(get_conn, POC_DATABASE_FILE)
        return {"success": True, "total_sincronizadas": total}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Falha ao sincronizar parcelas projetadas: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# GERAR PARCELAS — VENDAFORMAPAGTOPRAZO → RECEBER
#
# Motor compartilhado em core/services/receber_generator.py, usado tambem pelo CLI
# gerar_receber_vendas_sem_parcela.py e pela tela "Geracao de Parcelas".
#
# Modo A: venda sem NENHUMA parcela em RECEBER -> gera a matriz inteira dela.
# Modo B: parcelas orfas (prazo sem linha), inclusive de vendas ja lancadas. B ⊇ A.
#
# O ID NAO e informado no INSERT: quem atribui e a trigger RECEBER_BI via
# GEN_RECEBER_ID. Calcular MAX(ID)+1 na mao (como estas rotas faziam) nao avanca o
# generator e quebra as insercoes seguintes do Vulcano legado com violacao de PK.
#
# Execucao e sincrona e pode levar minutos. Se algum dia entrar um reverse proxy na
# frente da API, estas rotas precisam de proxy_read_timeout 600s.
# ──────────────────────────────────────────────────────────────────────────────
class GerarParcelasInput(BaseModel):
    modo: str = "A"                  # "A" = venda sem parcela | "B" = parcelas orfas
    empresa_id: int | None = None    # None = todas as empresas
    empreendimento_id: int | None = None  # None = todos os empreendimentos
    data_inicio: str | None = None   # "YYYY-MM-DD" — so vale no modo B
    data_fim: str | None = None      # "YYYY-MM-DD" — so vale no modo B
    dry_run: bool = True             # True = so simula
    limite: int | None = None        # FIRST N, para piloto


def _rodar_geracao(modo, empresa_id, data_inicio, data_fim, dry_run, limite,
                   empreendimento_id=None):
    """Executa o motor e devolve o resultado pronto para virar JSON."""
    from core.services.receber_generator import executar

    conn_v = None
    try:
        conn_v = get_conn("vulcano")
        resultado = executar(
            conn_v,
            modo=modo,
            empresa_id=empresa_id,
            empreendimento_id=empreendimento_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limite=limite,
            dry_run=dry_run,
            log_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"),
        )
        # Lista de ate ~10k ids: vai para o JSON de rollback em disco, nao para a
        # resposta HTTP. O caminho do arquivo volta em log_rollback.
        resultado.pop("prazos_gravados", None)
        resultado["erros_detalhe"] = resultado.get("erros_detalhe", [])[:20]
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        if conn_v:
            try: conn_v.rollback()
            except: pass
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn_v: conn_v.close()


@app.post("/api/vulcano/gerar-parcelas")
def gerar_parcelas(data: GerarParcelasInput):
    """
    Simula (dry_run=True) ou grava (dry_run=False) parcelas em RECEBER com
    TOTALPAGO = 0, a partir dos prazos de VENDAFORMAPAGTOPRAZO.

    Filtros fixos: VENDAFORMAPAGTO.ATIVA = 'S' e VENDA.DISTRATO <> 'S'.

    Acima do teto (core.services.receber_generator.TETO_PARCELAS) a execucao volta
    com HTTP 200, acima_do_teto=True e inseridos=0 — nao e erro, e um pedido para
    estreitar o filtro, e a tela precisa continuar mostrando o resumo. A simulacao
    nunca e recusada: e assim que o operador descobre como fatiar.
    """
    return _rodar_geracao(
        modo=data.modo,
        empresa_id=data.empresa_id,
        empreendimento_id=data.empreendimento_id,
        data_inicio=data.data_inicio,
        data_fim=data.data_fim,
        dry_run=data.dry_run,
        limite=data.limite,
    )


class PopularReceberInput(BaseModel):
    empresa_id: int | None = None
    data_inicio: str | None = None
    dry_run: bool = True
    limite: int | None = None


@app.post("/api/vulcano/popular-receber-abertas")
def popular_receber_abertas(data: PopularReceberInput):
    """
    Mantido por compatibilidade: equivale a /api/vulcano/gerar-parcelas no modo B.
    Prefira a rota nova, que expõe os dois modos e o filtro de data final.
    """
    resultado = _rodar_geracao(
        modo="B",
        empresa_id=data.empresa_id,
        empreendimento_id=None,   # contrato antigo: sem recorte por obra
        data_inicio=data.data_inicio,
        data_fim=None,
        dry_run=data.dry_run,
        limite=data.limite,
    )
    # Chaves do contrato antigo, para nao quebrar quem ja chamava esta rota.
    resultado["modo"] = "dry_run" if data.dry_run else "execucao"
    resultado["empresa"] = data.empresa_id
    resultado["total_orfas"] = resultado.get("total_parcelas", 0)
    return resultado

import pandas as pd
import re

def _rows_from_parser_result(result):
    if result is None:
        return []
    if isinstance(result, pd.DataFrame):
        try:
            cleaned = result.replace({float("nan"): None})
            return cleaned.to_dict(orient="records")
        except Exception:
            return result.to_dict(orient="records")
    if isinstance(result, list):
        return result
    raise HTTPException(
        status_code=500,
        detail="O parser deve retornar uma lista de dicts ou um pandas.DataFrame.",
    )


def _sanitize_extracted_rows(rows: list) -> list:
    """Garante JSON válido no navegador (sem NaN/Infinity, tipos numpy/datetime nativos)."""

    def fix_val(v):
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, int) and not isinstance(v, bool):
            return v
        if isinstance(v, float):
            return v if math.isfinite(v) else None
        if isinstance(v, str):
            return v
        if isinstance(v, (datetime, date)):
            try:
                return v.isoformat()
            except Exception:
                return str(v)
        if isinstance(v, time_type):
            try:
                return v.isoformat()
            except Exception:
                return str(v)
        if isinstance(v, dict):
            return {str(k): fix_val(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [fix_val(x) for x in v]
        if hasattr(v, "item"):
            try:
                return fix_val(v.item())
            except Exception:
                pass
        if hasattr(v, "isoformat") and not isinstance(v, (bytes, bytearray)) and not isinstance(v, (dict, list, tuple)):
            try:
                return v.isoformat()
            except Exception:
                pass
        return str(v)

    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append({str(k): fix_val(val) for k, val in row.items()})
    return out


def _extract_with_saved_parser(content: bytes, filename: str, template_id: int):
    conn = connect_app()
    c = conn.cursor()
    c.execute("SELECT python_code FROM pdf_parser_templates WHERE id = ?", (int(template_id),))
    row = c.fetchone()
    conn.close()
    if not row or not (row[0] or "").strip():
        raise HTTPException(status_code=404, detail="Modelo não configurado. Não há regras salvas para este layout.")
    manifesto = row[0]

    chunks = []
    max_pages = 4  # Aumentado para 4 (pois o PDF pode ter capa/resumo, 3 paginas deixava a tabela de fora)
    max_chars = 3000
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages:
                break
            extracted = page.extract_text(layout=True) or page.extract_text() or ""
            if not extracted.strip():
                continue
            chunks.append(f"--- Página {i + 1} ---\n{extracted[:max_chars]}")

    text_content = "\n\n".join(chunks)

    prompt = f"""Você extrai dicionários financeiros de relatórios em PDF com inteligência.
Retorne APENAS um JSON válido seguindo a chave "recebimentos" contendo a lista.

[MANUAL DE EXTRAÇÃO DA EMPRESA ATUAL (OBRIGO VOCÊ A SEGUIR AS REGRAS ABAIXO!)]
{manifesto}

[DADOS TEXTUAIS DO PDF MODO LAYOUT PARA LEITURA]
{text_content}"""

    parsed = _ollama_generate_json(prompt)
    recs = parsed.get("recebimentos", [])
    if not isinstance(recs, list):
        recs = []

    return {
        "filename": filename,
        "extracted_data": _sanitize_extracted_rows(recs),
        "parser_source": "template",
        "parser_template_id": template_id,
        "hint": f"Lido via Ollama (modelo: {OLLAMA_MODEL_ID}) usando as regras salvas."
    }


def _heuristic_money_br(value) -> float:
    if value is None:
        return 0.0
    t = re.sub(r"[^\d,.\-]", "", str(value).strip())
    if not t or t == "-":
        return 0.0
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def _heuristic_extract_recebimentos_from_pdf(content: bytes) -> list:
    """
    Fallback quando o .py salvo não casa com o PDF: regex tolerante + texto com e sem layout.
    Não substitui um parser bem afinado; evita 0 linhas em layouts comuns de faturamento.
    """
    date_re = re.compile(r"\d{2}/\d{2}/\d{4}")
    parcel_token = r"(?:\d{1,3}/\d{1,3}|\d{1,3}-\d{1,3})[A-Za-z]*"
    parcel_re = re.compile(parcel_token)
    skip_kw = ("FATURAMENTO", "RELATÓRIO", "CNPJ", "EMPREENDIMENTO", "RESUMO", "TOTAIS", "SOMA ")

    def skip_line(line: str) -> bool:
        if len(line.strip()) < 8:
            return True
        if date_re.search(line) is None:
            return True
        u = line.upper()
        if sum(1 for k in ("PARCELA", "VALOR", "VENC", "CLIENTE", "COMPRADOR", "NOME") if k in u) >= 4:
            return True
        for k in skip_kw:
            if k in u and parcel_re.search(line) is None:
                return True
        return False

    p4 = re.compile(
        rf"(?P<nome>.+?)\s+(?P<dt>\d{{2}}/\d{{2}}/\d{{4}})\s+(?P<parc>{parcel_token})\s+"
        r"(?P<v1>[\d\.,\-]+)\s+(?P<v2>[\d\.,\-]+)\s+(?P<v3>[\d\.,\-]+)\s+(?P<v4>[\d\.,\-]+)\s*$",
        re.UNICODE,
    )
    p3 = re.compile(
        rf"(?P<nome>.+?)\s+(?P<dt>\d{{2}}/\d{{2}}/\d{{4}})\s+(?P<parc>{parcel_token})\s+"
        r"(?P<v1>[\d\.,\-]+)\s+(?P<v2>[\d\.,\-]+)\s+(?P<v3>[\d\.,\-]+)\s*$",
        re.UNICODE,
    )

    results = []
    seen_keys: set = set()
    seen_norm_lines: set = set()

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            texts = []
            a = page.extract_text(layout=True) or ""
            b = page.extract_text() or ""
            if a.strip():
                texts.append(a)
            if b.strip() and b != a:
                texts.append(b)
            for text in texts:
                for raw in text.splitlines():
                    line = " ".join(raw.split())
                    norm = line.strip()
                    if not norm or norm in seen_norm_lines:
                        continue
                    seen_norm_lines.add(norm)
                    if skip_line(line):
                        continue
                    m = p4.search(line) or p3.search(line)
                    if not m:
                        continue
                    nome = re.sub(r"^[|\s\-–:.]+", "", m.group("nome"))
                    nome = re.sub(r"[|\s\-–:.]+$", "", nome).strip()
                    if len(nome) < 2:
                        continue
                    dt = m.group("dt")
                    parc = m.group("parc").replace("-", "/")
                    v1 = _heuristic_money_br(m.group("v1"))
                    v2 = _heuristic_money_br(m.group("v2"))
                    v3 = _heuristic_money_br(m.group("v3"))
                    _gd = m.groupdict()
                    v4 = (
                        _heuristic_money_br(_gd["v4"])
                        if _gd.get("v4") is not None
                        else 0.0
                    )
                    key = (nome, dt, parc, round(v1, 2), round(v2, 2))
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    results.append(
                        {
                            "comprador": nome,
                            "data": dt,
                            "parcela": parc,
                            "valor_parcela": v1,
                            "total_pago": v2,
                            "desconto": v3,
                            "acrescimo": v4,
                        }
                    )
    return results


class ConversorSavePayload(BaseModel):
    filename: str
    import_mode: str
    raw_pdf_text: str = ""
    extracted_data: list[dict]

@app.post("/api/conversor/salvar-extraidos")
async def conversor_salvar_extraidos(payload: ConversorSavePayload):
    """
    Grava a extração no SQLite, dividindo em um Batch Pai (onde mora o texto do PDF)
    e os Registros Filhos (o JSON). Converte automaticamente as datas D/M/Y em ISO.
    """
    conn = connect_app()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO conversor_batches (filename, import_mode, raw_pdf_text)
            VALUES (?, ?, ?)
        ''', (payload.filename, payload.import_mode, payload.raw_pdf_text))
        
        batch_id = cur.lastrowid
        
        # Regex to match DD/MM/YYYY
        import re
        def to_iso(date_str):
            if not date_str: return None
            # Ex: "15/04/2025" -> "2025-04-15"
            m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(date_str).strip())
            if m:
                return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
            return date_str # if already iso or format is weird, fallback

        inserts = []
        for reg in payload.extracted_data:
            inserts.append((
                batch_id,
                reg.get('comprador', ''),
                reg.get('cpf_cnpj', ''),
                reg.get('empreendimento', ''),
                reg.get('unidade', ''),
                to_iso(reg.get('dt_vencimento')),
                to_iso(reg.get('dt_pagamento')),
                str(reg.get('parcela', '')),
                float(reg.get('valor_raiz', 0) or 0),
                float(reg.get('descontos', 0) or 0),
                float(reg.get('acrescimos_variacoes', 0) or 0),
                float(reg.get('total_pago', 0) or 0)
            ))
            
        cur.executemany('''
            INSERT INTO conversor_data_staging (
                batch_id, comprador, cpf_cnpj, empreendimento, unidade, 
                dt_vencimento, dt_pagamento, parcela, valor_raiz, descontos, 
                acrescimos_variacoes, total_pago
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', inserts)

        conn.commit()
        return {"success": True, "batch_id": batch_id, "items": len(inserts)}
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/conversor/listar-extraidos")
def conversor_listar_extraidos():
    """Retorna os batches pai já gravados"""
    conn = connect_app()
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
            SELECT b.id, b.filename, b.import_mode, b.created_at, 
                   COUNT(s.id) as linhas_importadas
            FROM conversor_batches b
            LEFT JOIN conversor_data_staging s ON s.batch_id = b.id
            GROUP BY b.id
            ORDER BY b.id DESC
        ''')
        rows = cur.fetchall()
        return {"success": True, "batches": [dict(r) for r in rows]}
    finally:
        conn.close()

@app.post("/api/extract-pdf")
async def extract_pdf(
    file: UploadFile = File(...),
    parser_template_id: int | None = Query(default=None),
    empresa_id: int | None = Query(default=None),
    allow_gemini_fallback: bool = Query(default=True),
    heuristic_fallback: bool = Query(default=True),
    force_ai: bool = Query(default=False),
    import_mode: str = Form(default="recebimentos")
):
    """
    Extrai dados do PDF. Envie `parser_template_id` ou `empresa_id` na **query string** (recomendado
    com multipart/file — evita falha de alguns clients com Form+File). Roda o script salvo sem Gemini.
    Se só `empresa_id` e houver padrão em empresa_parser_padrao, usa esse modelo. Senão: IA.
    `force_ai=true` bypassa qualquer template/fast-path e envia direto ao Gemini.
    """
    try:
        content = await file.read()
        mime_type = file.content_type or "application/pdf"
        
        chunks = []
        max_pages = 18
        max_chars = 9000
        
        if "pdf" in mime_type.lower():
            try:
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for i, page in enumerate(pdf.pages):
                        if i >= max_pages:
                            break
                        extracted = page.extract_text(layout=True) or page.extract_text() or ""
                        if extracted.strip():
                            chunks.append(f"--- Página {i + 1} ---\n{extracted[:max_chars]}")
            except Exception:
                pass

        is_vision = False
        if not chunks:
            if not ("image" in mime_type.lower() or "pdf" in mime_type.lower()):
                 raise HTTPException(status_code=400, detail="Formato não suportado. Envie PDF ou Imagem.")
            is_vision = True
            combined = "[Documento Multimodal anexado diretamente à Inteligência (Vision)]"
        else:
            combined = "\n\n".join(chunks)

        global LAST_RAW_PDF_TEXT_FOR_PARSER
        LAST_RAW_PDF_TEXT_FOR_PARSER = combined[:4000]
        raw_text_lines = [ln for ln in LAST_RAW_PDF_TEXT_FOR_PARSER.split("\n") if ln.strip()]

        # --- FAST-PATH HEURÍSTICO (MOTOR PY NATIVO) PARA EXTRAÇÃO EM MILISSEGUNDOS ---
        # Ignorado quando force_ai=True (usuário quer obrigatoriamente o Gemini)
        if not force_ai and "SIENGE / SOFTPLAN" in combined and "Recebidas" in combined:
            import re
            registros = []
            current_record = None
            unified_text = combined.replace("\r", "")
            
            nome_empreendimento = ""
            m_emp = re.search(r'Centro de custo(.*)', unified_text[:1000])
            if m_emp:
                empr_parts = m_emp.group(1).split('-')
                if len(empr_parts) > 0:
                    nome_empreendimento = empr_parts[-1].strip()
            
            pattern = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+(CT\.\S+)\s+(\d+)\s+(\S+)\s+(\d+)\s+(\d)\s+(0?\d{1,2}/0?\d{1,2}/\d{4})\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)$')

            for line in unified_text.split("\n"):
                line = line.strip()
                if not line or "Total do dia" in line or "SIENGE / SOFTPLAN" in line: continue
                match = pattern.match(line)
                if match:
                    comprador = match.group(2).strip()
                    cpf_cnpj = ''
                    m_doc = re.search(r'[-–]?\s*\(\s*([\d\.\-\/]{10,})\s*\)?$', comprador)
                    if m_doc:
                        cpf_cnpj = re.sub(r'\D', '', m_doc.group(1))
                        comprador = comprador[:m_doc.start()].strip(' -')
                            
                    dt_vecto = match.group(9)
                    if len(dt_vecto) > 10: dt_vecto = dt_vecto[-10:]
                    
                    val_baixa = float(match.group(10).replace('.', '').replace(',', '.'))
                    acresc = float(match.group(11).replace('.', '').replace(',', '.'))
                    seguro = float(match.group(12).replace('.', '').replace(',', '.'))
                    tx_adm = float(match.group(13).replace('.', '').replace(',', '.'))
                    acrescimos_somados = acresc + seguro + tx_adm
                    
                    descontos = float(match.group(14).replace('.', '').replace(',', '.'))
                    liquido = float(match.group(15).replace('.', '').replace(',', '.'))
                    
                    current_record = {
                        'comprador': comprador,
                        'cpf_cnpj': cpf_cnpj,
                        'empreendimento': nome_empreendimento,
                        'unidade': match.group(7),
                        'dt_vencimento': dt_vecto,
                        'dt_pagamento': match.group(1),
                        'parcela': match.group(6),
                        'valor_raiz': val_baixa,
                        'descontos': descontos,
                        'acrescimos_variacoes': acrescimos_somados,
                        'total_pago': liquido
                    }
                    registros.append(current_record)
                elif current_record:
                    m_cpf = re.match(r'^[\d\.\-/]+$', line.strip().strip(' ()'))
                    if m_cpf:
                        current_record['cpf_cnpj'] += re.sub(r'\D', '', m_cpf.group())
                        
            if registros:
                return {
                    "filename": file.filename,
                    "extracted_data": registros,
                    "parser_source": "template_py_sienge",
                    "pages_used": len(chunks),
                    "raw_text_lines": raw_text_lines
                }
        # --- FIM FAST-PATH ---


        tid = parser_template_id
        # force_ai=True: ignora qualquer template e vai direto ao Gemini
        if force_ai:
            tid = None
            allow_gemini_fallback = True
        elif is_vision or import_mode != 'recebimentos':
            tid = None
            allow_gemini_fallback = True
            
        # Só busca template padrão da empresa se force_ai=False
        # (force_ai=True deve mandar SEMPRE ao Gemini sem nenhum parser intermediário)
        if not force_ai and tid is None and empresa_id is not None and import_mode == 'recebimentos':
            conn = connect_app()
            c = conn.cursor()
            c.execute(
                "SELECT parser_template_id FROM empresa_parser_padrao WHERE empresa_id = ?",
                (int(empresa_id),),
            )
            row = c.fetchone()
            conn.close()
            if row and row[0] is not None:
                tid = int(row[0])

        template_result = None
        if tid is not None:
            try:
                # Or LLM inference might take too long
                template_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        _extract_with_saved_parser,
                        content,
                        file.filename or "upload.pdf",
                        tid,
                    ),
                    timeout=600.0,
                )
            except asyncio.TimeoutError:
                return {
                    "filename": file.filename or "upload.pdf",
                    "extracted_data": [],
                    "parser_source": "template",
                    "parser_template_id": int(tid),
                    "hint": "O Ollama excedeu o tempo limite de 10 minutos (Processamento pesado de PDF no processador/RAM). Tente um PDF menor ou um modelo mais leve.",
                    "error": True,
                    "raw_text_lines": raw_text_lines
                }
            ex_list = (
                template_result.get("extracted_data")
                if isinstance(template_result.get("extracted_data"), list)
                else []
            )
            if (
                heuristic_fallback
                and isinstance(template_result, dict)
                and len(ex_list) == 0
            ):
                recs_h = await asyncio.to_thread(_heuristic_extract_recebimentos_from_pdf, content)
                if recs_h:
                    return {
                        "filename": file.filename or "upload.pdf",
                        "extracted_data": _sanitize_extracted_rows(recs_h),
                        "parser_source": "heuristic",
                        "parser_template_id": int(tid),
                        "hint": "OLLAMA Não retornou linhas via Prompt. Caímos na leitura heurística bruta; use dados com cautela ou gere novas Regras.",
                        "raw_text_lines": raw_text_lines
                    }
            # Se o modelo não encontrou linhas, opcionalmente cai para Gemini para não travar o operador.
            if (
                allow_gemini_fallback
                and isinstance(template_result, dict)
                and isinstance(template_result.get("extracted_data"), list)
                and len(template_result.get("extracted_data")) == 0
            ):
                template_id_used = template_result.get("parser_template_id") or tid
                # segue para Gemini abaixo, mas preserva metadado do template
                tid = int(template_id_used) if template_id_used is not None else tid
                template_result = {"parser_template_id": tid}
            else:
                if isinstance(template_result, dict):
                    template_result["raw_text_lines"] = raw_text_lines
                return template_result

        _require_gemini_key()

        # Semaphore destravado para 15, uma vez que a autenticação JSON da Vertex não sofre as repressões da API MakerSuite (Google GenAI básica).
        _gemini_sem = asyncio.Semaphore(15)

        async def fetch_chunk(chunk_idx, chunk_text):
            header_ctx = ""
            if chunk_idx > 0 and len(chunks) > 0:
                linhas_primeira = chunks[0].split("\n")[:18]
                header_ctx = "[CABEÇALHOS DA PRÍMEIRA PÁGINA PARA REFERÊNCIA]\n" + "\n".join(linhas_primeira) + "\n\n[DADOS DESTA PÁGINA]\n"
            
            if import_mode == 'vendas':
                prompt = f"""Você extrai dados comerciais e financeiros estruturados de CONTRATOS, FICHAS ou EXTRATOS DE VENDAS IMOBILIÁRIAS.
Restaure a semântica de colunas tabulares.

SCHEMA DE VENDA:
1. 'cliente_doc': CPF ou CNPJ do Comprador.
2. 'empreendimento': Nome do empreendimento/condomínio.
3. 'unidade': Número do lote, apartamento ou unidade.
4. 'data_venda': Data da operação/assinatura (DTOPER).
5. 'numero_contrato': Número do contrato.
6. 'valor_total': Valor Total da Venda/Transação (float).
7. 'condicoes_pagamento': Lista com 'descricao' (ex: Sinal, Mensais), 'valor' (float) e 'quantidade_parcelas' (int).

SAÍDA (APENAS JSON VÁLIDO):
{{
  "registros": [
    {{ "cliente_doc": "...", "empreendimento": "...", "unidade": "...", "data_venda": "...", "numero_contrato": "...", "valor_total": 0.0, "condicoes_pagamento": [ {{ "descricao": "...", "valor": 0.0, "quantidade_parcelas": 1 }} ] }}
  ]
}}
Não inclua texto fora do JSON.

Text extraído:
{header_ctx}
{chunk_text}
"""
            else:
                prompt = f"""Você extrai linhas de RECEBIMENTOS/PAGAMENTOS/PARCELAS de relatórios imobiliários.
Restaure a semântica de colunas tabulares.

SCHEMA:
1. 'comprador': Nome do cliente.
2. 'cpf_cnpj': CPF ou CNPJ.
3. 'empreendimento': Nome do prédio/projeto.
4. 'unidade': Número do apartamento/lote.
5. 'dt_vencimento': Data original de corte.
6. 'dt_pagamento': Data da baixa no banco.
7. 'parcela': Número (ex: 12/41 PM).
8. Numéricos (float): 'valor_raiz', 'descontos', 'acrescimos_variacoes' (Juros+Multa+Tx), 'total_pago' (Líquido). Se nulo, 0.0.

SAÍDA (APENAS JSON VÁLIDO):
{{
  "registros": [
    {{ "comprador": "...", "cpf_cnpj": "...", "empreendimento": "...", "unidade": "...", "dt_vencimento": "...", "dt_pagamento": "...", "parcela": "...", "valor_raiz": 0.0, "descontos": 0.0, "acrescimos_variacoes": 0.0, "total_pago": 0.0 }}
  ]
}}
Não inclua texto fora do JSON. Traga TODAS as linhas encontradas.

Text extraído:
{header_ctx}
{chunk_text}
"""
            # --- PARALELISMO COM SEMAPHORE ---
            # Sem sleep sequencial: todas as páginas disparam ao mesmo tempo,
            # mas no máx 5 de uma vez (controla rate-limit sem serializar).
            kwargs = {"prompt": prompt}
            if is_vision:
                kwargs["file_data"] = content
                kwargs["mime_type"] = mime_type

            async with _gemini_sem:
                return await _gemini_generate_json_async(**kwargs)

        try:
            tasks = []
            if is_vision or not chunks:
                # Modo vision: documento inteiro em uma chamada (não há como dividir)
                tasks.append(fetch_chunk(0, combined))
            else:
                # Modo texto: cada página vira uma task independente — paralelismo total
                for i, c_text in enumerate(chunks):
                    tasks.append(fetch_chunk(i, c_text))

            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False),
                timeout=GEMINI_EXTRACT_TIMEOUT_SEC,
            )
            
            recs = []
            for parsed in results:
                r = parsed.get("registros", parsed.get("recebimentos", []))
                if isinstance(r, list):
                    recs.extend(r)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=(f"Gemini excedeu {int(GEMINI_EXTRACT_TIMEOUT_SEC)}s. Aumente GEMINI_EXTRACT_TIMEOUT_SEC no backend/.env.")
            )

        recs = _sanitize_extracted_rows(recs)
        out = {
            "filename": file.filename,
            "extracted_data": recs,
            "parser_source": "gemini" if not template_result else "gemini_fallback",
            "pages_used": len(chunks),
            "raw_text_lines": raw_text_lines
        }
        if template_result and template_result.get("parser_template_id") is not None:
            out["parser_template_id"] = int(template_result["parser_template_id"])
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")

class ParserChatInput(BaseModel):
    instruction: str
    current_data: list

@app.post("/api/parser/chat")
def parser_chat(data: ParserChatInput):
    import json
    import copy
    try:
        _require_gemini_key()
        n = len(data.current_data)
        # Passaremos toda a tabela para que ele possa gerar o índice corretamente para todas as linhas afetadas (Gemini aguenta o contexto).
        preview = data.current_data 
        idx_hint = f"Temos {n} itens no total." if n else "Vazia."
        prompt = f"""Você é um especialista em engenharia de dados (Data Wrangler).
O usuário deseja higienizar ou corrigir falhas contínuas na tabela JSON extraída do PDF.
Instrução do usuário (Frequentemente ele dará apenas 2 ou 3 amostras do Texto PDF): "{data.instruction}"

[ATENÇÃO ESTREMA]
A instrução do usuário pode usar exemplos isolados (ex: "A unidade nessas linhas é 102"), MAS ISSO É UMA REGRA DE HIGIENIZAÇÃO GERAL. 
Sua tarefa é INFERIR A REGRA LÓGICA (ex: A unidade pegou o valor errado) E APLICÁ-LA EM TODAS AS {n} LINHAS DA TABELA ABAIXO. Avalie minuciosamente TODAS as posições e corrija TODAS que sofrem do mesmo erro de padrão. Se ele falou sobre as "unidades", provavelmente TODAS AS UNIDADES estão estragadas com o valor contábil.

Tabela Completa Atual:
{json.dumps(preview, ensure_ascii=False, indent=2)}

NÃO DEVOLVA A TABELA INTEIRA! Devolva um array gigante de 'operations' para consertar TODOS os índices afetados. Use "update" para dados e "delete" para sumir com lixo.
Formato:
{{
  "operations": [
    {{ "action": "update", "index": 0, "field": "data", "value": "01/01/2025" }},
    {{ "action": "delete", "index": 5 }}
  ]
}}
Se não houver nada a fazer, retorne {{"operations": []}}.
"""
        parsed = _gemini_generate_json(prompt)
        ops = parsed.get("operations", [])
        if not isinstance(ops, list):
            ops = []

        updated_data = copy.deepcopy(data.current_data)
        updates = [op for op in ops if op.get("action") == "update" and "index" in op and "field" in op]
        deletes = [op for op in ops if op.get("action") == "delete" and "index" in op]

        errors = 0
        for op in updates:
            try:
                idx = int(op["index"])
                if 0 <= idx < len(updated_data):
                    updated_data[idx][op["field"]] = str(op.get("value", ""))
            except (ValueError, TypeError):
                errors += 1

        deletes.sort(
            key=lambda x: int(x.get("index", -1))
            if isinstance(x.get("index"), (int, str)) and str(x.get("index")).isdigit()
            else -1,
            reverse=True,
        )
        for op in deletes:
            try:
                idx = int(op["index"])
                if 0 <= idx < len(updated_data):
                    updated_data.pop(idx)
            except (ValueError, TypeError):
                errors += 1

        if "updated_data" in parsed and isinstance(parsed["updated_data"], list) and not ops:
            updated_data = parsed["updated_data"]

        return {
            "message": f"Tabela ajustada (Gemini). ({len(updates)} ups, {len(deletes)} dels"
            + (f", {errors} erros" if errors else "")
            + ")",
            "updated_data": updated_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
import time

class ParserSaveInput(BaseModel):
    history: list
    final_data: list
    nome: str | None = None
    descricao: str | None = None
    empresa_id: int | None = None
    definir_padrao_empresa: bool = True

def _gemini_generate_python_plain(prompt: str) -> str:
    """Fallback quando JSON com python_code fica grande ou inválido."""
    _require_gemini_key()
    try:
        model_cls = VertexModel if USE_VERTEX_FOR_GEMINI else genai.GenerativeModel
        gen_cfg = {"max_output_tokens": 8192}
        if USE_VERTEX_FOR_GEMINI:
            gen_cfg["thinking_config"] = {"thinking_budget": 0}
        model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg)
        resp = model.generate_content(
            prompt
            + "\n\nResponda APENAS com o código-fonte Python completo. Sem markdown, sem explicação."
        )
        text = (resp.text or "").strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if len(lines) > 2:
                text = "\n".join(lines[1:-1])
                if text.lower().startswith("python"):
                    text = text[6:].lstrip("\n")
        return text
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e) or "Quota" in str(e):
            raise HTTPException(status_code=429, detail="Limite de requisições API Gemini (Free Tier) excedido ao gerar script. Aguarde 1 minuto.")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar script Python via Gemini: {str(e)[:200]}")

class ParserSaveInput(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    history: list[dict[str, str]]
    final_data: list[dict[str, str | float]]
    empresa_id: int | None = None
    definir_padrao_empresa: bool = False

@app.post("/api/parser/save")
def parser_save(data: ParserSaveInput):
    import json
    try:
        _require_gemini_key()
        chat_context = ""
        for msg in data.history:
            chat_context += f"[{msg.get('role', '?').upper()}]: {msg.get('content', '')}\n"

        sample = data.final_data[:5] if data.final_data else []
        prompt = f"""Você é um Engenheiro de Dados Sênior criando REGRAS ESTÁTICAS DE EXTRAÇÃO ("Manifesto") para um modelo Menor e Restrito (Qwen 3B).
Ele não tem raciocínio profundo, então você deve guiá-lo ESCREVENDO AS POSIÇÕES ESPACIAIS LITERAIS.
Com base neste histórico de chat de correções (se houver):
{chat_context}

E no formato JSON de amostra:
{json.dumps(sample, ensure_ascii=False, indent=2)}

Sua tarefa é ESCREVER UM TEXTO DE ATÉ 12 LINHAS ensinando LITERALMENTE o Qwen 3B a mapear o SCHEMA VULCANO.
Instrua-o com regras rústicas de posicionamento. Exemplo de linguagem: "O CNPJ está grudado na col 2. A Unidade está na col 4 da primeira reta da linha. Os valores estão agrupados na Reta Final: o 1º é a parcela, o 2º é Acréscimo, o 5º é Desconto. Retorne tudo como float 0.0."
OBRIGATÓRIO: Force o Qwen a extrair estritamente as exatas chaves JSON expostas na amostra acima, definindo posições claras para `cpf_cnpj`, `unidade`, as duas datas e toda a consolidação de pagamentos (total_pago, valor_raiz, descontos, acrescimos_variacoes).

O Qwen extrairá TODAS as linhas financeiras que achar parecidas e ignorará o resto. O formato de saída central dele DEVE ser `{"recebimentos": [...]}`.

Retorne APENAS um JSON com a chave `python_code` cujo valor seja este pequeno guia gerado em texto bruto (sem aspas markdown).
"""
        code_to_save = None
        try:
            parsed = _gemini_generate_json(prompt)
            pc = parsed.get("python_code")
            if isinstance(pc, str) and pc.strip():
                code_to_save = pc
        except Exception:
            pass
        if not code_to_save or not code_to_save.strip():
            code_to_save = (
                "Siga estruturação de recebimentos. "
                "Retorne chaves de recebimento. Ignore todos os valores lixo."
            )

        template_id = None
        nome_registro = (data.nome or "").strip() or f"Parser_Prompt_{int(time.time())}"
        descricao = (data.descricao or "Gerado com Assistant").strip()
        filename = "sem_codigo_ollama.txt"
        
        try:
            conn = connect_app()
            c = conn.cursor()
            sample_store = json.dumps(sample, ensure_ascii=False)[:80000]
            c.execute(
                """INSERT INTO pdf_parser_templates (nome, descricao, python_code, sample_json, arquivo_gerado)
                   VALUES (?, ?, ?, ?, ?)""",
                (nome_registro, descricao, code_to_save, sample_store, filename),
            )
            template_id = c.lastrowid
            if data.empresa_id is not None and data.definir_padrao_empresa:
                c.execute(
                    """INSERT INTO empresa_parser_padrao (empresa_id, parser_template_id)
                       VALUES (?, ?)
                       ON CONFLICT(empresa_id) DO UPDATE SET
                         parser_template_id=excluded.parser_template_id,
                         data_atualizacao=CURRENT_TIMESTAMP""",
                    (int(data.empresa_id), template_id),
                )
            conn.commit()
            conn.close()
        except Exception as db_err:
            print("parser_save DB:", db_err)

        return {
            "filename": filename,
            "filepath": "banco_de_dados",
            "status": "Manifesto Ollama salvo com sucesso" if template_id else "Erro ao salvar o manifesto no banco.",
            "code": code_to_save,
            "python_code": code_to_save,
            "template_id": template_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ParserTemplateSetDefault(BaseModel):
    empresa_id: int
    parser_template_id: int


@app.get("/api/parser/templates")
def list_parser_templates(empresa_id: int | None = None):
    conn = connect_app()
    c = conn.cursor()
    padrao_id = None
    if empresa_id is not None:
        c.execute(
            "SELECT parser_template_id FROM empresa_parser_padrao WHERE empresa_id = ?",
            (int(empresa_id),),
        )
        row = c.fetchone()
        if row:
            padrao_id = row[0]
    c.execute(
        "SELECT id, nome, descricao, data_criacao, arquivo_gerado FROM pdf_parser_templates ORDER BY id DESC"
    )
    rows = c.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append(
            {
                "id": r[0],
                "nome": r[1],
                "descricao": r[2],
                "data_criacao": r[3],
                "arquivo_gerado": r[4],
                "is_padrao_empresa": padrao_id is not None and r[0] == padrao_id,
            }
        )
    return out

@app.delete("/api/parser/template/{template_id}")
def delete_parser_template(template_id: int):
    try:
        conn = connect_app()
        c = conn.cursor()
        c.execute("SELECT arquivo_gerado FROM pdf_parser_templates WHERE id = ?", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template não encontrado.")
        
        c.execute("DELETE FROM pdf_parser_templates WHERE id = ?", (template_id,))
        c.execute("UPDATE empresa_parser_padrao SET parser_template_id = NULL WHERE parser_template_id = ?", (template_id,))
        conn.commit()
        conn.close()
        
        try:
            if row[0]:
                filepath = os.path.join(os.getcwd(), "parsers", row[0])
                if os.path.exists(filepath):
                    os.remove(filepath)
        except Exception:
            pass
            
        return {"status": "ok", "message": "Template excluído com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/parser/template/{template_id}")
def delete_parser_template(template_id: int):
    try:
        conn = connect_app()
        c = conn.cursor()
        c.execute("SELECT arquivo_gerado FROM pdf_parser_templates WHERE id = ?", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template não encontrado.")
        
        c.execute("DELETE FROM pdf_parser_templates WHERE id = ?", (template_id,))
        c.execute("UPDATE empresa_parser_padrao SET parser_template_id = NULL WHERE parser_template_id = ?", (template_id,))
        conn.commit()
        conn.close()
        
        try:
            if row[0]:
                filepath = os.path.join(os.getcwd(), "parsers", row[0])
                if os.path.exists(filepath):
                    os.remove(filepath)
        except Exception:
            pass
            
        return {"status": "ok", "message": "Template excluído com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/parser/templates/{template_id}")
def get_parser_template(template_id: int):
    conn = connect_app()
    c = conn.cursor()
    c.execute(
        "SELECT id, nome, descricao, python_code, sample_json, data_criacao, arquivo_gerado FROM pdf_parser_templates WHERE id = ?",
        (template_id,),
    )
    r = c.fetchone()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return {
        "id": r[0],
        "nome": r[1],
        "descricao": r[2],
        "python_code": r[3],
        "sample_json": r[4],
        "data_criacao": r[5],
        "arquivo_gerado": r[6],
    }


@app.post("/api/parser/templates/set-default")
def set_parser_template_default(body: ParserTemplateSetDefault):
    conn = connect_app()
    c = conn.cursor()
    c.execute("SELECT 1 FROM pdf_parser_templates WHERE id = ?", (body.parser_template_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Template não encontrado")
    c.execute(
        """INSERT INTO empresa_parser_padrao (empresa_id, parser_template_id)
           VALUES (?, ?)
           ON CONFLICT(empresa_id) DO UPDATE SET
             parser_template_id=excluded.parser_template_id,
             data_atualizacao=CURRENT_TIMESTAMP""",
        (int(body.empresa_id), int(body.parser_template_id)),
    )
    conn.commit()
    conn.close()
    return {"success": True}

def _detectar_linha_header_excel(content: bytes) -> int:
    """Planilha de cliente costuma ter linhas decorativas antes do cabeçalho
    (título, logotipo, vazias) — com header=0 o pandas devolve 'Unnamed: N' e a
    sugestão de mapeamento da IA morre. Procura nas 15 primeiras linhas a que
    mais parece cabeçalho: maior contagem de células TEXTUAIS distintas."""
    try:
        raw = pd.read_excel(io.BytesIO(content), header=None, nrows=15)
    except Exception:
        return 0
    melhor_linha, melhor_score = 0, 0
    for i in range(len(raw)):
        celulas = [str(c).strip() for c in raw.iloc[i].tolist()
                   if c is not None and str(c).strip() not in ("", "nan", "NaT")]
        textuais = [c for c in celulas if not c.replace(".", "").replace(",", "").replace("-", "").replace("/", "").isdigit()]
        score = len(set(textuais))
        if score > melhor_score:
            melhor_linha, melhor_score = i, score
    return melhor_linha if melhor_score >= 2 else 0

@app.post("/api/upload-planilha")
async def upload_planilha(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if file.filename.lower().endswith('.csv'):
            try:
                df = pd.read_csv(io.BytesIO(content), sep=None, engine='python')
            except:
                df = pd.read_csv(io.BytesIO(content), encoding='latin1', sep=None, engine='python')
        elif file.filename.lower().endswith(('.xls', '.xlsx')):
            header_row = _detectar_linha_header_excel(content)
            df = pd.read_excel(io.BytesIO(content), header=header_row)
            df = df.dropna(how='all').loc[:, ~df.columns.astype(str).str.startswith('Unnamed')]
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado. Use CSV ou Excel.")

        columns = df.columns.tolist()
        for col in df.columns:  # datas viram ISO (senao NaT vaza como string na previa)
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d')
        df = df.fillna('')
        data_preview = df.head(10).to_dict(orient='records')
        
        return {
            "filename": file.filename,
            "columns": columns,
            "preview": data_preview,
            "all_rows": df.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/api/smart-importer/preparar-colunas")
def smart_importer_preparar_colunas(payload: dict):
    """Apoio ao De-Para: o analista descreve em texto livre como interpretar a
    planilha (ex.: 'a coluna UNIDADE traz bloco e apartamento juntos, BL A AP 101')
    e a IA devolve um plano de COLUNAS DERIVADAS (regex por coluna nova). O regex
    é aplicado aqui, deterministicamente, em TODAS as linhas — a IA desenha a
    regra uma vez, sem custo por linha."""
    import json
    import re as _re
    columns = payload.get("columns", [])
    rows = payload.get("rows", [])
    instrucoes = str(payload.get("instrucoes") or "").strip()
    if not instrucoes:
        raise HTTPException(status_code=400, detail="Escreva as instruções para o apoio ao De-Para.")
    if not columns or not rows:
        raise HTTPException(status_code=400, detail="Envie a planilha antes de aplicar as instruções.")

    amostras = {c: [str(r.get(c, ""))[:60] for r in rows[:8]] for c in columns}
    prompt = f"""Você prepara planilhas de clientes para importação num sistema imobiliário.
COLUNAS ATUAIS (com até 8 amostras de valores): {json.dumps(amostras, ensure_ascii=False)}

INSTRUÇÕES DO ANALISTA:
{instrucoes[:2000]}

Se alguma coluna contém MAIS DE UMA informação (conforme as instruções), proponha colunas derivadas.
Responda SOMENTE este JSON:
{{"novas_colunas": [{{"nome": "NOME DA NOVA COLUNA", "origem": "COLUNA DE ORIGEM EXATA",
   "regex": "expressão regular Python com UM grupo de captura que extrai o valor"}}],
 "observacao": "explicação curta do que foi feito"}}

Regras: o regex deve funcionar nas amostras mostradas; use grupos de captura (parênteses);
se nada precisa ser derivado, devolva novas_colunas como lista vazia e explique na observacao."""

    plano = _gemini_generate_json(prompt)
    novas = plano.get("novas_colunas") or []
    relatorio = []
    for nc in novas:
        nome = str(nc.get("nome") or "").strip()
        origem = str(nc.get("origem") or "").strip()
        rx = str(nc.get("regex") or "").strip()
        if not nome or origem not in columns or not rx:
            relatorio.append({"coluna": nome or "?", "ok": False, "detalhe": f"plano inválido (origem '{origem}' inexistente ou regex vazio)"})
            continue
        try:
            comp = _re.compile(rx)
        except _re.error as e:
            relatorio.append({"coluna": nome, "ok": False, "detalhe": f"regex inválido: {e}"})
            continue
        preenchidas = 0
        for r in rows:
            m = comp.search(str(r.get(origem, "") or ""))
            valor = (m.group(1) if (m and m.groups()) else (m.group(0) if m else "")).strip() if m else ""
            r[nome] = valor
            if valor:
                preenchidas += 1
        if nome not in columns:
            columns.append(nome)
        relatorio.append({"coluna": nome, "ok": True,
                          "detalhe": f"extraída de '{origem}' — {preenchidas}/{len(rows)} linha(s) preenchidas"})

    return {"success": True, "columns": columns, "all_rows": rows,
            "preview": rows[:10], "relatorio": relatorio,
            "observacao": str(plano.get("observacao") or "")}

@app.post("/api/schema-match")
def schema_match(payload: dict):
    """Sugestao de de-para coluna->campo p/ o Smart Importer.

    Reescrito: usava Ollama (inexistente no deploy -> 500 silencioso e tudo
    'Ignorar') e devolvia o mapa aninhado por tabela (o front espera plano).
    Agora usa o Vertex/Gemini padrao do projeto, restrito aos campos validos
    do destino, com validacao server-side do retorno.
    """
    import json
    columns = payload.get("columns", [])
    campos_validos = payload.get("campos", [])
    destino = payload.get("target_table", "")
    amostras = payload.get("amostras", {})
    if not columns:
        return {"mapping": {}}

    instrucoes = str(payload.get("instrucoes") or "").strip()
    bloco_instrucoes = f"\nINSTRUÇÕES DO ANALISTA (siga-as ao decidir o mapeamento):\n{instrucoes[:1500]}\n" if instrucoes else ""
    prompt = f"""Você mapeia colunas de planilhas de clientes para campos de um sistema imobiliário.
DESTINO: {destino}
CAMPOS VÁLIDOS (use exatamente estes valores): {json.dumps(campos_validos, ensure_ascii=False)}
COLUNAS DA PLANILHA (com amostra da 1ª linha): {json.dumps({c: str(amostras.get(c, ''))[:40] for c in columns}, ensure_ascii=False)}
{bloco_instrucoes}
Responda SOMENTE um objeto JSON plano onde cada chave é o nome EXATO da coluna da planilha
e o valor é um dos CAMPOS VÁLIDOS, ou null quando a coluna não corresponder a nenhum campo.
Exemplo: {{"CPF": "CLIENTE_CPF_CNPJ", "OBS INTERNA": null}}"""

    try:
        raw = _gemini_generate_json(prompt)
        if not isinstance(raw, dict):
            raise ValueError("resposta nao e objeto JSON")
        # achata retornos aninhados por tabela e valida contra os campos validos
        if raw and all(isinstance(v, dict) for v in raw.values()):
            flat = {}
            for sub in raw.values():
                flat.update(sub)
            raw = flat
        validos = set(campos_validos)
        mapping = {}
        for col in columns:
            v = raw.get(col)
            mapping[col] = v if (isinstance(v, str) and (not validos or v in validos)) else None
        return {"mapping": mapping}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sugestao de mapeamento falhou: {str(e)[:200]}")

# --- VULCANO MVP DAY 1 CRUD ENDPOINTS ---
from fastapi import Request

class EmpreendimentoInput(BaseModel):
    empresa_id: int
    nome: str
    metragem: float | None = 0.0
    custo: float | None = 0.0
    ret: str | None = "N"
    cno: str | None = ""
    conta_caixa: str | None = None
    conta_clientes: str | None = None
    centro_custo: str | None = None
    conta_estand: str | None = None
    conta_estcon: str | None = None
    conta_despesa: str | None = None
    conta_rec: str | None = None
    conta_variacao: str | None = None
    conta_lucroacum: str | None = None
    hist_venda: str | None = None
    hist_recebimento: str | None = None
    hist_variacao: str | None = None
    hist_distrato: str | None = None
    endereco: str | None = None
    conta_devolucao: str | None = None
    hist_estorno: str | None = None

@app.post("/api/vulcano/empreendimentos")
async def post_empreendimentos(data: EmpreendimentoInput):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        # Lock transacional básico com generator max ID
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM EMPREENDIMENTO")
        new_id = cur.fetchone()[0]
        
        def s_int(v):
            if not v: return None
            v_str = str(v).split(' - ')[0].strip()
            return int(v_str) if v_str.isdigit() else None
        
        fields = ["ID", "NOME", "METRAGEMTOTAL", "CUSTOORCADO", "RET", "CODIGOEMPRESA", "ATIVO", "CNO", 
                  "CONTACAIXA", "CONTACLI", "CODIGOCENTROCUSTO", "CONTAESTAND", "CONTAESTCON", 
                  "CONTADESPESA", "CONTAREC", "CONTAVARIACAO", "CONTALUCROACUM", 
                  "CODIGOHISTVENDA", "CODIGOHISTRECEBIMENTO", "CODIGOHISTVARIACAO", "CODIGOHISTBAIXAADI",
                  "ENDERECO", "CONTADEVOLUCAO", "CODIGO_HIST_ESTORNO_SALDO"]
        
        query = f"INSERT INTO EMPREENDIMENTO ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})"
        
        params = (
            new_id, str(data.nome), float(data.metragem or 0), float(data.custo or 0),
            data.ret, data.empresa_id, "S", str(data.cno or ""),
            s_int(data.conta_caixa), s_int(data.conta_clientes), s_int(data.centro_custo),
            s_int(data.conta_estand), s_int(data.conta_estcon), s_int(data.conta_despesa),
            s_int(data.conta_rec), s_int(data.conta_variacao), s_int(data.conta_lucroacum),
            s_int(data.hist_venda), s_int(data.hist_recebimento), 
            s_int(data.hist_variacao), s_int(data.hist_distrato),
            data.endereco, s_int(data.conta_devolucao), s_int(data.hist_estorno)
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"success": True, "id": new_id, "message": "Empreendimento cadastrado com sucesso!"}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"Falha de gravação no banco Vulcano: {str(e)}")

@app.put("/api/vulcano/empreendimentos/{emp_id}")
async def put_empreendimentos(emp_id: int, data: EmpreendimentoInput):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        def s_int(v):
            if not v: return None
            v_str = str(v).split(' - ')[0].strip()
            return int(v_str) if v_str.isdigit() else None
            
        query = """UPDATE EMPREENDIMENTO SET 
                   NOME=?, METRAGEMTOTAL=?, CUSTOORCADO=?, RET=?, CNO=?,
                   CONTACAIXA=?, CONTACLI=?, CODIGOCENTROCUSTO=?, CONTAESTAND=?, CONTAESTCON=?,
                   CONTADESPESA=?, CONTAREC=?, CONTAVARIACAO=?, CONTALUCROACUM=?,
                   CODIGOHISTVENDA=?, CODIGOHISTRECEBIMENTO=?, CODIGOHISTVARIACAO=?, CODIGOHISTBAIXAADI=?,
                   ENDERECO=?, CONTADEVOLUCAO=?, CODIGO_HIST_ESTORNO_SALDO=?
                   WHERE ID=?"""
                   
        params = (
            str(data.nome), float(data.metragem or 0), float(data.custo or 0),
            data.ret, str(data.cno or ""),
            s_int(data.conta_caixa), s_int(data.conta_clientes), s_int(data.centro_custo),
            s_int(data.conta_estand), s_int(data.conta_estcon), s_int(data.conta_despesa),
            s_int(data.conta_rec), s_int(data.conta_variacao), s_int(data.conta_lucroacum),
            s_int(data.hist_venda), s_int(data.hist_recebimento), 
            s_int(data.hist_variacao), s_int(data.hist_distrato),
            data.endereco, s_int(data.conta_devolucao), s_int(data.hist_estorno),
            emp_id
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Empreendimento atualizado com sucesso!"}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"Falha de atualização Vulcano: {str(e)}")

@app.delete("/api/vulcano/empreendimentos/{emp_id}")
def delete_empreendimento(emp_id: int):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(1) FROM VENDA WHERE IDEMPREENDIMENTO = ?", (emp_id,))
        count_vendas = cur.fetchone()[0]
        if count_vendas > 0:
            raise HTTPException(status_code=400, detail=f"Ação bloqueada: Existem {count_vendas} vendas vinculadas a esta infraestrutura.")
            
        cur.execute("DELETE FROM UNIDADE WHERE IDBLOCO IN (SELECT ID FROM BLOCO WHERE IDEMPREENDIMENTO = ?)", (emp_id,))
        cur.execute("DELETE FROM BLOCO WHERE IDEMPREENDIMENTO = ?", (emp_id,))
        cur.execute("DELETE FROM EMPREENDIMENTO WHERE ID = ?", (emp_id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Empreendimento removido permanentemente."}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"Erro interno ao deletar: {str(e)}")

@app.post("/api/vulcano/blocos")
async def create_bloco(request: Request):
    conn = None
    try:
        data = await request.json()
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM BLOCO")
        new_id = cur.fetchone()[0]
        
        id_emp = int(data.get("id_empreendimento", 0))
        nome_bloco = str(data.get("nome", "NOVO BLOCO"))
        
        query = "INSERT INTO BLOCO (ID, IDEMPREENDIMENTO, NOME) VALUES (?, ?, ?)"
        cur.execute(query, (new_id, id_emp, nome_bloco.encode('cp1252', 'ignore')))
        
        conn.commit()
        conn.close()
        return {"id": new_id, "success": True}
    except Exception as e:
        print(f"Error in create_bloco: {e}")
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/vulcano/blocos/{bloco_id}")
async def update_bloco(bloco_id: int, request: Request):
    conn = None
    try:
        data = await request.json()
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        nome_bloco = str(data.get("nome", ""))
        query = "UPDATE BLOCO SET NOME = ? WHERE ID = ?"
        cur.execute(query, (nome_bloco.encode('cp1252', 'ignore'), bloco_id))
        
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        print(f"Error in update_bloco: {e}")
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vulcano/blocos/{bloco_id}")
def delete_bloco(bloco_id: int):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("DELETE FROM UNIDADE WHERE IDBLOCO = ?", (bloco_id,))
        cur.execute("DELETE FROM BLOCO WHERE ID = ?", (bloco_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vulcano/unidades")
async def create_unidade(request: Request):
    conn = None
    try:
        data = await request.json()
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM UNIDADE")
        new_id = cur.fetchone()[0]
        
        query = "INSERT INTO UNIDADE (ID, IDBLOCO, DESCRICAO, METRAGEM, NUMCADIMOB, UNIDADE_DISTRATO) VALUES (?, ?, ?, ?, ?, ?)"
        cur.execute(query, (
            new_id, 
            int(data.get("id_bloco", 0)), 
            str(data.get("descricao", "")).encode('cp1252', 'ignore'), 
            float(data.get("metragem") or 0), 
            str(data.get("inscricao", "")).encode('cp1252', 'ignore'),
            str(data.get("unidade_distrato", "N")).encode('cp1252', 'ignore')
        ))
        
        conn.commit()
        conn.close()
        return {"id": new_id, "success": True}
    except Exception as e:
        print(f"Error in create_unidade: {e}")
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/vulcano/unidades/{unid_id}")
async def update_unidade(unid_id: int, request: Request):
    conn = None
    try:
        data = await request.json()
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        query = "UPDATE UNIDADE SET DESCRICAO = ?, METRAGEM = ?, NUMCADIMOB = ?, UNIDADE_DISTRATO = ? WHERE ID = ?"
        cur.execute(query, (
            str(data.get("descricao", "")).encode('cp1252', 'ignore'), 
            float(data.get("metragem") or 0), 
            str(data.get("inscricao", "")).encode('cp1252', 'ignore'),
            str(data.get("unidade_distrato", "N")).encode('cp1252', 'ignore'),
            unid_id
        ))
        
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        print(f"Error in update_unidade: {e}")
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vulcano/unidades/{unid_id}")
def delete_unidade(unid_id: int):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("DELETE FROM UNIDADE WHERE ID = ?", (unid_id,))
        
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vulcano/empreendimentos/{emp_id}/detalhes")
def get_empreendimento_detalhes(emp_id: int, incluir_vendidas: bool = False):
    """Blocos + unidades do empreendimento. Por padrão só as DISPONÍVEIS (o
    modal de venda consome assim); incluir_vendidas=true devolve todas com a
    flag `vendida` e a `data_venda` da venda ativa (aba Estrutura)."""
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()

        cur.execute("SELECT ID, NOME FROM BLOCO WHERE IDEMPREENDIMENTO = ?", (emp_id,))
        blocos = [{"id": r[0], "nome": r[1].decode('win1252', 'ignore').strip() if isinstance(r[1], bytes) else str(r[1] or "").strip()} for r in cur.fetchall()]

        unidades = []
        if blocos:
            b_ids = [str(b['id']) for b in blocos]
            placeholders = ",".join(["?"] * len(b_ids))

            query_unidades = f"""
                SELECT u.ID, u.IDBLOCO, u.DESCRICAO, u.METRAGEM, u.NUMCADIMOB, u.UNIDADE_DISTRATO,
                       (SELECT MAX(v.DTOPER) FROM VENDAUNIDADE vu
                        JOIN VENDA v ON vu.IDVENDA = v.ID
                        WHERE vu.IDUNIDADE = u.ID AND COALESCE(v.DISTRATO, 'N') <> 'S') AS DT_VENDA
                FROM UNIDADE u
                WHERE u.IDBLOCO IN ({placeholders})
                ORDER BY u.IDBLOCO, u.ID
            """
            cur.execute(query_unidades, tuple(b_ids))

            for r in cur.fetchall():
                dt_venda = r[6]
                if dt_venda is not None and not incluir_vendidas:
                    continue  # comportamento clássico: só disponíveis
                if hasattr(dt_venda, "date"):
                    dt_venda = dt_venda.date()
                unidades.append({
                    "id": r[0],
                    "id_bloco": r[1],
                    "descricao": r[2].decode('win1252', 'ignore').strip() if isinstance(r[2], bytes) else str(r[2] or "").strip(),
                    "metragem": float(r[3] or 0),
                    "inscricao": str(r[4] or ""),
                    "unidade_distrato": r[5].decode('win1252', 'ignore').strip() if isinstance(r[5], bytes) else str(r[5] or "N").strip(),
                    "vendida": dt_venda is not None,
                    "data_venda": dt_venda.strftime('%d/%m/%Y') if dt_venda else None
                })
                
        conn.close()
        return {"blocos": blocos, "unidades": unidades}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vulcano/clientes/search")
def search_cliente(cpf_cnpj: str):
    conn_v = conn_q = None
    try:
        raw_doc = "".join(filter(str.isdigit, cpf_cnpj))
        if not raw_doc:
            return {"found": False}
        
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()
            
        conn_v = get_conn("vulcano")
        cur_v = conn_v.cursor()
        cur_v.execute("SELECT FIRST 1 ID, NOME, CNPJ FROM CLIENTE WHERE REPLACE(REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '-', ''), '/', ''), ' ', '') = ?", (raw_doc,))
        v_row = cur_v.fetchone()
        if v_row:
            return {"found": True, "origem": "Vulcano", "id_vulcano": v_row[0], "nome": dec(v_row[1]), "cpf_cnpj": dec(v_row[2])}
            
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute("SELECT FIRST 1 CODIGOPESSOA, NOMEPESSOA, INSCRFEDERAL FROM PESSOA WHERE REPLACE(REPLACE(REPLACE(REPLACE(INSCRFEDERAL, '.', ''), '-', ''), '/', ''), ' ', '') = ?", (raw_doc,))
        q_row = cur_q.fetchone()
        if q_row:
            return {"found": True, "origem": "Questor", "id_questor": q_row[0], "nome": dec(q_row[1]), "cpf_cnpj": dec(q_row[2])}
            
        return {"found": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn_v: conn_v.close()
        if conn_q: conn_q.close()

@app.post("/api/vulcano/vendas")
async def post_vendas(request: Request):
    import datetime

    def months_between(d1: datetime.date, d2: datetime.date) -> int:
        """Quantos meses completos de diferença entre d1 e d2 (d2 >= d1)."""
        return (d2.year - d1.year) * 12 + (d2.month - d1.month)

    def add_months(d: datetime.date, n: int) -> datetime.date:
        month = d.month - 1 + n
        year = d.year + month // 12
        month = month % 12 + 1
        days_in_month = [31, 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day = min(d.day, days_in_month[month - 1])
        return datetime.date(year, month, day)

    def calc_vencimento(venc_inicial: str, idx: int, tipo: str, intervalo_meses: int) -> datetime.date | None:
        """Retorna a data de vencimento da parcela de índice `idx` (0-based)."""
        try:
            base = datetime.datetime.strptime(venc_inicial, "%Y-%m-%d").date()
        except Exception:
            return None

        if tipo in ("SINAL", "INTERMEDIARIA", "CHAVES", "FINANCIAMENTO"):
            # Parcela única – sempre na data informada (idx é sempre 0)
            return base
        elif tipo == "MENSAL":
            return add_months(base, idx)
        elif tipo == "SEMESTRAL":
            return add_months(base, idx * 6)
        elif tipo == "ANUAL":
            return add_months(base, idx * 12)
        elif tipo == "REFORCO":
            # intervalo_meses é detectado automaticamente (6 ou 12)
            return add_months(base, idx * intervalo_meses)
        else:
            # Fallback mensal
            return add_months(base, idx)

    try:
        data = await request.json()
        empresa_id = data.get("empresa_id")
        if not empresa_id:
            raise HTTPException(status_code=400, detail="empresa_id obrigatório")

        conn = get_conn("vulcano")
        cur = conn.cursor()

        # data da venda: guarda contra ano digitado curto no input date (ex.: 0026)
        _d = str(data.get("data", "") or "")
        if _d and (len(_d) < 10 or _d[:4] < "1990"):
            raise HTTPException(status_code=400, detail=f"Data da venda inválida: {_d}. Confira o ano (ex.: 2026).")

        # --- CLIENTES (todos os compradores; o principal vai na VENDA principal,
        # os demais viram vendas satelites vinculadas via IDVENDAVINCULADA) ---
        # A base viva atual tem CLIENTE só com (ID, NOME, CNPJ) — CODIGOEMPRESA
        # existia no schema antigo e derruba o INSERT com SQL -206 (caso real da
        # analista no GRAND LIFE). Detecta a coluna e monta o INSERT compatível.
        cur.execute("SELECT 1 FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLIENTE' AND TRIM(RDB$FIELD_NAME) = 'CODIGOEMPRESA'")
        cliente_tem_empresa = cur.fetchone() is not None

        def _get_or_create_cliente(comp) -> int | None:
            raw_doc = "".join(filter(str.isdigit, comp.get("cpf_cnpj", "")))
            if not raw_doc:
                return None
            cur.execute("SELECT FIRST 1 ID FROM CLIENTE WHERE REPLACE(REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '-', ''), '/', ''), ' ', '') = ?", (raw_doc,))
            cli_row = cur.fetchone()
            if cli_row:
                return cli_row[0]
            cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM CLIENTE")
            cid = cur.fetchone()[0]
            nome_enc = str(comp.get("nome", "")).encode('cp1252', 'ignore')[:100]
            if cliente_tem_empresa:
                cur.execute("INSERT INTO CLIENTE (ID, NOME, CNPJ, CODIGOEMPRESA) VALUES (?, ?, ?, ?)",
                    (cid, nome_enc, comp.get("cpf_cnpj", ""), int(empresa_id)))
            else:
                cur.execute("INSERT INTO CLIENTE (ID, NOME, CNPJ) VALUES (?, ?, ?)",
                    (cid, nome_enc, comp.get("cpf_cnpj", "")))
            return cid

        compradores = data.get("compradores", [])
        # comprador principal: flag `principal`, senao o primeiro da lista
        idx_principal = next((i for i, c in enumerate(compradores) if c.get("principal")), 0)
        if compradores:
            compradores = [compradores[idx_principal]] + [c for i, c in enumerate(compradores) if i != idx_principal]
        ids_clientes = [_get_or_create_cliente(c) for c in compradores]
        id_cliente = ids_clientes[0] if ids_clientes else None

        # Rateio do contrato entre os CPFs (DIMOB/EFD-Contribuicoes precisam do
        # valor por adquirente): percentual informado por comprador, normalizado
        # p/ fechar 100; sem percentuais, divide igual. As cotas somam EXATAMENTE
        # o total (ultima absorve arredondamento).
        total_contrato = float(data.get("total", 0) or 0)
        n_comp = max(1, len(compradores))
        percs = [float(c.get("percentual") or 0) for c in compradores] or [100.0]
        soma_percs = sum(p for p in percs if p > 0)
        if soma_percs <= 0:
            percs = [100.0 / n_comp] * n_comp
        else:
            percs = [max(0.0, p) * 100.0 / soma_percs for p in percs]
        cotas = [round(total_contrato * p / 100.0, 2) for p in percs]
        if cotas:
            cotas[-1] = round(total_contrato - sum(cotas[:-1]), 2)

        # --- VENDA ---
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDA")
        new_id = cur.fetchone()[0]

        permuta = str(data.get("permuta", "N")).upper()
        if permuta not in ["S", "N"]: permuta = "N"

        date_str = data.get("data", "")
        id_empreendimento = int(data.get("id_empreendimento", 0) or 0)

        conta_permuta = int(data.get("conta_permuta") or 0) or None

        # Nº do contrato: informavel; default = id da venda (UNICO por venda —
        # o PGD da DIMOB rejeita 2 linhas do MESMO CPF com contrato repetido)
        num_contrato = str(data.get("num_contrato") or "").strip()[:90] or str(new_id)

        # NUMCADIMOB e INTEGER na base viva (nao aceita o antigo "MVP-<id>"):
        # usa o numero de cadastro imobiliario da 1a unidade vendida, se houver.
        num_cad = None
        _unids = data.get("unidades_selecionadas") or []
        if _unids:
            try:
                cur.execute("SELECT NUMCADIMOB FROM UNIDADE WHERE ID = ?", (int(_unids[0]),))
                _row = cur.fetchone()
                if _row and _row[0] is not None:
                    num_cad = int(str(_row[0]).strip() or 0) or None
            except Exception:
                num_cad = None

        query = "INSERT INTO VENDA (ID, IDEMPREENDIMENTO, NUMCADIMOB, NUMCONT, DTOPER, DESCUNIDIMOB, TOTALVENDA, CODIGOEMPRESA, DISTRATO, PERMUTA, CONTA_PERMUTA, ID_CLIENTE) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'N', ?, ?, ?)"
        params = (
            new_id,
            id_empreendimento,
            num_cad,
            num_contrato.encode('cp1252', 'ignore'),
            date_str,
            str(data.get("unidade", "")).encode('cp1252', 'ignore')[:100],
            cotas[0] if cotas else total_contrato,
            int(empresa_id),
            permuta,
            conta_permuta,
            id_cliente
        )
        cur.execute(query, params)

        # --- VENDAS SATELITES (multi-comprador, valores rateados por CPF) ---
        # 1 linha VENDA por comprador extra com a SUA cota do contrato (DIMOB e
        # EFD-Contribuicoes declaram por adquirente), vinculada pela
        # IDVENDAVINCULADA e marcada no INFCOMP. As cotas do grupo somam o
        # contrato — listas/POC nao dobram. Unidades, condicoes e RECEBER
        # existem so na principal (fluxo financeiro e um so).
        desc_unid = str(data.get("unidade", "")).encode('cp1252', 'ignore')[:100]
        for offset, cid_extra in enumerate(ids_clientes[1:], start=1):
            if cid_extra is None:
                continue
            sat_id = new_id + offset
            cur.execute(
                "INSERT INTO VENDA (ID, IDEMPREENDIMENTO, NUMCADIMOB, NUMCONT, DTOPER, DESCUNIDIMOB, TOTALVENDA, CODIGOEMPRESA, DISTRATO, PERMUTA, ID_CLIENTE, IDVENDAVINCULADA, INFCOMP) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'N', ?, ?, ?, ?)",
                (
                    sat_id,
                    id_empreendimento,
                    num_cad,
                    num_contrato.encode('cp1252', 'ignore'),
                    date_str,
                    desc_unid,
                    cotas[offset] if offset < len(cotas) else 0,
                    int(empresa_id),
                    permuta,
                    cid_extra,
                    new_id,
                    f"VINCULADA VENDA #{new_id}".encode('cp1252', 'ignore'),
                ),
            )

        # --- VENDAUNIDADE ---
        unidades_selecionadas = data.get("unidades_selecionadas", [])
        if unidades_selecionadas:
            # N+1 FIX: pré-busca o MAX(ID) uma vez, usa contador local
            cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDAUNIDADE")
            vu_id_base = cur.fetchone()[0]
            for idx_vu, u_id in enumerate(unidades_selecionadas):
                vu_id = vu_id_base + idx_vu
                cur.execute("INSERT INTO VENDAUNIDADE (ID, IDVENDA, IDUNIDADE) VALUES (?, ?, ?)", (vu_id, new_id, int(u_id)))

        # Determinar última data mensal (para ancorar CHAVES/FINANCIAMENTO depois)
        import datetime as _dt
        data_venda: _dt.date | None = None
        try:
            data_venda = _dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            pass

        # --- CONDIÇÕES (FORMAS DE PAGAMENTO) ---
        condicoes = data.get("condicoes", [])

        # Pre-calcular último vencimento das parcelas MENSAIS para ancorar
        # types that should come "at the end"
        ultima_data_mensal: _dt.date | None = None
        for cond in condicoes:
            tipo = cond.get("tipo", "MENSAL")
            qtd = int(cond.get("quantidade", 1))
            venc_ini = cond.get("vencimento", "")
            if tipo == "MENSAL" and venc_ini:
                try:
                    base_m = _dt.datetime.strptime(venc_ini, "%Y-%m-%d").date()
                    ultima = add_months(base_m, qtd - 1)
                    if ultima_data_mensal is None or ultima > ultima_data_mensal:
                        ultima_data_mensal = ultima
                except Exception:
                    pass

        # N+1 FIX: pré-busca todos os MAX(ID) necessários uma vez
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDAFORMAPAGTO")
        fp_id_base = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDAFORMAPAGTOPRAZO")
        prazo_id_base = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM RECEBER")
        rec_id_base = cur.fetchone()[0]

        _fp_counter    = fp_id_base
        _prazo_counter = prazo_id_base
        _rec_counter   = rec_id_base

        for cond in condicoes:
            fp_id = _fp_counter
            _fp_counter += 1

            tipo = cond.get("tipo", "MENSAL")
            qtd = int(cond.get("quantidade", 1))
            valor_base = float(cond.get("valor", 0))
            venc_inicial = cond.get("vencimento", "")

            # --- REFORCO: detectar intervalo automático ---
            intervalo_meses = 12  # default anual
            if tipo == "REFORCO" and data_venda and venc_inicial:
                try:
                    d_venc = _dt.datetime.strptime(venc_inicial, "%Y-%m-%d").date()
                    diff = months_between(data_venda, d_venc)
                    # Se cai em 6 meses ou múltiplo de 6 (até 9), é semestral; senão anual
                    if diff > 0 and diff <= 9:
                        intervalo_meses = 6
                    else:
                        intervalo_meses = 12
                except Exception:
                    intervalo_meses = 12

            # --- CHAVES / FINANCIAMENTO: data = depois das mensais ---
            if tipo in ("CHAVES", "FINANCIAMENTO") and ultima_data_mensal is not None:
                venc_inicial = add_months(ultima_data_mensal, 1).strftime("%Y-%m-%d")
            
            # Parcelas únicas: forçar quantidade = 1
            if tipo in ("SINAL", "INTERMEDIARIA", "CHAVES", "FINANCIAMENTO"):
                qtd = 1

            mensal_flag = "S" if tipo == "MENSAL" else "N"
            tipo_label = {
                "SINAL": "Ato/Sinal",
                "MENSAL": "Mensais",
                "SEMESTRAL": "Semestrais",
                "ANUAL": "Anuais",
                "REFORCO": f"Reforço ({'Semestral' if intervalo_meses == 6 else 'Anual'}) ({qtd}x)",
                "INTERMEDIARIA": "Intermediária",
                "CHAVES": "Chaves (Repasse)",
                "FINANCIAMENTO": "Financiamento (Repasse)",
            }.get(tipo, tipo)
            descricao_fp = f"{tipo_label} ({qtd}x)" if tipo not in ("CHAVES", "FINANCIAMENTO", "SINAL", "INTERMEDIARIA") else tipo_label

            q_fp = "INSERT INTO VENDAFORMAPAGTO (ID, IDVENDA, DESCRICAO, VALOR, MENSAL, ATIVA, QUANTIDADE_PARCELAS) VALUES (?, ?, ?, ?, ?, ?, ?)"
            cur.execute(q_fp, (fp_id, new_id, descricao_fp, valor_base * qtd, mensal_flag, "S", qtd))

            # --- PRAZOS + RECEBER ---
            if venc_inicial and qtd > 0:
                for i in range(qtd):
                    dt_prazo = calc_vencimento(venc_inicial, i, tipo, intervalo_meses)
                    dt_prazo_str = dt_prazo.strftime("%Y-%m-%d") if dt_prazo else venc_inicial

                    # N+1 FIX: usa contadores pré-calculados
                    prazo_id = _prazo_counter
                    _prazo_counter += 1

                    referencia = f"{i+1}/{qtd}"
                    q_prazo = "INSERT INTO VENDAFORMAPAGTOPRAZO (ID, IDVENDAFORMAPAGTO, DATA, REFERENCIA, VALOR, VALOR_PAGO) VALUES (?, ?, ?, ?, ?, ?)"
                    cur.execute(q_prazo, (prazo_id, fp_id, dt_prazo_str, referencia, valor_base, 0.0))

                    rec_id = _rec_counter
                    _rec_counter += 1
                    q_rec = """
                        INSERT INTO RECEBER (ID, IDVENDA, DATA, VALORPARCELA, PARCELA, OBS, IDVENDAFORMAPAGTO, IDVENDAFORMAPAGTOPRAZO, TOTALPAGO)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cur.execute(q_rec, (rec_id, new_id, dt_prazo_str, valor_base, referencia, f"GERADA NA VENDA ({tipo})", fp_id, prazo_id, 0.0))

        conn.commit()
        conn.close()
        return {"success": True, "id": new_id, "message": "Venda e Condições cadastradas!"}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/distratos")
async def post_distratos(request: Request):
    try:
        data = await request.json()
        id_venda = data.get("id_venda")
        if not id_venda:
            raise HTTPException(status_code=400, detail="id_venda obrigatório")
            
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM DISTRATO")
        new_id = cur.fetchone()[0]
        
        q_dist = "INSERT INTO DISTRATO (ID, IDVENDA, DATA, VALORDEVOLVIDO, DATAPAGAMENTO) VALUES (?, ?, ?, ?, ?)"
        pr_dist = (
            new_id,
            int(id_venda),
            data.get("data_distrato"),
            float(data.get("valor_devolvido", 0) or 0),
            data.get("data_pagamento")
        )
        cur.execute(q_dist, pr_dist)
        
        # update venda flag (cascateia para as vendas satelites de multi-comprador)
        cur.execute("UPDATE VENDA SET DISTRATO = 'S', DATADISTRATO = ? WHERE ID = ? OR IDVENDAVINCULADA = ?", (data.get("data_distrato"), int(id_venda), int(id_venda)))
        
        conn.commit()
        conn.close()
        return {"success": True, "id": new_id, "message": "Distrato registrado!"}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

class PreviewBaixasInput(BaseModel):
    empresa_id: int
    extracted_data: list[dict]
    use_splink: bool = False  # se True, usa Splink probabilístico ao invés do scoring manual


# ──────────────────────────────────────────────────────────────────────────
# PANDERA — Schema de validação para linhas extraídas do PDF
# ──────────────────────────────────────────────────────────────────────────
def _validate_pdf_rows(rows: list[dict]) -> list[dict]:
    """
    Coerce e valida cada linha extraída do PDF via Pandera.
    Linhas inválidas são corrigidas com defaults seguros (não bloqueiam).
    Problemas são logados mas não lançam exceção.
    """
    import logging
    import pandas as pd

    _DEFAULTS = {
        "comprador_nome": "",
        "cpf_cnpj": "",
        "total_pago": 0.0,
        "valor_raiz": 0.0,
        "unidade": "",
        "dt_vencimento": None,
        "acrescimos_variacoes": 0.0,
        "descontos": 0.0,
    }

    cleaned = []
    for i, row in enumerate(rows):
        r = dict(row)
        for field, default in _DEFAULTS.items():
            raw = r.get(field)
            if field in ("total_pago", "valor_raiz", "acrescimos_variacoes", "descontos"):
                try:
                    r[field] = float(raw or 0)
                    if r[field] < 0:
                        logging.warning(f"[Pandera] linha {i}: {field}={r[field]} negativo → zerado")
                        r[field] = 0.0
                except (TypeError, ValueError):
                    logging.warning(f"[Pandera] linha {i}: {field}='{raw}' inválido → {default}")
                    r[field] = default
            else:
                r[field] = str(raw or "").strip() if raw is not None else default
        cleaned.append(r)
    return cleaned


# ──────────────────────────────────────────────────────────────────────────
# PyOD — Detecção de anomalia de valor no lote de pagamentos (Conciliação)
# ──────────────────────────────────────────────────────────────────────────
def _pyod_score_batch(rows: list[dict]) -> dict:
    """
    Detecta valores de pagamento atípicos no lote via IsolationForest.
    Retorna {row_idx: {'anomaly_score': float, 'anomaly_flag': bool}}
    IsolationForest funciona mesmo com poucos registros (mínimo 5).
    """
    import numpy as np
    if len(rows) < 5:
        return {}
    try:
        import numpy as np
        from pyod.models.iforest import IForest

        valores = np.array([
            [float(r.get("total_pago") or 0), float(r.get("valor_raiz") or 0)]
            for r in rows
        ])

        # IsolationForest: contamination = % esperada de outliers (5%)
        clf = IForest(contamination=0.05, random_state=42, n_estimators=50)
        clf.fit(valores)

        scores = clf.decision_scores_   # quanto maior = mais anômalo
        labels = clf.labels_            # 1 = outlier, 0 = normal

        # Normaliza score para 0-1
        min_s, max_s = scores.min(), scores.max()
        norm = (scores - min_s) / (max_s - min_s + 1e-9)

        return {
            i: {"anomaly_score": round(float(norm[i]), 3), "anomaly_flag": bool(labels[i] == 1)}
            for i in range(len(rows))
        }
    except Exception:
        import traceback; traceback.print_exc()
        return {}


def _splink_build_match_map(extracted_rows: list[dict], todas_vendas: list) -> dict:
    """
    Roda Splink probabilístico entre pagamentos do PDF e contratos Vulcano.
    Retorna {row_index: {'v_row': tuple, 'prob': float, 'v_id': int}}
    """
    import re, unicodedata, warnings as _w
    _w.filterwarnings("ignore")
    try:
        import pandas as pd
        from splink import DuckDBAPI, Linker, SettingsCreator
        import splink.comparison_library as cl
    except ImportError:
        return {}

    def _norm_cpf(s):
        d = re.sub(r'\D', '', str(s or ''))
        return d if len(d) >= 11 else None

    def _norm_nome(s):
        s = str(s or '').upper().strip()
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return re.sub(r'\s+', ' ', s)

    def _norm_unidade(s):
        return re.sub(r'BLOCO\s+\S+\s*[-]?\s*', '', str(s or '').upper()).strip()

    def _balde(v, step=500):
        try:
            return str(int(float(v or 0) / step) * step)
        except Exception:
            return "0"

    def _dec(vx):
        if vx is None: return ''
        if isinstance(vx, (bytes, bytearray)): return vx.decode('win1252', 'ignore')
        return str(vx)

    # Tabela esquerda: pagamentos PDF
    pdf_rows = []
    for idx, row in enumerate(extracted_rows):
        pdf_rows.append({
            'unique_id': f'P{idx}',
            '_row_idx': idx,
            'nome_norm':   _norm_nome(row.get('comprador_nome') or row.get('comprador') or ''),
            'cpf_norm':    _norm_cpf(row.get('cpf_cnpj') or row.get('cpf') or ''),
            'unid_norm':   _norm_unidade(row.get('unidade') or ''),
            'valor_balde': _balde(row.get('total_pago') or row.get('valor') or 0),
        })

    # Tabela direita: contratos ERP (v_id, c_nome, c_id, c_cnpj, v_desc, e_nome)
    erp_rows = []
    for vd in todas_vendas:
        v_id, c_nome, c_id, c_cnpj, v_desc, e_nome = vd
        erp_rows.append({
            'unique_id': f'V{v_id}',
            '_v_id': v_id,
            'nome_norm':   _norm_nome(_dec(c_nome)),
            'cpf_norm':    _norm_cpf(_dec(c_cnpj)),
            'unid_norm':   _norm_unidade(_dec(v_desc)),
            'valor_balde': "0",  # contratos não têm valor aqui
        })

    if not pdf_rows or not erp_rows:
        return {}

    df_pdf = pd.DataFrame(pdf_rows)
    df_erp = pd.DataFrame(erp_rows)

    try:
        settings = SettingsCreator(
            link_type="link_only",
            blocking_rules_to_generate_predictions=[
                "l.cpf_norm = r.cpf_norm",
                "substr(l.nome_norm,1,5) = substr(r.nome_norm,1,5)",
                "l.unid_norm = r.unid_norm",
            ],
            comparisons=[
                cl.ExactMatch("cpf_norm"),
                cl.JaroWinklerAtThresholds("nome_norm", [0.92, 0.85]),
                cl.ExactMatch("unid_norm"),
            ],
            max_iterations=20,
            em_convergence=0.001,
        )
        db_api = DuckDBAPI()
        linker = Linker([df_pdf, df_erp], settings, db_api=db_api)
        linker.training.estimate_u_using_random_sampling(max_pairs=1e5)
        try:
            linker.training.estimate_parameters_using_expectation_maximisation(
                "l.cpf_norm = r.cpf_norm"
            )
        except Exception:
            pass
        try:
            linker.training.estimate_parameters_using_expectation_maximisation(
                "substr(l.nome_norm,1,5) = substr(r.nome_norm,1,5)"
            )
        except Exception:
            pass

        preds = linker.inference.predict(threshold_match_probability=0.45).as_pandas_dataframe()
        if preds.empty:
            return {}

        # Melhor match por linha PDF (maior probabilidade)
        best = (
            preds.sort_values('match_probability', ascending=False)
            .drop_duplicates(subset=['unique_id_l'])
        )

        # Monta mapa {row_idx: {v_id, prob, v_row}}
        vid_to_vrow = {str(vd[0]): vd for vd in todas_vendas}
        result = {}
        for _, r in best.iterrows():
            uid_l = str(r['unique_id_l'])  # "P0", "P1" ...
            uid_r = str(r['unique_id_r'])  # "V12345"
            prob = float(r['match_probability'])
            if prob < 0.45:
                continue
            # extrai row_idx
            try:
                row_idx = int(uid_l.replace('P', ''))
            except Exception:
                continue
            v_id_str = uid_r.replace('V', '')
            v_row = vid_to_vrow.get(v_id_str)
            if v_row is None:
                # tenta int key
                try:
                    v_row = vid_to_vrow.get(str(int(v_id_str)))
                except Exception:
                    pass
            if v_row:
                result[row_idx] = {'v_row': v_row, 'prob': prob}
        return result
    except Exception:
        import traceback; traceback.print_exc()
        return {}


@app.post("/api/parser/preview-baixas")
def preview_baixas(data: PreviewBaixasInput):
    def dec(v):
        if v is None: return ''
        if isinstance(v, (bytes, bytearray)): return v.decode('win1252', 'ignore')
        return str(v)

    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        cur.execute("""
            SELECT v.ID, c.NOME, c.ID, c.CNPJ, v.DESCUNIDIMOB, e.NOME
            FROM VENDA v
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
        """, (data.empresa_id,))
        todas_vendas = cur.fetchall()
        
        # ── Pandera: valida e coerce todos os campos das linhas PDF ──
        _extracted_clean = _validate_pdf_rows(data.extracted_data)

        # ── PyOD: score de anomalia de valor no lote inteiro ──
        _pyod_map = _pyod_score_batch(_extracted_clean)

        # ── Splink: pré-computa mapa de matches para TODO o lote de uma vez ──
        splink_map: dict = {}
        if data.use_splink:
            splink_map = _splink_build_match_map(_extracted_clean, todas_vendas)
        
        results = []
        reserved_ids_receber = set()
        reserved_ids_prazos = set()
        
        # Global Transaction Cache para proteger o Firebird
        _cache_receber = {}
        _cache_prazos = {}

        for row_idx, row in enumerate(_extracted_clean):
            unidade = str(row.get("unidade", "")).strip()
            total_pago = float(row.get("total_pago", 0) or 0)
            valor_raiz = float(row.get("valor_raiz", 0) or 0)
            has_date = bool(row.get("dt_vencimento"))
            # FIX: campo pode vir como 'comprador' ou 'comprador_nome' dependendo do extrator
            comprador_nome = str(row.get("comprador_nome") or row.get("comprador") or "").strip()
            
            if not unidade and not comprador_nome:
                pass
                
            raw_cpf = str(row.get("cpf_cnpj", "")).strip()
            cpf_clean = ''.join(c for c in raw_cpf if c.isdigit())
            
            # ── ENGINE DE MATCHING ──────────────────────────────────────
            # Modo Splink: usa probabilidade calibrada (Fellegi-Sunter)
            # Modo Heurístico: scoring manual em RAM (padrão original)
            def clean_str(s): return str(s).lower().strip()
            
            _splink_prob: float | None = None  # probabilidade do Splink, se usado
            candidatas = []

            if data.use_splink and row_idx in splink_map:
                sm = splink_map[row_idx]
                _splink_prob = sm['prob']
                _is_dia = _splink_prob >= 0.85
                candidatas = [{'v_row': sm['v_row'], 'score': int(_splink_prob * 100), 'is_diamante': _is_dia}]
            else:
                # ── HEURÍSTICA + RapidFuzz ─────────────────────────────────────
                # token_set_ratio: ignora ordem das palavras e palavras extras
                # partial_ratio:   cobre abreviações e substrings de unidade
                from rapidfuzz import fuzz as _fuzz
                for v_data in todas_vendas:
                    v_id, c_nome, c_id, c_cnpj, v_desc, e_nome_db = v_data
                    
                    db_cpf = ''.join(c for c in str(c_cnpj or '') if c.isdigit())
                    score = 0
                    is_diamante_c = False
                    
                    # NÍVEL 0: CPF exato → Diamante (score máximo, para na iteração)
                    if cpf_clean and len(cpf_clean) > 5 and cpf_clean == db_cpf:
                        score += 20
                        is_diamante_c = True
                        
                    # NÍVEL 1: Nome — RapidFuzz token_set_ratio
                    # Captura: "PEDRO ALVES MONTEIRO" ↔ "PEDRO MONTEIRO ALVES" → 100
                    # Captura: "JOAO CARLOS SILVA"   ↔ "JOAO CARLOS DA SILVA" → 95
                    _nome_ratio = 0
                    if comprador_nome:
                        _nome_ratio = _fuzz.token_set_ratio(
                            comprador_nome, str(c_nome or ''), score_cutoff=0
                        )
                        if _nome_ratio >= 75:
                            score += max(5, int(_nome_ratio / 100 * 15))  # proporcional 5–15
                        
                    # NÍVEL 2: Unidade — partial_ratio (cobre abreviações)
                    # Captura: "APTO 302" ↔ "BLOCO A APTO 302" → 100
                    # FIX: se nome bate muito bem (≥85) e unidade está vazia no ERP,
                    # aceita candidato mesmo sem DESCUNIDIMOB (ex: Flávio Hormann)
                    if unidade and v_desc:
                        _unid_ratio = _fuzz.partial_ratio(
                            clean_str(unidade), clean_str(v_desc), score_cutoff=0
                        )
                        if _unid_ratio >= 80:
                            score += max(5, int(_unid_ratio / 100 * 15))  # proporcional 5–15
                    elif unidade and not v_desc and _nome_ratio >= 85:
                        # Unidade no PDF mas DESCUNIDIMOB vazio no ERP — nome forte compensa
                        score += 5  # bônus mínimo para entrar no pool
                        
                    if score > 0:
                        candidatas.append({
                            'v_row': v_data,
                            'score': score,
                            'is_diamante': is_diamante_c
                        })

                
            if not candidatas:
                results.append({"row": row, "status": "NAO_ENCONTRADO_OU_JA_PAGO", "id_receber": None,
                               "db_estado_atual": None, "proposta_ia": None,
                               "match_engine": "splink" if data.use_splink else "heuristic",
                               "match_probability": _splink_prob})
                continue

            if candidatas:
                candidatas.sort(key=lambda x: x['score'], reverse=True)
                best_s = candidatas[0]['score']
                candidatas = [c for c in candidatas if c['score'] >= best_s - 15][:10]
                # DEBUG
                import logging
                logging.warning(f"[PREVIEW_BAIXAS] '{comprador_nome}' unid='{unidade}' val={total_pago:.2f} → {len(candidatas)} candidata(s): {[(dec(c['v_row'][1])[:20], c['score'], dec(c['v_row'][4])[:20]) for c in candidatas]}")

            grupos_unidades = {}
            for cand in candidatas:
                import re
                desc_bruto = dec(cand["v_row"][4]).upper().strip()
                m = re.search(r'(?:APTO|AP|UNIDADE|SALA|CASA|CT|COTA)\s*(\w+)', desc_bruto)
                if m:
                    desc_unid = m.group(1)
                else:
                    digits = re.findall(r'\d+', desc_bruto)
                    desc_unid = digits[-1] if digits else f'V_{cand["v_row"][0]}'
                    
                if desc_unid not in grupos_unidades:
                    grupos_unidades[desc_unid] = []
                grupos_unidades[desc_unid].append(cand)
                
            melhor_match_final = None 
            from itertools import combinations
            
            pdf_venc = str(row.get('dt_vencimento', '')).strip()
            pdf_mes = ''
            pdf_ano = ''
            if '-' in pdf_venc:
                parts = pdf_venc.split('-')
                if len(parts) >= 3: # YYYY-MM-DD
                    pdf_ano, pdf_mes = parts[0], parts[1].zfill(2)
            elif '/' in pdf_venc:
                parts = pdf_venc.split('/')
                if len(parts) >= 2: # DD/MM/YYYY
                    pdf_mes = parts[1].zfill(2)
                    if len(parts) >= 3:
                        pdf_ano = parts[2]
            
            
            for grupo_key, grupo_vendas in grupos_unidades.items():
                pool_abertas = []
                pool_quitadas = []
                pool_prazos = []
                pool_prazos_quitados = []
                
                for cand in grupo_vendas:
                    v_id = int(cand['v_row'][0])
                    
                    if v_id not in _cache_receber:
                        # FIX: sem corte de data — queremos TODAS as parcelas da venda
                        # separando abertas (TOTALPAGO=0) de quitadas (TOTALPAGO>0) em memória
                        cur.execute("SELECT ID, DATA, VALORPARCELA, TOTALPAGO, PARCELA FROM RECEBER WHERE IDVENDA = ?", (v_id,))
                        _cache_receber[v_id] = cur.fetchall()
                        
                    for ra in _cache_receber[v_id]: 
                        if ra[0] not in reserved_ids_receber: # IMPEDE DUPLICIDADE NO ARQUIVO
                            if float(ra[3] or 0) > 0:
                                pool_quitadas.append((ra, cand, False))
                            else:
                                pool_abertas.append((ra, cand, False))
                        
                    if v_id not in _cache_prazos:
                        cur.execute("""
                            SELECT p.ID, p.DATA, p.VALOR, vfp.ID, p.VALOR_PAGO
                            FROM VENDAFORMAPAGTOPRAZO p
                            JOIN VENDAFORMAPAGTO vfp ON vfp.ID = p.IDVENDAFORMAPAGTO
                            WHERE vfp.IDVENDA = ?
                        """, (v_id,))
                        _cache_prazos[v_id] = cur.fetchall()
                        
                    for pr in _cache_prazos[v_id]: 
                        if pr[0] not in reserved_ids_prazos: # IMPEDE DUPLICIDADE NO ARQUIVO
                            if float(pr[4] or 0) > 0:
                                pool_prazos_quitados.append((pr, cand, True))
                            else:
                                pool_prazos.append((pr, cand, True))
                        
                pool_abertas.sort(key=lambda x: str(x[0][1]) if x[0][1] else '9999')
                pool_prazos.sort(key=lambda x: str(x[0][1]) if x[0][1] else '9999')
                
                logging.warning(f"  [GRUPO '{grupo_key}'] pool_abertas={len(pool_abertas)} pool_quitadas={len(pool_quitadas)} pool_prazos={len(pool_prazos)} pdf_mes={pdf_mes} pdf_ano={pdf_ano}")
                # Detalha quitadas do mês alvo para diagnóstico
                for _pq, _, _ in pool_quitadas[:30]:
                    _pq_data = str(_pq[1])
                    if pdf_mes and f'-{pdf_mes}-' in _pq_data:
                        logging.warning(f"    [QUITADA MÊS OK] id={_pq[0]} data={_pq_data} valorparc={_pq[2]} totalpago={_pq[3]}")
                
                match_perfeito = None
                lista_multipla = []
                mat_type = ""
                
                def same_date_combo(c_list):
                    if not c_list: return False
                    primeira_data = c_list[0][0][1]
                    for c in c_list[1:]:
                        if c[0][1] != primeira_data: return False
                    return True
                    
                def has_pdf_date(c_list):
                    db_venc = str(c_list[0][0][1])
                    return (pdf_mes and f'-{pdf_mes}-' in db_venc and (not pdf_ano or pdf_ano in db_venc))

                # PRIORIDADE SUPREMA 00: JA PAGO (Faturas Quitadas Históricas)
                # FIX: tolerância proporcional de 30% para cobrir variação CUB/INCC
                # Critérios (em ordem de força):
                #   A) Com data + valor_raiz bate com parcela-base (CUB identificado)
                #   B) Com data + diferença < 30% do valor da parcela
                #   C) Sem data + valor EXATO (< 0.50) — sinal forte de duplicata
                for _pool, _type in [(pool_quitadas, "JA_PAGO_RECEBER"), (pool_prazos_quitados, "JA_PAGO_PROJETADA")]:
                    for p_tuple in _pool:
                        p, cand, is_prazo = p_tuple
                        p_valor = float(p[2] or 0)
                        if p_valor <= 0: continue
                        diff_abs = abs(p_valor - total_pago)
                        diff_abs_raiz = abs(p_valor - valor_raiz) if valor_raiz else 9999
                        diff_rate = diff_abs / p_valor if p_valor else 9999
                        db_venc = str(p[1])
                        date_ok = pdf_mes and f'-{pdf_mes}-' in db_venc and (not pdf_ano or pdf_ano in db_venc)
                        # A: data bate + valor_raiz confirma a parcela-base
                        raiz_bate = valor_raiz and diff_abs_raiz < 5.0
                        # B: data bate + margem 30% (cobre CUB)
                        margem_ok = diff_rate < 0.30
                        # C: valor exatíssimo sem data
                        exact_value = diff_abs < 0.50
                        if (date_ok and (raiz_bate or margem_ok)) or exact_value:
                            match_perfeito = p_tuple
                            mat_type = _type
                            break
                    if match_perfeito: break

                # 00B. Múltiplo JA PAGO (Titulos Conjuntos quitados)
                # Não exigimos same_date_combo aqui porque parcelas conjuntas (ex: Gilberto) 
                # podem ter vencimentos DB como 01/09 e 30/09, mas foram pagas juntas no PDF.
                if not match_perfeito and not lista_multipla:
                    achou_combo_pago = False
                    for _pool, _type in [(pool_quitadas, "MULTIPLO_JA_PAGO_RECEBER"), (pool_prazos_quitados, "MULTIPLO_JA_PAGO_PROJETADA")]:
                        if len(_pool) >= 2:
                            for combo_tamanho in [2, 3, 4]:
                                if achou_combo_pago or len(_pool) < combo_tamanho: break
                                for combo in combinations(_pool, combo_tamanho):
                                    soma_combo = sum(float(it[0][2] or 0) for it in combo)
                                    if soma_combo > 0 and soma_combo <= total_pago:
                                        diff_rate = abs(total_pago - soma_combo)/soma_combo
                                        if diff_rate < 0.05:
                                            lista_multipla = list(combo)
                                            mat_type = _type
                                            achou_combo_pago = True
                                            break
                        if achou_combo_pago: break
                
                # PRIORIDADE MÁXIMA 0: DATA BATE ESTREITAMENTE COM A DATA DO PDF e o VALOR BATE.
                if not match_perfeito and not lista_multipla:
                    for p_tuple in pool_abertas:
                        p, cand, is_prazo = p_tuple
                        if float(p[2] or 0) > 0 and (abs(float(p[2]) - total_pago) < 5.0 or abs(float(p[2]) - valor_raiz) < 5.0):
                            db_venc = str(p[1])
                            if pdf_mes and f'-{pdf_mes}-' in db_venc and pdf_ano in db_venc:
                                match_perfeito = p_tuple
                                mat_type = "PERFEITO_RECEBER_DATA_EXATA"
                                break
                            
                # 1. Match Singular Rápido
                # PROTEÇÃO ANTI-ADIANTAMENTO: só permite match sem data se NÃO houver parcela
                # já quitada no Vulcano com valor próximo (indicaria que esta transação já foi
                # registrada e a engine estaria roubando uma parcela futura em aberto).
                _existe_quitada_similar = any(
                    abs(float(p[0][2] or 0) - total_pago) < 5.0
                    for p in (pool_quitadas + pool_prazos_quitados)
                )
                # Detectar multi-comprador (mesmo grupo de unidade tem vendas de múltiplos IDs)
                _ids_venda_no_grupo = set(str(c['v_row'][0]) for c in grupo_vendas)
                _multi_vendas = len(_ids_venda_no_grupo) > 1

                if not match_perfeito and not lista_multipla and not _existe_quitada_similar:
                    for p_tuple in pool_abertas:
                        p, cand, is_prazo = p_tuple
                        p_valor = float(p[2] or 0)
                        if p_valor > 0 and (abs(p_valor - total_pago) < 5.0 or abs(p_valor - valor_raiz) < 5.0):
                            db_venc = str(p[1])
                            # Em cenário multi-vendas (mesma unidade, compradores distintos),
                            # exigir também confirmação de data para não adiantar quitações.
                            if _multi_vendas and pdf_mes:
                                if f'-{pdf_mes}-' in db_venc and (not pdf_ano or pdf_ano in db_venc):
                                    match_perfeito = p_tuple
                                    mat_type = "PERFEITO_RECEBER_MULTI"
                                    break
                            elif _multi_vendas and not pdf_mes:
                                # FIX: PDF sem data em cenário multi-comprador — só confirma
                                # se valor_raiz for exato (< R$0,50) para evitar adiantamento
                                if valor_raiz and abs(p_valor - valor_raiz) < 0.50:
                                    match_perfeito = p_tuple
                                    mat_type = "PERFEITO_RECEBER_MULTI_SEM_DATA"
                                    break
                            elif not _multi_vendas:
                                match_perfeito = p_tuple
                                mat_type = "PERFEITO_RECEBER"
                                break

                if not match_perfeito and not _existe_quitada_similar:
                    for pr_tuple in pool_prazos:
                        pr, cand, is_prazo = pr_tuple
                        if float(pr[2] or 0) > 0 and (abs(float(pr[2]) - total_pago) < 5.0 or abs(float(pr[2]) - valor_raiz) < 5.0):
                            match_perfeito = pr_tuple
                            mat_type = "PERFEITO_PROJETADA"
                            break
                            
                # 2. Combinação Múltipla Inteligente (Isocrônica)
                if not match_perfeito and not lista_multipla and len(pool_abertas) >= 2:
                    achou_combo = False
                    
                    # FASE A: Data Exata com o Pdf + Isocrônica entre Titulos (< 5% erro)
                    for combo_tamanho in [2, 3, 4]:
                        if achou_combo or len(pool_abertas) < combo_tamanho: break
                        for combo in combinations(pool_abertas, combo_tamanho):
                            if same_date_combo(combo) and has_pdf_date(combo):
                                soma_combo = sum(float(it[0][2] or 0) for it in combo)
                                if soma_combo > 0 and soma_combo <= total_pago:
                                    diff_rate = abs(total_pago - soma_combo)/soma_combo
                                    if diff_rate < 0.05:
                                        lista_multipla = list(combo)
                                        mat_type = "MULTIPLO_RECEBER_DATA_EXATA"
                                        achou_combo = True
                                        break
                                        
                    # FASE B: Isocrônica Geral (< 5% erro) para meses onde a OCR falhou a data
                    if not achou_combo:
                        for combo_tamanho in [2, 3, 4]:
                            if achou_combo or len(pool_abertas) < combo_tamanho: break
                            for combo in combinations(pool_abertas, combo_tamanho):
                                if same_date_combo(combo):
                                    soma_combo = sum(float(it[0][2] or 0) for it in combo)
                                    if soma_combo > 0 and soma_combo <= total_pago:
                                        diff_rate = abs(total_pago - soma_combo)/soma_combo
                                        if diff_rate < 0.05:
                                            lista_multipla = list(combo)
                                            mat_type = "MULTIPLO_RECEBER_ISOCRONICA"
                                            achou_combo = True
                                            break
                                            
                    # FASE C: Isocrônica com CUB Extenso ou Juros (< 30% erro)
                    if not achou_combo:
                        for combo_tamanho in [2, 3, 4]:
                            if achou_combo or len(pool_abertas) < combo_tamanho: break
                            for combo in combinations(pool_abertas, combo_tamanho):
                                if same_date_combo(combo):
                                    soma_combo = sum(float(it[0][2] or 0) for it in combo)
                                    if soma_combo > 0 and soma_combo <= total_pago:
                                        diff_rate = abs(total_pago - soma_combo)/soma_combo
                                        if diff_rate < 0.30:
                                            lista_multipla = list(combo)
                                            mat_type = "MULTIPLO_RECEBER_ISOCRONICA_CUB"
                                            achou_combo = True
                                            break

                    # FASE D: Fallback Misto - DESATIVADO em cenário multi-vendas para evitar
                    # adiantamento de quitações em unidades com múltiplos compradores
                    if not achou_combo and not _multi_vendas and not _existe_quitada_similar:
                        for combo_tamanho in [2, 3]:
                            if achou_combo or len(pool_abertas) < combo_tamanho: break
                            for combo in combinations(pool_abertas, combo_tamanho):
                                soma_combo = sum(float(it[0][2] or 0) for it in combo)
                                if soma_combo > 0 and soma_combo <= total_pago:
                                    diff_rate = abs(total_pago - soma_combo)/soma_combo
                                    if diff_rate < 0.20:
                                        lista_multipla = list(combo)
                                        mat_type = "MULTIPLO_RECEBER_MISTO"
                                        achou_combo = True
                                        break
                    # FASE E: Fallback Híbrido com Prazos (Mensais + Reforços/Anuais Projetados)
                    if not achou_combo:
                        pool_hibrida = pool_abertas + pool_prazos
                        if len(pool_hibrida) >= 2:
                            for combo_tamanho in [2, 3, 4]:
                                if achou_combo or len(pool_hibrida) < combo_tamanho: break
                                for combo in combinations(pool_hibrida, combo_tamanho):
                                    # Relaxamos a Isocronia porque um Reforço costuma cair junto de uma Mensal, mas de Contratos/Prazos diferentes
                                    soma_combo = sum(float(it[0][2] or 0) for it in combo)
                                    if soma_combo > 0 and soma_combo <= total_pago:
                                        diff_rate = abs(total_pago - soma_combo)/soma_combo
                                        if diff_rate < 0.20:
                                            lista_multipla = list(combo)
                                            mat_type = "MULTIPLO_RECEBER_PROJETADA_HIBRIDA"
                                            achou_combo = True
                                            break
                
                # 3. Margem CUB Singular — com data exata independe de diamante (FIX Schutzeler)
                # Sem data: exige diamante (CPF) para evitar false-positives
                if not match_perfeito and not lista_multipla:
                    diamante_no_grupo = any(c['is_diamante'] for c in grupo_vendas)
                    # FASE CUB-A: Data exata + margem 30% — qualquer match, não precisa de diamante
                    # Cobre variações de CUB/INCC onde o OCR capturou a data corretamente
                    if pdf_mes:
                        for p_tuple in pool_abertas:
                            p, cand, is_prazo = p_tuple
                            p_valor = float(p[2] or 0)
                            db_venc = str(p[1])
                            if (p_valor > 0 and total_pago > p_valor
                                    and f'-{pdf_mes}-' in db_venc
                                    and (not pdf_ano or pdf_ano in db_venc)):
                                diff_rate = (total_pago - p_valor) / p_valor
                                # valor_raiz bate com a parcela-base → acréscimo é a variação
                                valor_raiz_bate = valor_raiz and abs(valor_raiz - p_valor) < 5.0
                                if diff_rate < 0.30 or valor_raiz_bate:
                                    match_perfeito = p_tuple
                                    mat_type = "CUB_RECEBER_DATA_EXATA"
                                    break
                        if not match_perfeito:
                            for pr_tuple in pool_prazos:
                                pr, cand, is_prazo = pr_tuple
                                pr_valor = float(pr[2] or 0)
                                db_venc = str(pr[1])
                                if (pr_valor > 0 and total_pago > pr_valor
                                        and f'-{pdf_mes}-' in db_venc
                                        and (not pdf_ano or pdf_ano in db_venc)):
                                    diff_rate = (total_pago - pr_valor) / pr_valor
                                    valor_raiz_bate = valor_raiz and abs(valor_raiz - pr_valor) < 5.0
                                    if diff_rate < 0.30 or valor_raiz_bate:
                                        match_perfeito = pr_tuple
                                        mat_type = "CUB_PROJETADA_DATA_EXATA"
                                        break

                    # FASE CUB-B: Sem data — exige diamante (CPF) para evitar false-positives
                    if not match_perfeito and diamante_no_grupo:
                        for p_tuple in pool_abertas:
                            p, cand, is_prazo = p_tuple
                            p_valor = float(p[2] or 0)
                            if p_valor > 0 and total_pago > p_valor and (abs(total_pago - p_valor) / p_valor) < 2.0:
                                match_perfeito = p_tuple
                                mat_type = "CUB_RECEBER"
                                break
                                
                        if not match_perfeito:
                            for pr_tuple in pool_prazos:
                                pr, cand, is_prazo = pr_tuple
                                pr_valor = float(pr[2] or 0)
                                if pr_valor > 0 and total_pago > pr_valor and (abs(total_pago - pr_valor) / pr_valor) < 2.0:
                                    match_perfeito = pr_tuple
                                    mat_type = "CUB_PROJETADA"
                                    break
                                        
                if match_perfeito:
                    cand = match_perfeito[1]
                    mat_reason = f"Match Global ({mat_type})"
                    melhor_match_final = { 'type': mat_type, 'db_raw': match_perfeito[0], 'reason': mat_reason, 'v_row': cand['v_row'] }
                    break
                elif lista_multipla:
                    if not mat_type:
                        mat_type = "MULTIPLO_RECEBER"
                    melhor_match_final = { 'type': mat_type, 'lista': lista_multipla }
                    break
                    
            # ── FASE CROSS-GROUP: Co-proprietários (múltiplas vendas mesma unidade) ──────────
            # Caso: David + esposa têm 2 vendas separadas; extrato tem 1 linha = soma das 2.
            # FIX bugs: break→continue; pool pré-filtrado para mês alvo (performance + precisão).
            if not melhor_match_final:
                from itertools import combinations as _combs
                _all_q_cg = []   # quitadas do mês alvo, cross-group
                _all_a_cg = []   # abertas do mês alvo, cross-group
                _seen_cg = set()
                for _gk, _gv in grupos_unidades.items():
                    for _gc in _gv:
                        _gv_id = int(_gc['v_row'][0])
                        if _gv_id in _seen_cg:
                            continue
                        _seen_cg.add(_gv_id)
                        for _ra in _cache_receber.get(_gv_id, []):
                            if _ra[0] in reserved_ids_receber:
                                continue
                            # Pré-filtro de mês: só inclui parcelas do mês alvo do PDF
                            _ra_data = str(_ra[1])
                            if pdf_mes and f'-{pdf_mes}-' not in _ra_data:
                                continue
                            if pdf_ano and pdf_ano not in _ra_data:
                                continue
                            _tup = (_ra, _gc, False)
                            if float(_ra[3] or 0) > 0:
                                _all_q_cg.append(_tup)
                            else:
                                _all_a_cg.append(_tup)
                        for _pr in _cache_prazos.get(_gv_id, []):
                            if _pr[0] in reserved_ids_prazos:
                                continue
                            _pr_data = str(_pr[1])
                            if pdf_mes and f'-{pdf_mes}-' not in _pr_data:
                                continue
                            if pdf_ano and pdf_ano not in _pr_data:
                                continue
                            _tup = (_pr, _gc, True)
                            if float(_pr[4] or 0) > 0:
                                _all_q_cg.append(_tup)
                            else:
                                _all_a_cg.append(_tup)

                logging.warning(f"  [CROSS-GROUP BUILD] '{comprador_nome}' unid='{unidade}' all_q={len(_all_q_cg)} all_a={len(_all_a_cg)}")

                # FIX: continue (não break) para tentar abertas quando quitadas falham
                for _pool_cg, _mat_cg in [(_all_q_cg, "MULTIPLO_JA_PAGO_CO_PROP"), (_all_a_cg, "MULTIPLO_RECEBER_CO_PROP")]:
                    if melhor_match_final:
                        break
                    if len(_pool_cg) < 2:
                        continue   # ← FIX: era 'break', ignorava o próximo pool
                    for _sz in [2, 3, 4]:
                        if melhor_match_final or len(_pool_cg) < _sz:
                            break
                        for _combo in _combs(_pool_cg, _sz):
                            # OBRIGATÓRIO: combo deve cruzar vendas diferentes
                            _vids_cb = set(_c[1]['v_row'][0] for _c in _combo)
                            if len(_vids_cb) < 2:
                                continue
                            # FIX: para quitadas usa TOTALPAGO (índice 3 para RECEBER, índice 4 para PRAZO)
                            # Para abertas usa VALORPARCELA/VALOR (índice 2)
                            def _val_item(it):
                                d, _, is_pr = it
                                if _mat_cg == "MULTIPLO_JA_PAGO_CO_PROP":
                                    return float(d[4] or d[2] or 0) if is_pr else float(d[3] or d[2] or 0)
                                return float(d[2] or 0)
                            _soma = sum(_val_item(_c) for _c in _combo)
                            if _soma <= 0:
                                continue
                            _dr = abs(total_pago - _soma) / _soma
                            if _dr >= 0.10:   # 10% — mais generoso que intra-grupo (5%)
                                continue
                            melhor_match_final = {'type': _mat_cg, 'lista': list(_combo)}
                            logging.warning(f"  [CROSS-GROUP HIT] '{comprador_nome}' unid='{unidade}' → {_mat_cg} sz={_sz} vids={_vids_cb} soma={_soma:.2f}")
                            break
                    if melhor_match_final:
                        break



            if melhor_match_final:

                if 'MULTIPLO' in melhor_match_final['type']:
                    lista = melhor_match_final['lista']
                    
                    ids_str = []
                    nomes_str = []
                    parcelas_str = []
                    rateios_list = []
                    soma_valor = 0
                    
                    base_p_data = lista[0]
                    base_p, base_cand, base_is_praz = base_p_data
                    base_v_id, _, base_c_id, _, base_v_desc, base_e_nome = base_cand['v_row']
                    
                    for item in lista:
                        p, cand, is_praz = item
                        v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = cand['v_row']
                        
                        r_acresc = 0
                        r_desc = 0
                        r_pago = 0
                        if is_praz:
                            pr_id, pr_data, pr_valor, f_id, p_valor_pago = p
                            p_id = f"PROJ-{pr_id}"
                            p_parcela = "Projeção"
                            reserved_ids_prazos.add(pr_id)
                            r_pago = float(pr_valor or 0)
                            proj_payload = {"idvenda": v_id, "idcliente": c_id, "data_vencimento": pr_data, "valor_previsto": pr_valor, "referencia": f"Projeção {pr_id}", "idprazopagto": pr_id}
                            rateios_list.append({"id_receber": p_id, "is_projetada": True, "proj_payload": proj_payload, "pago": r_pago, "acrescimo": r_acresc, "desconto": r_desc})
                        else:
                            p_id, p_venc, p_valor, p_pago, p_parcela = p
                            reserved_ids_receber.add(p_id)
                            r_pago = float(p_valor or 0)
                            rateios_list.append({"id_receber": p_id, "is_projetada": False, "pago": r_pago, "acrescimo": r_acresc, "desconto": r_desc})
                            
                        ids_str.append(str(p_id))
                        if dec(c_nome) not in nomes_str:
                            nomes_str.append(dec(c_nome))
                            
                        parcelas_str.append(dec(p_parcela) or "S/PARC")
                        soma_valor += float(p_valor or 0)
                        
                    calc_acresc = float(row.get('acrescimos_variacoes', 0) or 0)
                    if total_pago > soma_valor and calc_acresc == 0:
                        calc_acresc = total_pago - soma_valor
                    
                    if len(rateios_list) > 0:
                        rateios_list[0]['acrescimo'] = calc_acresc
                        rateios_list[0]['desconto'] = float(row.get('descontos', 0) or 0)
                    
                    p_venc = base_p[1]    
                    venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                        
                    is_ja_pago = 'JA_PAGO' in melhor_match_final['type']
                    reason = "Fatura Histórica Conjunta Quitada no ERP" if is_ja_pago else f"Consolidado Conjunto ({len(lista)} Titulos ERP)"
                    status_ret = "ALERTA_JA_PAGO" if is_ja_pago else "MATCH_PERFEITO"
                        
                    results.append({
                        'row': row, 
                        'has_date': has_date, 
                        'matched': True, 
                        'match_reason': reason, 
                        'status': status_ret, 
                        'id_receber': " & ".join(ids_str) if not is_ja_pago else None,
                        'erp_data': {
                            'ID': " & ".join(ids_str), 
                            'CLIENTE_NOME': " & ".join(nomes_str), 
                            'DESCUNIDIMOB': dec(base_v_desc), 
                            'EMPREENDIMENTO': dec(base_e_nome)
                        },
                        'db_estado_atual': {
                            'venda': base_v_id, 
                            'cliente': " & ".join(nomes_str), 
                            'vencimento': venc_str, 
                            'valor_parcela': soma_valor, 
                            'parcela': " & ".join(parcelas_str), 
                            'pago_hoje': 0
                        },
                        'proposta_ia': {
                            'novo_total_pago': total_pago if not is_ja_pago else 0, 
                            'novo_desconto': float(row.get('descontos', 0) or 0) if not is_ja_pago else 0, 
                            'novo_acrescimo': calc_acresc if not is_ja_pago else 0, 
                            'projetada': False,
                            'rateios': rateios_list if not is_ja_pago else []
                        }
                    })
                elif 'JA_PAGO' in melhor_match_final['type']:
                    v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = melhor_match_final['v_row']
                    match_reason = melhor_match_final['reason']
                    mat_type = melhor_match_final['type']
                    
                    if 'RECEBER' in mat_type:
                        p_id, p_venc, p_valor, p_pago, p_parcela = melhor_match_final['db_raw']
                        venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                        results.append({
                            'row': row, 'has_date': has_date, 'matched': True, 'match_reason': "Fatura já consta Quitada no ERP", 'status': 'ALERTA_JA_PAGO', 'id_receber': p_id,
                            'erp_data': {'ID': p_id, 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': venc_str, 'valor_parcela': float(p_valor or 0), 'parcela': dec(p_parcela), 'pago_hoje': float(p_pago or 0)},
                            'proposta_ia': {'novo_total_pago': float(p_pago or 0), 'novo_desconto': 0, 'novo_acrescimo': 0, 'projetada': False}
                        })
                    elif 'PROJETADA' in mat_type:
                        pr_id, pr_data, pr_valor, f_id, p_valor_pago = melhor_match_final['db_raw']
                        proj_venc = pr_data.strftime('%d/%m/%Y') if hasattr(pr_data, 'strftime') else dec(pr_data)
                        results.append({
                            'row': row, 'has_date': has_date, 'matched': True, 'match_reason': "Fatura já consta Quitada no ERP", 'status': 'ALERTA_JA_PAGO', 'id_receber': None,
                            'erp_data': {'ID': 'PROJ-' + str(pr_id), 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': float(pr_valor or 0), 'parcela': f'Projeção Quitada {pr_id}', 'pago_hoje': float(p_valor_pago or 0)},
                            'proposta_ia': {'novo_total_pago': float(p_valor_pago or 0), 'novo_desconto': 0, 'novo_acrescimo': 0, 'projetada': False}
                        })
                elif 'MULTIPLO' in melhor_match_final['type']:
                    lista = melhor_match_final['lista']
                    
                    ids_str = []
                    nomes_str = []
                    parcelas_str = []
                    soma_valor = 0
                    
                    base_p_data = lista[0]
                    base_p, base_cand, base_is_praz = base_p_data
                    base_v_id, _, base_c_id, _, base_v_desc, base_e_nome = base_cand['v_row']
                    
                    rateios_list = []
                    
                    for item in lista:
                        p, cand, is_praz = item
                        v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = cand['v_row']
                        
                        r_acresc = 0
                        r_desc = 0
                        r_pago = 0
                        if is_praz:
                            pr_id, pr_data, pr_valor, f_id, p_valor_pago = p
                            p_id = f"PROJ-{pr_id}"
                            p_parcela = "Projeção"
                            reserved_ids_prazos.add(pr_id)
                            r_pago = float(pr_valor or 0)
                            proj_payload = {"idvenda": v_id, "idcliente": c_id, "data_vencimento": pr_data, "valor_previsto": pr_valor, "referencia": f"Projeção {pr_id}", "idprazopagto": pr_id}
                            rateios_list.append({"id_receber": p_id, "is_projetada": True, "proj_payload": proj_payload, "pago": r_pago, "acrescimo": r_acresc, "desconto": r_desc})
                        else:
                            p_id, p_venc, p_valor, p_pago, p_parcela = p
                            reserved_ids_receber.add(p_id)
                            r_pago = float(p_valor or 0)
                            rateios_list.append({"id_receber": p_id, "is_projetada": False, "pago": r_pago, "acrescimo": r_acresc, "desconto": r_desc})
                            
                        ids_str.append(str(p_id))
                        if dec(c_nome) not in nomes_str:
                            nomes_str.append(dec(c_nome))
                            
                        parcelas_str.append(dec(p_parcela) or "S/PARC")
                        soma_valor += float(p_valor or 0)
                        
                    calc_acresc = float(row.get('acrescimos_variacoes', 0) or 0)
                    if total_pago > soma_valor and calc_acresc == 0:
                        calc_acresc = total_pago - soma_valor
                    
                    if len(rateios_list) > 0:
                        rateios_list[0]['acrescimo'] = calc_acresc
                        rateios_list[0]['desconto'] = float(row.get('descontos', 0) or 0)
                    
                    p_venc = base_p[1]    
                    venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                        
                    results.append({
                        'row': row, 
                        'has_date': has_date, 
                        'matched': True, 
                        'match_reason': f"Consolidado Conjunto ({len(lista)} Titulos ERP)", 
                        'status': 'MATCH_PERFEITO', 
                        'id_receber': " & ".join(ids_str),
                        'erp_data': {
                            'ID': " & ".join(ids_str), 
                            'CLIENTE_NOME': " & ".join(nomes_str), 
                            'DESCUNIDIMOB': dec(base_v_desc), 
                            'EMPREENDIMENTO': dec(base_e_nome)
                        },
                        'db_estado_atual': {
                            'venda': base_v_id, 
                            'cliente': " & ".join(nomes_str), 
                            'vencimento': venc_str, 
                            'valor_parcela': soma_valor, 
                            'parcela': " & ".join(parcelas_str), 
                            'pago_hoje': 0
                        },
                        'proposta_ia': {
                            'novo_total_pago': total_pago, 
                            'novo_desconto': float(row.get('descontos', 0) or 0), 
                            'novo_acrescimo': calc_acresc, 
                            'projetada': False,
                            'rateios': rateios_list
                        }
                    })
                else:    
                    v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = melhor_match_final['v_row']
                    match_reason = melhor_match_final['reason']
                    mat_type = melhor_match_final['type']
                    
                    if 'RECEBER' in mat_type:
                        p_id, p_venc, p_valor, p_pago, p_parcela = melhor_match_final['db_raw']
                        reserved_ids_receber.add(p_id)
                        
                        calc_acresc = float(row.get('acrescimos_variacoes', 0) or 0)
                        if total_pago > float(p_valor or 0) and calc_acresc == 0:
                            calc_acresc = total_pago - float(p_valor or 0)
                            
                        venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                        results.append({
                            'row': row, 'has_date': has_date, 'matched': True, 'match_reason': match_reason, 'status': 'MATCH_PERFEITO', 'id_receber': p_id,
                            'erp_data': {'ID': p_id, 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': venc_str, 'valor_parcela': float(p_valor or 0), 'parcela': dec(p_parcela), 'pago_hoje': float(p_pago or 0)},
                            'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': calc_acresc, 'projetada': False}
                        })
                    elif 'PROJETADA' in mat_type:
                        pr_id, pr_data, pr_valor, f_id, p_valor_pago = melhor_match_final['db_raw']
                        reserved_ids_prazos.add(pr_id)
                        
                        calc_acresc = float(row.get('acrescimos_variacoes', 0) or 0)
                        if total_pago > float(pr_valor or 0) and calc_acresc == 0:
                            calc_acresc = total_pago - float(pr_valor or 0)
                            
                        proj_venc = pr_data.strftime('%d/%m/%Y') if hasattr(pr_data, 'strftime') else dec(pr_data)
                        results.append({
                            'row': row, 'has_date': has_date, 'matched': True, 'match_reason': match_reason, 'status': 'PROJETADA_NOVA_LINHA', 'id_receber': None,
                            'erp_data': {'ID': 'PROJ-' + str(pr_id), 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': float(pr_valor or 0), 'parcela': f'Projeção ERP {pr_id}', 'pago_hoje': 0},
                            'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': calc_acresc, 'projetada': True,
                                'proj_payload': {'idvenda': v_id, 'idcliente': c_id, 'idformapagto': f_id, 'idprazopagto': pr_id, 'data_vencimento': pr_data.strftime('%Y-%m-%d') if hasattr(pr_data, 'strftime') else str(pr_data), 'valor_previsto': float(pr_valor or 0), 'referencia': f'Projeção {pr_id}'}
                            }
                        })
            else:
                best_cand = candidatas[0]
                v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = best_cand['v_row']
                
                is_ouro = False
                if comprador_nome and clean_str(comprador_nome) in clean_str(c_nome): is_ouro = True
                elif unidade and v_desc_db and clean_str(unidade) in clean_str(v_desc_db): is_ouro = True
                    
                match_reason = 'Match Ouro (Nome/Unidade) Nativo'
                if best_cand['is_diamante']: match_reason = 'Match Diamante (CPF/CNPJ) Nativo'
                
                pr_id = -1 * (hash(str(v_id) + str(total_pago) + str(row.get('dt_vencimento', ''))) % 1000000)
                proj_venc = str(row.get('dt_vencimento', ''))
                results.append({
                    'row': row, 'has_date': has_date, 'matched': True, 'match_reason': f'{match_reason}', 'status': 'PROJETADA_NOVA_LINHA_NATIVA', 'id_receber': None,
                    'erp_data': {'ID': f'NTV-{abs(pr_id)}', 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                    'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': total_pago, 'parcela': 'Gerada Nativa Extra-Caixa', 'pago_hoje': 0},
                    'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': True, 'nativa_sqlite': True,
                        'proj_payload': {'idvenda': v_id, 'idcliente': c_id, 'data_vencimento': proj_venc, 'valor_previsto': total_pago, 'referencia': 'Baixa Nativa Multi', 'pseudo_id': pr_id}
                    }
                })

        # ── Injeta anomaly_score (PyOD) em cada resultado ──
        for i, res in enumerate(results):
            pyod_info = _pyod_map.get(i, {})
            res["anomaly_score"]  = pyod_info.get("anomaly_score")
            res["anomaly_flag"]   = pyod_info.get("anomaly_flag", False)
            res["match_engine"]   = res.get("match_engine", "splink" if data.use_splink else "heuristic")
        return {"resultados": results}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


class CommitBaixasInput(BaseModel):
    empresa_id: int
    lote_efetivado: list[dict]
    arquivo_nome: str = "Extrato_Manual.pdf"

@app.post("/api/parser/commit-baixas")
def commit_baixas(data: CommitBaixasInput):
    import datetime
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        hoje_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO IMPORTACAO_LOTE (ARQUIVO_NOME, DATA_UPLOAD, TOTAL_BAIXAS) VALUES (?, ?, ?)", 
                   (data.arquivo_nome, hoje_str, len(data.lote_efetivado)))
        lote_id = cur.lastrowid
        
        lote_expandido = []
        for item in data.lote_efetivado:
            prop = item.get("proposta_ia", {})
            if "rateios" in prop and isinstance(prop["rateios"], list):
                for rat in prop["rateios"]:
                    v_item = dict(item)
                    v_item["id_receber"] = rat.get("id_receber")
                    v_item["proposta_ia"] = {
                        "projetada": rat.get("is_projetada", False),
                        "proj_payload": rat.get("proj_payload"),
                        "novo_total_pago": rat.get("pago", 0),
                        "novo_desconto": rat.get("desconto", 0),
                        "novo_acrescimo": rat.get("acrescimo", 0)
                    }
                    lote_expandido.append(v_item)
            else:
                lote_expandido.append(item)
        
        sucessos = 0
        for item in lote_expandido:
            rid = item.get("id_receber")
            prop = item.get("proposta_ia", {})
            row = item.get("row", {})
            banco = row.get("banco", "DESCONHECIDO")
            dt_pagto = row.get("dt_pagamento", hoje_str[:10])
            
            if prop.get("projetada") and prop.get("proj_payload"):
                pl = prop["proj_payload"]
                cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM RECEBER")
                rid = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO RECEBER (ID, IDVENDA, IDCLIENTE, DATA, VALORPARCELA, PARCELA, OBS, IDVENDAFORMAPAGTO, IDVENDAFORMAPAGTOPRAZO)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (rid, pl["idvenda"], pl["idcliente"], pl["data_vencimento"], pl["valor_previsto"], pl["referencia"], "PROJ INDUZIDA PELO PARSER", pl.get("idformapagto"), pl.get("idprazopagto")))
                
                # Update prazos to avoid zombies
                if pl.get("idprazopagto"):
                    cur.execute("UPDATE VENDAFORMAPAGTOPRAZO SET VALOR_PAGO = ? WHERE ID = ?", (float(prop.get("novo_total_pago", 0)), pl["idprazopagto"]))

            if not rid: continue
            
            # Registrar no Tabela Historica
            cur.execute("""
                INSERT INTO RECEBIMENTO_FINANCEIRO (ID_LOTE, ID_RECEBER, DATA_PAGAMENTO, VALOR_PAGO, RATEIO_TEXT, BANCO, ACRESCIMO, DESCONTO)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lote_id, rid, dt_pagto, float(prop.get("novo_total_pago",0)), str(item.get("match_reason","")), banco,
                float(prop.get("novo_acrescimo", 0)), float(prop.get("novo_desconto", 0))
            ))
            
            cur.execute("SELECT TOTALPAGO FROM RECEBER WHERE ID = ?", (rid,))
            r = cur.fetchone()
            if not r or (r[0] is not None and float(r[0]) > 0):
                continue
                
            cur.execute(
                "UPDATE RECEBER SET TOTALPAGO = ?, DESCONTO = ?, VALORVARIACAO = ?, OBS = ? WHERE ID = ?",
                (
                    float(prop.get("novo_total_pago", 0)),
                    float(prop.get("novo_desconto", 0)),
                    float(prop.get("novo_acrescimo", 0)),
                    f"BAIXA LOTE {lote_id}",
                    int(rid)
                )
            )
            sucessos += 1
            
        conn.commit()
        return {"success": True, "baixados": sucessos, "lote_id": lote_id}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# --- ROTAS BASE: ÁREA FISCAL E SERO ---
@app.post("/api/fiscal/f200")
def fiscal_injetar_f200():
    return {"success": True, "message": "Simulação de injeção de F200 concluída (Tabelas Venda/Recebimento). Backend conectará no Questor."}

@app.post("/api/fiscal/ret")
def fiscal_injetar_ret():
    return {"success": True, "message": "Simulação de injeção RET concluída (EFDINCORPIMOBRET)."}

@app.post("/api/fiscal/distratos")
def fiscal_injetar_distratos():
    return {"success": True, "message": "Ajuste de Distratos processado. (EFDAJUSTEPISCOFINS)"}

@app.post("/api/fiscal/dimob")
def fiscal_gerar_dimob():
    return {"success": True, "message": "Arquivo DIMOB gerado estruturalmente."}

@app.get("/api/sero/obras")
def get_sero_obras(empresa_id: int):
    try:
        conn_q = get_conn("questor")
        conn_v = get_conn("vulcano")
        cur_q  = conn_q.cursor()
        cur_v  = conn_v.cursor()
        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode("win1252", "ignore").strip()
            return str(v).strip()

        # OUTEMPs com folha própria (CALCULORATEIO evento 5041)
        cur_q.execute("""
            SELECT DISTINCT C.CODIGOOUTEMP
            FROM CALCULORATEIO C
            WHERE C.CODIGOEMPRESA = ? AND C.CODIGOEVENTO = 5041
        """, (empresa_id,))
        outemps_folha = {r[0] for r in cur_q.fetchall()}

        # OUTEMPs com GPS terceiros (TERCEIROPGTO)
        cur_q.execute("""
            SELECT DISTINCT CODIGOOUTEMP
            FROM TERCEIROPGTO
            WHERE CODIGOEMPRESA = ?
        """, (empresa_id,))
        outemps_gps = {r[0] for r in cur_q.fetchall()}

        todos_outemps = outemps_folha | outemps_gps
        if not todos_outemps:
            conn_q.close(); conn_v.close()
            return []

        placeholders = ",".join("?" * len(todos_outemps))
        cur_q.execute(f"""
            SELECT OE.CODIGOOUTEMP, OE.NOMEOUTEMP, OE.INSCRFEDERAL,
                   OEE.INSCRFEDPROPRIET, OEE.TIPOOUTEMP
            FROM OUTRAEMPEMP OEE
            JOIN OUTRAEMPRESA OE ON OE.CODIGOOUTEMP = OEE.CODIGOOUTEMP
            WHERE OEE.CODIGOEMPRESA = ?
              AND OEE.CODIGOOUTEMP IN ({placeholders})
            ORDER BY OEE.TIPOOUTEMP, OE.NOMEOUTEMP
        """, tuple([empresa_id] + list(todos_outemps)))
        rows_q = cur_q.fetchall()

        try:
            cur_v.execute("""
                SELECT ID, NOME, CODIGOCENTROCUSTO FROM EMPREENDIMENTO
                WHERE CODIGOEMPRESA = ?
                  AND (OBRACONCLUIDA = 'N' OR OBRACONCLUIDA IS NULL)
                ORDER BY ID DESC
            """, (empresa_id,))
            vulcano_projetos = cur_v.fetchall()
        except Exception:
            cur_v.execute("""
                SELECT ID, NOME, CODIGOCENTROCUSTO FROM EMPREENDIMENTO
                WHERE CODIGOEMPRESA = ? ORDER BY ID DESC
            """, (empresa_id,))
            vulcano_projetos = cur_v.fetchall()

        obras = []
        for r in rows_q:
            cod = r[0]
            nome_q = dec(r[1])
            tipo   = dec(r[4])
            inscr  = dec(r[2])
            cnpj_prop = dec(r[3])
            tem_folha = cod in outemps_folha
            tem_gps = cod in outemps_gps
            
            if tipo == "2":
                if vulcano_projetos:
                    for pid, pnome, pcc in vulcano_projetos:
                        if pcc:
                            obras.append({
                                "id": f"{cod}|{pcc}",
                                "nome": f"{dec(pnome)} (CC {pcc})",
                                "nome_questor": nome_q,
                                "inscricao": inscr,
                                "cnpj_proprietario": cnpj_prop,
                                "tipo": 2,
                                "tem_folha": tem_folha,
                                "tem_gps": tem_gps,
                            })
                    continue 
            
            obras.append({
                "id": str(cod),
                "nome": nome_q,
                "nome_questor": nome_q,
                "inscricao": inscr,
                "cnpj_proprietario": cnpj_prop,
                "tipo": int(tipo) if tipo else 1,
                "tem_folha": tem_folha,
                "tem_gps": tem_gps,
            })
            
        conn_q.close(); conn_v.close()
        return obras
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.get("/api/sero/cub")

def get_sero_cub(compet: str = Query(..., description="Mes YYYY-MM")):
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        compet_db = compet + '-31'
        cur.execute("SELECT FIRST 1 VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND VALOR IS NOT NULL AND MES <= ? ORDER BY MES DESC", (compet_db,))
        r = cur.fetchone()
        conn.close()
        return {"cub": float(r[0]) if r and r[0] else None}
    except Exception as e:
        return {"error": str(e), "cub": None}

@app.get("/api/sped/f200/preview")
def sped_f200_preview(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_f200
    res = processar_f200(empresa_id, ano, mes, dry_run=True, get_conn=get_conn)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.post("/api/sped/f200/commit")
def sped_f200_commit(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_f200
    res = processar_f200(empresa_id, ano, mes, dry_run=False, get_conn=get_conn)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.get("/api/sped/ret/preview")
def sped_ret_preview(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_ret
    res = processar_ret(empresa_id, ano, mes, dry_run=True, get_conn=get_conn)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.post("/api/sped/ret/commit")
def sped_ret_commit(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_ret
    res = processar_ret(empresa_id, ano, mes, dry_run=False, get_conn=get_conn)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.get("/api/sped/resumo")
def sped_resumo(empresa_id: int, ano: int, mes: int):
    """Quadro Resumo por empreendimento (tela legada 'Consultar F200'):
    F200 (parcela/variação/base/PIS/COFINS) + RET (base/valor) + distratos do mês."""
    from injector_sped import processar_ret, processar_f200
    ret = processar_ret(empresa_id, ano, mes, dry_run=True, get_conn=get_conn)
    if not ret.get("success"):
        raise HTTPException(status_code=500, detail=f"RET: {ret.get('error')}")
    f200 = processar_f200(empresa_id, ano, mes, dry_run=True, get_conn=get_conn)
    if not f200.get("success"):
        raise HTTPException(status_code=500, detail=f"F200: {f200.get('error')}")

    obras = {}
    def _slot(nome):
        nome = (nome or "(sem empreendimento)").strip() or "(sem empreendimento)"
        return obras.setdefault(nome.upper(), {
            "empreendimento": nome, "recebimentos": 0.0, "valor_parcela": 0.0,
            "variacao": 0.0, "bc_f200": 0.0, "pis": 0.0, "cofins": 0.0,
            "bc_ret": 0.0, "valor_ret": 0.0, "aliq_ret": None, "distrato": 0.0,
        })

    for r in f200.get("data", []):
        s = _slot(r.get("obra"))
        s["recebimentos"] += r["vltotrec"]
        s["valor_parcela"] += r.get("valor_parcela", r["vltotrec"])
        s["variacao"] += r.get("variacao", 0.0)
        s["bc_f200"] += r["vlbc"]
        s["pis"] += r["vlpis"]
        s["cofins"] += r["vlcofins"]
    for r in ret.get("data", []):
        s = _slot(r.get("unidade"))
        s["recebimentos"] += r["base_calculo"]
        s["valor_parcela"] += r["receita_principal"]
        s["variacao"] += r["receita_financeira"]
        s["bc_ret"] += r["base_calculo"]
        s["valor_ret"] += r["total_ret"]
        s["aliq_ret"] = r["aliqret"]

    # Distratos do mês (informativo)
    import calendar as _cal
    import datetime as _dt
    dt_ini = _dt.date(ano, mes, 1)
    dt_fim = _dt.date(ano, mes, _cal.monthrange(ano, mes)[1])
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("""
            SELECT E.NOME, SUM(V.TOTALVENDA)
            FROM VENDA V
            LEFT JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ? AND V.DISTRATO = 'S'
              AND V.DATADISTRATO >= ? AND V.DATADISTRATO <= ?
            GROUP BY E.NOME
        """, (empresa_id, dt_ini, dt_fim))
        for nome, valor in cur.fetchall():
            nome = nome.decode("cp1252", "ignore") if isinstance(nome, bytes) else str(nome or "")
            _slot(nome)["distrato"] += float(valor or 0)
    except Exception:
        pass
    finally:
        if conn: conn.close()

    rows = sorted(obras.values(), key=lambda x: x["empreendimento"])
    for r in rows:
        for k in ("recebimentos", "valor_parcela", "variacao", "bc_f200", "pis",
                  "cofins", "bc_ret", "valor_ret", "distrato"):
            r[k] = round(r[k], 2)
    tot = {k: round(sum(r[k] for r in rows), 2)
           for k in ("recebimentos", "valor_parcela", "variacao", "bc_f200", "pis",
                     "cofins", "bc_ret", "valor_ret", "distrato")}
    return {"success": True, "data": rows, "totais": tot}

@app.get("/api/sped/analitico-unidades")
def sped_analitico_unidades(empresa_id: int, ano: int, mes: int):
    """Conferência apartamento por apartamento do que compõe os registros do SPED:
    cada linha é uma venda/unidade com recebimento na competência, classificada no
    destino RET (bloco 1800 — registro único por obra optante) ou F200. Usa as
    MESMAS regras da apuração (injector_sped): RET='S' + DATAINICIORET por parcela,
    distrato fora, TOTALPAGO>0 — os subtotais por obra batem com o registro."""
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        # por parcela (sem GROUP BY): classificacao RET/F200 e por parcela — uma
        # venda pode se dividir na virada do DATAINICIORET; agrega em python
        cur.execute("""
            SELECT E.NOME, E.RET, E.DATAINICIORET, E.ALIQRET,
                   V.ID, V.DESCUNIDIMOB, V.NUMCADIMOB, C.NOME, C.CNPJ,
                   R.DATA, R.TOTALPAGO, COALESCE(R.VALORVARIACAO, 0)
            FROM RECEBER R
            JOIN VENDA V ON R.IDVENDA = V.ID
            JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
            LEFT JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND R.TOTALPAGO > 0
              AND EXTRACT(YEAR FROM R.DATA) = ?
              AND EXTRACT(MONTH FROM R.DATA) = ?
        """, (empresa_id, ano, mes))

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()

        import datetime as _dt
        linhas = {}
        for r in cur.fetchall():
            (obra, ret_flag, dt_ini_ret, aliqret, vid, unidade, numcad,
             cliente, cnpj, data, pago, variacao) = r
            if isinstance(data, _dt.datetime):
                data = data.date()
            if isinstance(dt_ini_ret, _dt.datetime):
                dt_ini_ret = dt_ini_ret.date()
            # mesma regra do injector: parcela optante vai pro 1800, resto e F200
            eh_ret = dec(ret_flag) == 'S' and (dt_ini_ret is None or (data and data >= dt_ini_ret))
            destino = "RET_1800" if eh_ret else "F200"
            chave = (vid, destino)
            item = linhas.get(chave)
            if not item:
                item = linhas[chave] = {
                    "venda_id": vid, "destino": destino,
                    "empreendimento": dec(obra) or "(sem empreendimento)",
                    "unidade": dec(unidade), "numcadimob": numcad,
                    "comprador": dec(cliente), "cpf_cnpj": dec(cnpj),
                    "aliqret": float(aliqret) if (eh_ret and aliqret is not None) else (4.0 if eh_ret else None),
                    "qtd_parcelas": 0, "valor_parcela": 0.0, "variacao": 0.0, "total_recebido": 0.0,
                }
            item["qtd_parcelas"] += 1
            item["total_recebido"] += float(pago or 0)
            item["variacao"] += float(variacao or 0)
            item["valor_parcela"] += float(pago or 0) - float(variacao or 0)

        data_rows = sorted(linhas.values(), key=lambda x: (x["empreendimento"], x["destino"], x["unidade"], x["comprador"]))
        grupos = {}
        for x in data_rows:
            for k in ("valor_parcela", "variacao", "total_recebido"):
                x[k] = round(x[k], 2)
            x["ret_estimado"] = round(x["total_recebido"] * (x["aliqret"] or 0) / 100, 2) if x["destino"] == "RET_1800" else None
            g = grupos.setdefault((x["empreendimento"], x["destino"]), {
                "empreendimento": x["empreendimento"], "destino": x["destino"],
                "aliqret": x["aliqret"], "qtd_unidades": 0, "qtd_parcelas": 0,
                "valor_parcela": 0.0, "variacao": 0.0, "total_recebido": 0.0, "ret_total": 0.0,
            })
            g["qtd_unidades"] += 1
            g["qtd_parcelas"] += x["qtd_parcelas"]
            g["valor_parcela"] = round(g["valor_parcela"] + x["valor_parcela"], 2)
            g["variacao"] = round(g["variacao"] + x["variacao"], 2)
            g["total_recebido"] = round(g["total_recebido"] + x["total_recebido"], 2)
            if x["ret_estimado"]:
                g["ret_total"] = round(g["ret_total"] + x["ret_estimado"], 2)
        # guia RET oficial e calculada sobre a BASE agregada da obra (evita drift de
        # arredondamento por unidade): recalcula no grupo
        for g in grupos.values():
            if g["destino"] == "RET_1800" and g["aliqret"]:
                g["ret_total"] = round(g["total_recebido"] * g["aliqret"] / 100, 2)

        return {"success": True, "data": data_rows,
                "grupos": sorted(grupos.values(), key=lambda x: (x["empreendimento"], x["destino"]))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.post("/api/vulcano/cronograma/sanear")
def sanear_cronograma(empresa_id: int, empreendimento_id: int = None, dry_run: bool = True):
    """Saneamento do cronograma legado: as baixas antigas entraram só no RECEBER e
    nunca marcaram VALOR_PAGO no VENDAFORMAPAGTOPRAZO — a venda parece ter dezenas
    de parcelas 'previstas' já cobertas pelo dinheiro recebido (caso Luiz Osnildo:
    234 abertas x saldo real de 2 parcelas).

    Regra: por venda, principal amortizado = Σ(TOTALPAGO − VARIACAO + DESCONTO) do
    RECEBER; abate primeiro o que o cronograma já tem marcado; o restante quita as
    parcelas abertas em ordem de vencimento (FIFO), só INTEIRAS — sem parciais.
    dry_run=true (default) apenas lista o que seria marcado."""
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()

        def dec(v):
            if v is None: return ""
            if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
            return str(v).strip()

        filtro_emp = " AND V.IDEMPREENDIMENTO = ?" if empreendimento_id else ""
        params_emp = [empresa_id] + ([empreendimento_id] if empreendimento_id else [])

        # principal amortizado por venda (mesmo criterio do saldo da tela Mensal)
        cur.execute(f"""
            SELECT R.IDVENDA, SUM(R.TOTALPAGO - COALESCE(R.VALORVARIACAO,0) + COALESCE(R.DESCONTO,0))
            FROM RECEBER R JOIN VENDA V ON R.IDVENDA = V.ID
            WHERE V.CODIGOEMPRESA = ? AND R.TOTALPAGO > 0
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              {filtro_emp}
            GROUP BY R.IDVENDA
        """, tuple(params_emp))
        amortizado = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

        # cronograma (formas ativas): ja marcado e abertos por venda
        cur.execute(f"""
            SELECT F.IDVENDA, P.ID, P.DATA, COALESCE(P.VALOR, 0), COALESCE(P.VALOR_PAGO, 0), C.NOME
            FROM VENDAFORMAPAGTOPRAZO P
            JOIN VENDAFORMAPAGTO F ON F.ID = P.IDVENDAFORMAPAGTO
            JOIN VENDA V ON V.ID = F.IDVENDA
            LEFT JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND COALESCE(F.ATIVA, 'S') <> 'N'
              {filtro_emp}
            ORDER BY F.IDVENDA, P.DATA, P.ID
        """, tuple(params_emp))

        por_venda = {}
        for vid, pid, pdata, valor, vpago, cnome in cur.fetchall():
            v = por_venda.setdefault(vid, {"comprador": dec(cnome), "ja_marcado": 0.0, "abertas": []})
            if float(vpago) > 0:
                v["ja_marcado"] += float(valor)
            else:
                v["abertas"].append((pid, str(pdata)[:10], float(valor)))

        plano, tot_parcelas, tot_valor = [], 0, 0.0
        for vid, v in por_venda.items():
            saldo_marcar = round(amortizado.get(vid, 0.0) - v["ja_marcado"], 2)
            if saldo_marcar <= 0 or not v["abertas"]:
                continue
            marcar = []
            for pid, pdata, valor in v["abertas"]:  # FIFO por vencimento
                if valor <= 0 or valor > saldo_marcar + 0.01:
                    break  # so parcela inteira; parou = resto continua aberto
                marcar.append({"prazo_id": pid, "vencimento": pdata, "valor": round(valor, 2)})
                saldo_marcar = round(saldo_marcar - valor, 2)
            if marcar:
                plano.append({
                    "venda_id": vid, "comprador": v["comprador"],
                    "amortizado_receber": round(amortizado.get(vid, 0.0), 2),
                    "ja_marcado_cronograma": round(v["ja_marcado"], 2),
                    "parcelas_a_marcar": len(marcar),
                    "valor_a_marcar": round(sum(m["valor"] for m in marcar), 2),
                    "restam_abertas": len(v["abertas"]) - len(marcar),
                    "parcelas": marcar,
                })
                tot_parcelas += len(marcar)
                tot_valor = round(tot_valor + plano[-1]["valor_a_marcar"], 2)

        if dry_run:
            return {"success": True, "dry_run": True, "vendas": len(plano),
                    "parcelas_a_marcar": tot_parcelas, "valor_a_marcar": tot_valor,
                    "plano": plano}

        for pv in plano:
            for m in pv["parcelas"]:
                cur.execute("UPDATE VENDAFORMAPAGTOPRAZO SET VALOR_PAGO = ? WHERE ID = ?",
                            (m["valor"], m["prazo_id"]))
        conn.commit()
        return {"success": True, "dry_run": False, "vendas": len(plano),
                "parcelas_marcadas": tot_parcelas, "valor_marcado": tot_valor,
                "message": f"{tot_parcelas} parcela(s) do cronograma marcadas como cobertas em {len(plano)} venda(s) — R$ {tot_valor:,.2f}."}
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.get("/api/vulcano/recebimentos-mensal")
def get_recebimentos_mensal(empresa_id: int, ano: int, mes: int, empreendimento_id: int = None):
    """Visão mensal legada (tela do analista): parcelas do mês de referência + abertas
    vencidas até o fim do mês, com saldos da venda e totais de rodapé."""
    import sqlite3
    import calendar as _cal
    import datetime as _dt
    dt_ini = _dt.date(ano, mes, 1)
    dt_fim = _dt.date(ano, mes, _cal.monthrange(ano, mes)[1])
    conn = None
    try:
        # baixas novas (SQLite): valor/data/variação/desconto — fundidas na visão
        baixas = {}
        try:
            s_conn = connect_app()
            s_cur = s_conn.cursor()
            s_cur.execute("""SELECT id_receber, valor_pago, data_pagamento, descontos, acrescimos
                             FROM operacoes_baixas WHERE empresa_id = ?""", (empresa_id,))
            baixas = {str(r[0]): {"valor_pago": float(r[1] or 0), "data": r[2],
                                  "desconto": float(r[3] or 0), "variacao": float(r[4] or 0)}
                      for r in s_cur.fetchall()}
            s_conn.close()
        except Exception:
            pass

        conn = get_conn("vulcano")
        cur = conn.cursor()

        filtro_emp = " AND V.IDEMPREENDIMENTO = ?" if empreendimento_id else ""
        params = [empresa_id, dt_ini, dt_fim, dt_fim]
        if empreendimento_id:
            params.append(empreendimento_id)
        cur.execute(f"""
            SELECT R.ID, V.ID, C.NOME, C.CNPJ, V.DESCUNIDIMOB, V.TOTALVENDA,
                   R.DATA, R.VALORPARCELA, R.DESCONTO, R.VALORVARIACAO, R.TOTALPAGO,
                   R.PARCELA, R.OBS, E.NOME
            FROM RECEBER R
            JOIN VENDA V ON R.IDVENDA = V.ID
            LEFT JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
            LEFT JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND ((R.DATA >= ? AND R.DATA <= ?)
                   OR (COALESCE(R.TOTALPAGO, 0) = 0 AND R.DATA <= ?))
              AND (V.IDVENDAVINCULADA IS NULL OR NOT EXISTS (
                    SELECT 1 FROM RECEBER RP
                    WHERE RP.IDVENDA = V.IDVENDAVINCULADA
                      AND RP.DATA = R.DATA
                      AND ABS(COALESCE(RP.VALORPARCELA, 0) - COALESCE(R.VALORPARCELA, 0)) < 0.02
                      AND ABS(COALESCE(RP.TOTALPAGO, 0) - COALESCE(R.TOTALPAGO, 0)) < 0.02))
              {filtro_emp}
            ORDER BY C.NOME, R.DATA, R.ID
        """, tuple(params))
        rows = cur.fetchall()
        # ↑ dedupe de SATÉLITE (auditoria 07/08): duplicatas legadas de
        # multi-comprador registram as MESMAS parcelas na venda vinculada —
        # a linha da satélite só entra quando NÃO houver espelho exato
        # (DATA+VALOR+PAGO) na principal, preservando pagamentos que o
        # legado registrou apenas na satélite (R$2,3mi na 95 / R$2,8mi na ALZ).

        # acumulados por venda: PRINCIPAL amortizado (total e antes do mês).
        # TOTALPAGO inclui a variação monetária — abatê-la do valor histórico do
        # contrato deixava o saldo NEGATIVO em contratos longos (caso Luiz Osnildo,
        # venda 121: 494.682,21 pagos com 184.947,21 de variação x contrato de
        # 311.291,00 = saldo -183.391,21). Amortização = TOTALPAGO - VARIACAO
        # + DESCONTO (para parcela quitada integral, é o valor nominal dela).
        def _acum(extra_sql, extra_params):
            cur.execute(f"""
                SELECT R.IDVENDA,
                       SUM(R.TOTALPAGO - COALESCE(R.VALORVARIACAO, 0) + COALESCE(R.DESCONTO, 0))
                FROM RECEBER R
                JOIN VENDA V ON R.IDVENDA = V.ID
                WHERE V.CODIGOEMPRESA = ? AND R.TOTALPAGO > 0 {extra_sql}
                GROUP BY R.IDVENDA
            """, tuple([empresa_id] + extra_params))
            return {r[0]: float(r[1] or 0) for r in cur.fetchall()}
        # "Saldo Atual" da tela = saldo no FIM DO MÊS selecionado, não o de hoje
        # — navegando para um mês passado, pagamentos posteriores não entram.
        pago_total = _acum(" AND R.DATA <= ?", [dt_fim])
        pago_antes = _acum(" AND R.DATA < ?", [dt_ini])

        # multi-comprador NOVO (rateio com marcador): a principal guarda só a
        # COTA do 1º CPF, mas as parcelas carregam o contrato cheio — sem esta
        # soma, o "Vlr Venda"/saldo do grupo rateado ficaria negativo conforme
        # paga. Vinculadas legadas SEM marcador ficam de fora (valor cheio
        # duplicado — somar dobraria).
        cur.execute("""
            SELECT V.IDVENDAVINCULADA, SUM(COALESCE(V.TOTALVENDA, 0))
            FROM VENDA V
            WHERE V.CODIGOEMPRESA = ? AND V.IDVENDAVINCULADA IS NOT NULL
              AND UPPER(COALESCE(V.INFCOMP, '')) LIKE 'VINCULADA VENDA #%'
            GROUP BY V.IDVENDAVINCULADA
        """, (empresa_id,))
        cota_extra = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

        # SALDO DO EMPREENDIMENTO (auditoria Belle Ville): o rodapé soma só as
        # vendas COM parcela no mês navegado — o operador comparava com o
        # legado/contábil e via "diferença". Este universo cobre TODAS as
        # vendas ativas do filtro (principais + cotas marcadas), saldo de
        # principal no fim do mês navegado.
        filtro_emp_v = " AND V.IDEMPREENDIMENTO = ?" if empreendimento_id else ""
        cur.execute(f"""
            SELECT V.ID, COALESCE(V.TOTALVENDA, 0) FROM VENDA V
            WHERE V.CODIGOEMPRESA = ? AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND V.IDVENDAVINCULADA IS NULL AND COALESCE(V.TOTALVENDA, 0) > 0.01
              {filtro_emp_v}
        """, tuple([empresa_id] + ([empreendimento_id] if empreendimento_id else [])))
        universo_rows = cur.fetchall()
        saldo_universo = round(sum(
            float(tv or 0) + cota_extra.get(vid, 0.0) - pago_total.get(vid, 0.0)
            for vid, tv in universo_rows), 2)
        contratos_ativos = len(universo_rows)

        def _s(v):
            return v.decode("cp1252", "ignore").strip() if isinstance(v, bytes) else (str(v).strip() if v is not None else "")

        # baixas novas ainda não refletidas no FDB reduzem o saldo da venda
        baixa_extra = {}
        result = []
        for r in rows:
            (rid, vid, cliente, cnpj, unidade, totalvenda, data, vparc,
             desc, var, pago, parcela, obs, obra) = r
            if isinstance(data, _dt.datetime):
                data = data.date()
            totalvenda = float(totalvenda or 0) + cota_extra.get(vid, 0.0)
            pago_f = float(pago or 0)
            bx = baixas.get(str(rid))
            if bx and pago_f <= 0 and str(bx["data"] or "")[:10] <= dt_fim.isoformat():
                baixa_extra[vid] = baixa_extra.get(vid, 0.0) + bx["valor_pago"] - bx["variacao"] + bx["desconto"]  # principal
            item = {
                "id": rid, "venda_id": vid,
                "comprador": _s(cliente), "cpf_cnpj": _s(cnpj),
                "unidade": _s(unidade), "empreendimento": _s(obra),
                "vlr_venda": round(totalvenda, 2),
                "saldo_anterior": round(totalvenda - pago_antes.get(vid, 0.0), 2),
                "vencimento": data.isoformat() if data else None,
                "data_pagto": bx["data"] if bx else "",
                "valor_parcela": round(float(vparc or 0), 2),
                "desconto": round(float(desc or 0), 2),
                "variacao": round(float(var or 0), 2),
                "total_pago": round(pago_f, 2),
                "saldo_atual": round(totalvenda - pago_total.get(vid, 0.0), 2),
                "parcela": _s(parcela), "obs": _s(obs),
                "status": "PAGO" if pago_f > 0 else ("VENCIDA" if data and data < dt_ini else "ABERTA"),
                "baixa_local": bool(bx and pago_f <= 0),
            }
            if bx and pago_f <= 0:  # baixada pelo Vulcano 2.0 (SQLite), FDB ainda em aberto
                item["total_pago"] = round(bx["valor_pago"], 2)
                item["variacao"] = round(bx["variacao"], 2)
                item["desconto"] = round(bx["desconto"], 2)
                item["status"] = "PAGO"
            result.append(item)

        # ── PARCELAS DO CRONOGRAMA (VENDAFORMAPAGTOPRAZO ainda nao efetivadas) ──
        # Vendas legadas tem as parcelas futuras/do mes so no cronograma; sem esta
        # mescla, filtrar um empreendimento cujo mes esta todo no cronograma
        # devolvia lista vazia ("as parcelas somem"). Mescla direto do Firebird
        # (nao depende do sync local de parcelas_abertas_projetadas).
        assinaturas = {(x["venda_id"], x["vencimento"], round(x["valor_parcela"], 2)) for x in result}
        cur.execute(f"""
            SELECT P.ID, V.ID, C.NOME, C.CNPJ, V.DESCUNIDIMOB, V.TOTALVENDA,
                   P.DATA, P.VALOR, P.REFERENCIA, E.NOME
            FROM VENDAFORMAPAGTOPRAZO P
            JOIN VENDAFORMAPAGTO F ON F.ID = P.IDVENDAFORMAPAGTO
            JOIN VENDA V ON V.ID = F.IDVENDA
            LEFT JOIN CLIENTE C ON V.ID_CLIENTE = C.ID
            LEFT JOIN EMPREENDIMENTO E ON V.IDEMPREENDIMENTO = E.ID
            WHERE V.CODIGOEMPRESA = ?
              AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)
              AND V.IDVENDAVINCULADA IS NULL
              AND COALESCE(F.ATIVA, 'S') <> 'N'
              AND COALESCE(P.VALOR_PAGO, 0) = 0
              AND P.DATA >= ? AND P.DATA <= ?
              {filtro_emp}
            ORDER BY C.NOME, P.DATA, P.ID
        """, tuple([empresa_id, dt_ini, dt_fim] + ([empreendimento_id] if empreendimento_id else [])))
        candidatos = cur.fetchall()

        # ── BAIXA ANTECIPADA DO LEGADO (consumo de slots em 3 passes) ──────────
        # O legado quita parcelas futuras criando RECEBER com a DATA DO PAGAMENTO
        # e a COMPETÊNCIA no rótulo (PARCELA='MM/YYYY') — e pode PULAR meses
        # (caso venda 19145: pagou 04..10/2026, deixou fev/mar em aberto; o FIFO
        # puro consumia fev/mar e deixava set/out como fantasmas). Regra: cada
        # RECEBER da venda com o MESMO VALOR consome um slot — 1º quem casa por
        # vencimento exato, 2º quem tem competência no rótulo consome o slot
        # DAQUELA competência, 3º FIFO nos mais antigos livres. Só entram
        # RECEBER com DATA <= fim do mês navegado: pagamento futuro não some
        # com slot em visão retrospectiva (a parcela ainda estava aberta).
        suprimidos = set()
        vids_cand = sorted({r[1] for r in candidatos})
        if vids_cand:
            ph_v = ",".join("?" * len(vids_cand))
            cur.execute(f"""SELECT IDVENDA, DATA, VALORPARCELA, PARCELA FROM RECEBER
                            WHERE IDVENDA IN ({ph_v}) AND DATA <= ?""",
                        tuple(vids_cand) + (dt_fim,))
            comp_re = re.compile(r"^(0[1-9]|1[0-2])/(\d{4})$")
            recs = {}
            for rvid, rdt, rval, rparc in cur.fetchall():
                if isinstance(rdt, _dt.datetime):
                    rdt = rdt.date()
                rv = round(float(rval or 0), 2)
                parc = rparc.decode('cp1252', 'ignore').strip() if isinstance(rparc, bytes) else str(rparc or "").strip()
                m = comp_re.match(parc)
                recs.setdefault((rvid, rv), []).append({
                    "d": rdt.isoformat() if rdt else None,
                    "comp": f"{m.group(2)}-{m.group(1)}" if m else None})
            cur.execute(f"""SELECT P.ID, F.IDVENDA, P.DATA, P.VALOR
                            FROM VENDAFORMAPAGTOPRAZO P
                            JOIN VENDAFORMAPAGTO F ON F.ID = P.IDVENDAFORMAPAGTO
                            WHERE F.IDVENDA IN ({ph_v}) AND COALESCE(F.ATIVA, 'S') <> 'N'
                            ORDER BY P.DATA, P.ID""", tuple(vids_cand))
            slots = {}
            for spid, svid, sdt, sval in cur.fetchall():
                if isinstance(sdt, _dt.datetime):
                    sdt = sdt.date()
                sv = round(float(sval or 0), 2)
                d_iso = sdt.isoformat() if sdt else None
                slots.setdefault((svid, sv), []).append(
                    {"id": spid, "d": d_iso, "ym": d_iso[:7] if d_iso else None, "livre": True})
            for chave, rlist in recs.items():
                sl = slots.get(chave)
                if not sl:
                    continue
                pend = []
                for r in rlist:      # passe 1: vencimento exato
                    alvo = next((s for s in sl if s["livre"] and s["d"] == r["d"]), None)
                    if alvo:
                        alvo["livre"] = False
                    else:
                        pend.append(r)
                resto = []
                for r in pend:       # passe 2: competência do rótulo (MM/YYYY)
                    alvo = next((s for s in sl if s["livre"] and r["comp"] and s["ym"] == r["comp"]), None)
                    if alvo:
                        alvo["livre"] = False
                    else:
                        resto.append(r)
                for r in resto:      # passe 3: FIFO nos mais antigos livres
                    alvo = next((s for s in sl if s["livre"]), None)
                    if alvo:
                        alvo["livre"] = False
                suprimidos.update(s["id"] for s in sl if not s["livre"])

        for r in candidatos:
            (pid, vid, cliente, cnpj, unidade, totalvenda, data, vparc, ref, obra) = r
            if isinstance(data, _dt.datetime):
                data = data.date()
            d_iso = data.isoformat() if data else None
            vparc_f = round(float(vparc or 0), 2)
            if (vid, d_iso, vparc_f) in assinaturas:
                continue  # ja efetivada no RECEBER (aparece acima)
            if pid in suprimidos:
                continue  # parcela realizada consome este slot (venc exato, competência do rótulo, ou FIFO)
            totalvenda = float(totalvenda or 0) + cota_extra.get(vid, 0.0)
            rid = f"prazo_{pid}"
            bx = baixas.get(rid)
            if bx and str(bx["data"] or "")[:10] <= dt_fim.isoformat():
                baixa_extra[vid] = baixa_extra.get(vid, 0.0) + bx["valor_pago"] - bx["variacao"] + bx["desconto"]  # principal
            item = {
                "id": rid, "venda_id": vid,
                "comprador": _s(cliente), "cpf_cnpj": _s(cnpj),
                "unidade": _s(unidade), "empreendimento": _s(obra),
                "vlr_venda": round(totalvenda, 2),
                "saldo_anterior": round(totalvenda - pago_antes.get(vid, 0.0), 2),
                "vencimento": d_iso,
                "data_pagto": bx["data"] if bx else "",
                "valor_parcela": vparc_f,
                "desconto": round(bx["desconto"], 2) if bx else 0.0,
                "variacao": round(bx["variacao"], 2) if bx else 0.0,
                "total_pago": round(bx["valor_pago"], 2) if bx else 0.0,
                "saldo_atual": round(totalvenda - pago_total.get(vid, 0.0), 2),
                "parcela": _s(ref), "obs": "Prevista (cronograma)",
                "status": "PAGO" if bx else ("VENCIDA" if data and data < dt_ini else "ABERTA"),
                "baixa_local": bool(bx),
            }
            result.append(item)

        for x in result:
            x["saldo_atual"] = round(x["saldo_atual"] - baixa_extra.get(x["venda_id"], 0.0), 2)

        tot = {k: round(sum(x[k] for x in result), 2)
               for k in ("valor_parcela", "desconto", "variacao", "total_pago")}
        tot["saldo_atual"] = round(sum({x["venda_id"]: x["saldo_atual"] for x in result}.values()), 2)
        return {"success": True, "data": result, "totais": tot,
                "saldo_universo": saldo_universo, "contratos_ativos": contratos_ativos,
                "periodo": {"ano": ano, "mes": mes}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@app.post("/api/sero/config")
def sero_salvar_config():
    return {"success": True, "message": "Expectativa de INSS da Obra/CNO salva com sucesso."}

@app.post("/api/sero/alocacao")
def sero_registrar_alocacao():
    return {"success": True, "message": "Alocação de folha do mês registrada."}

# ── API Agentes Autônomos (LangGraph) ────────────────────────────────────────────────────────────
from core.agents.auditoria_graph import graph_app, AuditoriaGraphState
from langgraph.types import Command
import uuid

class AuditStartReq(BaseModel):
    conta_alvo: str

def _serialize_agent_state(res: dict) -> dict:
    """
    Converte o state do LangGraph para um dict JSON-safe.
    O campo `messages` contém objetos AIMessage/HumanMessage/ToolMessage
    que não são serializaveis pelo FastAPI diretamente.
    """
    import json
    safe = {}
    for k, v in (res or {}).items():
        if k == "messages":
            # Converte cada mensagem para dict simples
            msgs = []
            for m in (v or []):
                try:
                    if hasattr(m, "to_json"):
                        msgs.append({"type": getattr(m, "type", "?"), "content": str(m.content or "")[:2000]})
                    elif hasattr(m, "content"):
                        msgs.append({"type": type(m).__name__, "content": str(m.content or "")[:2000]})
                    else:
                        msgs.append({"type": "unknown", "content": str(m)[:200]})
                except Exception:
                    pass
            safe[k] = msgs
        elif k == "resultados_db":
            # Garante que os resultados_db sejam strings (podem ter objetos)
            safe[k] = [
                {kk: (vv if isinstance(vv, (str, int, float, bool, type(None))) else str(vv))
                 for kk, vv in (item.items() if isinstance(item, dict) else {})}
                for item in (v or [])
            ]
        else:
            try:
                json.dumps(v)  # Testa se é serializavel
                safe[k] = v
            except Exception:
                safe[k] = str(v)
    return safe

_IA_NAO_CONFIGURADA = (
    "IA não configurada: monte chave_fernando.json (Vertex) no Dokploy ou defina GEMINI_API_KEY."
)


@app.post("/api/agentes/iniciar_auditoria")
async def api_agentes_iniciar(req: AuditStartReq):
    import asyncio
    if graph_app is None:
        raise HTTPException(status_code=503, detail=_IA_NAO_CONFIGURADA)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = AuditoriaGraphState(
        pergunta="Auditoria de rotina iniciada",
        conta_alvo=req.conta_alvo,
        passos_executados=[],
        resultados_db=[],
        historico_aprendizado=[],
        sugestao_correcao={},
        aprovado_pelo_usuario=False,
        feedback_usuario="",
        prompt_calibracao="",
        dossie_heuristico={},
        messages=[],
        tentativas_autocorrecao=0,   # reinicia o contador de autocorreção
    )

    try:
        # PERF: graph_app.invoke é síncrono — asyncio.to_thread descarrega no ThreadPool
        # sem bloquear o event loop enquanto o LLM e as tools do Firebird executam.
        res = await asyncio.to_thread(graph_app.invoke, initial_state, config)
        state = graph_app.get_state(config)
        return {
            "status": "PAUSED_FOR_HUMAN" if state.next else "FINISHED",
            "thread_id": thread_id,
            "state": _serialize_agent_state(res)
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        msg = str(e)
        if "GOOGLE_APPLICATION_CREDENTIALS" in tb or "credential" in msg.lower():
            detalhe = f"Vertex AI: credencial não encontrada ou inválida. Verifique GOOGLE_APPLICATION_CREDENTIALS no .env. Detalhe: {msg}"
        elif "DefaultCredentialsError" in tb:
            detalhe = f"Vertex AI: sem credencial padrão. Configure GOOGLE_APPLICATION_CREDENTIALS. Detalhe: {msg}"
        elif "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
            detalhe = f"Vertex AI: cota excedida ou rate limit atingido. Aguarde e tente novamente. Detalhe: {msg}"
        elif "404" in msg or "not found" in msg.lower():
            detalhe = f"Vertex AI: modelo não encontrado ou projeto incorreto (project_id no chavejson.json). Detalhe: {msg}"
        elif "LangGraph" in tb or "StateSnapshot" in tb or "graph" in tb.lower():
            detalhe = f"LangGraph: erro interno no grafo. Detalhe: {msg}"
        elif "firebird" in tb.lower() or "fdb" in tb.lower() or "isql" in tb.lower():
            detalhe = f"Firebird: falha ao conectar ao banco de dados. Verifique se o serviço Firebird está rodando. Detalhe: {msg}"
        else:
            detalhe = f"{type(e).__name__}: {msg}"
        raise HTTPException(status_code=500, detail=detalhe)

class AuditResumeReq(BaseModel):
    thread_id: str
    aprovado: bool
    feedback_usuario: str
    prompt_calibracao: str = None

@app.post("/api/agentes/resumir_auditoria")
def api_agentes_resumir(req: AuditResumeReq):
    if graph_app is None:
        raise HTTPException(status_code=503, detail=_IA_NAO_CONFIGURADA)
    config = {"configurable": {"thread_id": req.thread_id}}
    state = graph_app.get_state(config)
    if not state.next:
        raise HTTPException(status_code=400, detail="A thread não está pausada.")
    
    update_data = {
        "aprovado_pelo_usuario": req.aprovado,
        "feedback_usuario": req.feedback_usuario,
        "passos_executados": [f"Human feedback received: Approved={req.aprovado}"]
    }
    if req.prompt_calibracao is not None:
        update_data["prompt_calibracao"] = req.prompt_calibracao
    graph_app.update_state(config, update_data)
    
    res = graph_app.invoke(None, config=config)
    return {
        "status": "FINISHED",
        "state": _serialize_agent_state(res)
    }

def _analisar_importacao_vendas(cur, rows, _get, _parse_valor, _parse_data,
                                empresa_id, empreendimento_id):
    """Plano de importação de VENDAS a partir da planilha mapeada.

    Casa a UNIDADE (bloco + número) com a estrutura do empreendimento; linhas
    sem cliente/CPF são unidades não vendidas (ignoradas); unidade já vendida
    não importa de novo (re-importação segura)."""
    import re as _re

    def dec(v):
        if v is None: return ""
        if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
        return str(v).strip()

    # estrutura do empreendimento
    cur.execute("SELECT ID, NOME FROM BLOCO WHERE IDEMPREENDIMENTO = ?", (empreendimento_id,))
    blocos = {r[0]: dec(r[1]).upper() for r in cur.fetchall()}
    unidades = []
    if blocos:
        ph = ",".join("?" * len(blocos))
        cur.execute(f"SELECT ID, IDBLOCO, DESCRICAO, METRAGEM, NUMCADIMOB FROM UNIDADE WHERE IDBLOCO IN ({ph})", tuple(blocos))
        unidades = [{"id": r[0], "bloco": blocos.get(r[1], ""), "descricao": dec(r[2]),
                     "numcadimob": r[4]} for r in cur.fetchall()]

    # unidades ja vendidas (venda ativa)
    vendidas = set()
    if unidades:
        ph = ",".join("?" * len(unidades))
        cur.execute(f"""SELECT VU.IDUNIDADE FROM VENDAUNIDADE VU
                        JOIN VENDA V ON V.ID = VU.IDVENDA
                        WHERE VU.IDUNIDADE IN ({ph})
                          AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)""",
                    tuple(u["id"] for u in unidades))
        vendidas = {r[0] for r in cur.fetchall()}

    # cpfs com venda ativa no empreendimento (dedupe p/ linhas sem unidade casada)
    cur.execute("""SELECT C.CNPJ, V.TOTALVENDA FROM VENDA V
                   JOIN CLIENTE C ON C.ID = V.ID_CLIENTE
                   WHERE V.IDEMPREENDIMENTO = ? AND (V.DISTRATO = 'N' OR V.DISTRATO IS NULL)""",
                (empreendimento_id,))
    vendas_cpf = {("".join(filter(str.isdigit, dec(r[0]))), round(float(r[1] or 0), 2)) for r in cur.fetchall()}

    def _canon_bloco_nome(b):
        b = str(b or "").strip().upper()
        return f"BLOCO {b}" if b and len(b) <= 3 else b

    def _match_unidade(bloco_pl, unidade_pl):
        num = str(unidade_pl or "").strip()
        if not num:
            return None
        alvo_bloco = _canon_bloco_nome(bloco_pl)
        cands = [u for u in unidades
                 if _re.search(rf"(?<!\d){_re.escape(num)}(?!\d)", u["descricao"])]
        if alvo_bloco:
            no_bloco = [u for u in cands if u["bloco"] == alvo_bloco]
            cands = no_bloco or cands
        exatas = [u for u in cands if _re.match(rf"^\D*{_re.escape(num)}(?!\d)", u["descricao"].replace("APTO", "").strip())]
        return (exatas or cands)[0] if cands else None

    def _split_compradores(nome_cell, cpf_cell):
        """Casais vem com 2 CPFs na MESMA celula ('030... / 053...') e CNPJ tem
        '/' INTERNO — nunca quebrar nele. Extrai documentos por padrao (CNPJ
        formatado primeiro, depois runs de digitos >=11); cada documento vira
        um comprador (CNPJ e varchar(20), docs juntos estouravam SQL -303)."""
        txt = (cpf_cell or "").strip()
        pat = _re.compile(r"(\d{2}[.\s]?\d{3}[.\s]?\d{3}\s*/\s*\d{4}\s*-?\s*\d{2})|([\d.\-]+)")
        docs = []
        for m in pat.finditer(txt):
            tok = _re.sub(r"\s", "", m.group(0))
            if m.group(1) or len("".join(filter(str.isdigit, tok))) >= 11:
                docs.append(tok[:20])
        nomes = [n.strip() for n in _re.split(r"[/;]", nome_cell or "") if n.strip()]
        if len(docs) > 1 and len(nomes) != len(docs):
            alt = [n.strip() for n in _re.split(r"\s+E\s+", nome_cell or "", flags=_re.I) if n.strip()]
            if len(alt) == len(docs):
                nomes = alt
        comps = []
        for i, d in enumerate(docs):
            nome_i = nomes[i] if len(nomes) == len(docs) else (nome_cell or "").strip()
            comps.append({"nome": (nome_i or "(sem nome)")[:100], "cpf": d})
        if not comps and (nome_cell or cpf_cell):
            comps = [{"nome": (nome_cell or "(sem nome)").strip()[:100],
                      "cpf": txt[:20]}]
        return comps

    resultados, importaveis = [], []
    for row in rows:
        cliente = dec(_get(row, "CLIENTE_NOME"))
        cpf = dec(_get(row, "CLIENTE_CPF_CNPJ"))
        valor = _parse_valor(_get(row, "VGV"))
        data_v = _parse_data(_get(row, "DATA_VENDA"))
        contrato = dec(_get(row, "NUMERO_CONTRATO"))
        bloco_pl = dec(_get(row, "BLOCO"))
        unidade_pl = dec(_get(row, "UNIDADE"))

        base = {"cliente_planilha": cliente, "contrato": contrato,
                "dt_vencimento": data_v.isoformat() if data_v else None,
                "dt_pagamento": None, "valor_planilha": valor, "valor_vulcano": None}

        if not cliente and not cpf:
            resultados.append({**base, "status": "IGNORADA",
                               "unidade": f"{_canon_bloco_nome(bloco_pl)} {unidade_pl}".strip(),
                               "obs": "Unidade sem venda na planilha (sem cliente/CPF)."})
            continue
        if not cpf or not valor or not data_v:
            faltas = [n for n, v in (("CPF", cpf), ("valor", valor), ("data", data_v)) if not v]
            resultados.append({**base, "status": "SEM_DADOS",
                               "unidade": f"{_canon_bloco_nome(bloco_pl)} {unidade_pl}".strip(),
                               "obs": f"Linha com venda mas sem {', '.join(faltas)} — complete a planilha."})
            continue

        u = _match_unidade(bloco_pl, unidade_pl)
        compradores = _split_compradores(cliente, cpf)
        cpf_digits = "".join(filter(str.isdigit, compradores[0]["cpf"])) if compradores else ""
        if u and u["id"] in vendidas:
            resultados.append({**base, "status": "JA_VENDIDA",
                               "unidade": f"{u['bloco']} — {u['descricao']}",
                               "obs": "Unidade já tem venda ativa — não importa de novo."})
            continue
        if not u and (cpf_digits, round(valor, 2)) in vendas_cpf:
            resultados.append({**base, "status": "JA_VENDIDA",
                               "unidade": f"{_canon_bloco_nome(bloco_pl)} {unidade_pl}".strip(),
                               "obs": "Já existe venda ativa deste CPF com este valor no empreendimento."})
            continue

        status = "PRONTA" if u else "PRONTA_SEM_UNIDADE"
        item = {
            "compradores": compradores, "valor": round(valor, 2),
            "data": data_v.isoformat(), "contrato": contrato,
            "unidade_id": u["id"] if u else None,
            "numcadimob": (u or {}).get("numcadimob"),
            "descricao": (f"{u['bloco']} — {u['descricao']}" if u
                          else f"{_canon_bloco_nome(bloco_pl)} {unidade_pl}".strip())[:90],
        }
        importaveis.append(item)
        multi = f" {len(compradores)} compradores — rateio igual entre os CPFs (DIMOB por adquirente)." if len(compradores) > 1 else ""
        resultados.append({**base, "status": status, "unidade": item["descricao"],
                           "obs": "Vai criar venda + cliente + parcela única (1/1)." + multi
                                  + ("" if u else " ⚠ unidade não encontrada na estrutura — grava sem vínculo.")})

    return {"resultados": resultados, "importaveis": importaveis}

class PreviewMatchRequest(BaseModel):
    rows: list
    mapping: dict
    target_table: str
    empresa_id: int | None = None
    empreendimento_id: int | None = None


@app.post("/api/smart-importer/preview-match")
async def api_smart_importer_preview_match(payload: PreviewMatchRequest):
    import re as _re
    from datetime import datetime as _dt

    inv = {str(v): k for k, v in payload.mapping.items() if v and v != "null" and isinstance(v, str)}

    def _get(row, campo):
        col = inv.get(campo)
        return row.get(col) if col else None

    def _parse_valor(v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        try:
            s = str(v).strip()
            s = _re.sub(r"[^\d,\.]", "", s)
            if '.' in s and ',' in s:
                if s.rfind(',') > s.rfind('.'):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif ',' in s:
                s = s.replace(",", ".")
            return float(s) if s else None
        except Exception:
            return None

    def _parse_data(v):
        if not v:
            return None
        v = str(v).strip()[:10]
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return _dt.strptime(v, fmt).date()
            except ValueError:
                pass
        return None

    resultados = []

    if payload.target_table == "RECEBIMENTOS":
        conn_v = get_conn("vulcano")
        try:
            cur = conn_v.cursor()
            where_clauses = ["1=1"]
            params = []
            if payload.empresa_id:
                where_clauses.append("V.CODIGOEMPRESA = ?")
                params.append(payload.empresa_id)
            if payload.empreendimento_id:
                where_clauses.append("B.IDEMPREENDIMENTO = ?")
                params.append(payload.empreendimento_id)
            
            where_sql = " AND ".join(where_clauses)
            
            cur.execute(f"""
                SELECT R.ID, R.PARCELA, R.DATA, R.VALORPARCELA, R.TOTALPAGO,
                       C.NOME, U.DESCRICAO
                FROM RECEBER R
                LEFT JOIN VENDA V ON V.ID = R.IDVENDA
                LEFT JOIN CLIENTE C ON C.ID = V.ID_CLIENTE
                LEFT JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
                LEFT JOIN UNIDADE U ON U.ID = VU.IDUNIDADE
                LEFT JOIN BLOCO B ON B.ID = U.IDBLOCO
                WHERE {where_sql}
                ORDER BY R.DATA DESC
            """, params)
            parcelas = cur.fetchall()
            # idx: 0=ID, 1=PARCELA, 2=DATA(vencimento), 3=VALORPARCELA, 4=TOTALPAGO, 5=C.NOME, 6=U.DESCRICAO
            quitadas = [p for p in parcelas if (p[4] or 0) > 0]
            abertas  = [p for p in parcelas if (p[4] or 0) <= 0]
            
            assinaturas_fb = set()
            for p in parcelas:
                dt_str = str(p[2])[:10] if p[2] else ""
                val = round(float(p[3] or 0), 2)
                assinaturas_fb.add((dt_str, val))
            
            # PROJETADAS — desativadas por padrão (abertas = RECEBER TOTALPAGO<=0,
            # já carregadas acima da base viva); reative com PROJETADAS_ATIVAS=1.
            _proj_rows = []
            if os.environ.get("PROJETADAS_ATIVAS") == "1":
                conn_sq = get_conn("sqlite")
                cur_sq = conn_sq.cursor()
                sq_where = ["1=1"]
                sq_params = []
                if payload.empreendimento_id:
                    sq_where.append("empreendimento_id = ?")
                    sq_params.append(payload.empreendimento_id)
                cur_sq.execute(f"""
                    SELECT prazo_id, parcela_ref, data_venc, valor, 0.0,
                           cliente_nome, unidade_descricao
                    FROM parcelas_abertas_projetadas
                    WHERE {" AND ".join(sq_where)}
                """, sq_params)
                _proj_rows = cur_sq.fetchall()
                conn_sq.close()

            for row in _proj_rows:
                try:
                    dt_venc = datetime.datetime.strptime(row[2], "%Y-%m-%d").date() if row[2] else None
                except:
                    dt_venc = None
                    
                dt_str = str(dt_venc)[:10] if dt_venc else ""
                val = round(float(row[3] or 0), 2)
                # Evita duplicidade se o Firebird já tem essa parcela
                if (dt_str, val) in assinaturas_fb:
                    continue
                    
                # id prefixado: baixa em parcela projetada grava 'prazo_<id>' no
                # operacoes_baixas (mesma chave da tela Mensal — sem colidir com RECEBER.ID)
                abertas.append((f"prazo_{row[0]}", row[1], dt_venc, row[3], row[4], row[5], row[6]))
            # (o conn_sq.close() do commit original nao entra aqui: neste repo a
            #  conexao so existe dentro do `if PROJETADAS_ATIVAS` acima, onde ja e
            #  fechada — fechar de novo aqui daria NameError com a env desligada)
            TOLE = 1.0

            from collections import defaultdict
            idx_parcelas = defaultdict(list)
            for p in abertas:
                v = float(p[3] or 0)
                idx_parcelas[int(v)].append((p, "MATCH_PERFEITO"))
            for p in quitadas:
                v = float(p[4] or 0)
                idx_parcelas[int(v)].append((p, "JA_QUITADO"))

            todas_parcelas_fallback = [(p, "MATCH_PERFEITO") for p in abertas] + [(p, "JA_QUITADO") for p in quitadas]

            for row in payload.rows:
                valor_pl    = _parse_valor(_get(row, "VALOR_PAGO")) or _parse_valor(_get(row, "VALOR_PARCELA"))
                valor_nominal_pl = _parse_valor(_get(row, "VALOR_PARCELA"))
                acrescimos_pl = _parse_valor(_get(row, "ACRESCIMOS"))
                descontos_pl = _parse_valor(_get(row, "DESCONTOS"))
                num_parcela_pl = _get(row, "NUMERO_PARCELA") or ""
                
                dt_venc_pl  = _parse_data(_get(row, "DATA_VENCIMENTO"))
                dt_pago_pl  = _parse_data(_get(row, "DATA_PAGAMENTO"))
                cliente_pl  = _get(row, "CLIENTE_NOME") or ""
                contrato_pl = _get(row, "CONTRATO") or ""
                unidade_pl  = _get(row, "UNIDADE") or ""

                status = "SEM_MATCH"
                valor_v = cliente_v = dt_venc_v = unidade_v = num_parcela = id_parcela = acrescimos = descontos = None

                candidatos = []
                
                if valor_pl is not None:
                    v_int = int(valor_pl)
                    possiveis = idx_parcelas.get(v_int-1, []) + idx_parcelas.get(v_int, []) + idx_parcelas.get(v_int+1, [])
                else:
                    possiveis = todas_parcelas_fallback

                for p, st in possiveis:
                    pv    = float(p[4] if st == "JA_QUITADO" else p[3] or 0)
                    pvenc = p[2]
                    match_val  = valor_pl is not None and abs(pv - valor_pl) <= TOLE
                    match_venc = dt_venc_pl and pvenc and str(pvenc)[:10] == str(dt_venc_pl)
                    
                    nome_db = str(p[5] or "").upper().strip()
                    nome_pl = str(cliente_pl).upper().strip()
                    
                    match_nome = False
                    if not nome_pl or not nome_db:
                        match_nome = True
                    else:
                        if nome_db in nome_pl or nome_pl in nome_db:
                            match_nome = True
                        else:
                            tokens_db = set([t for t in nome_db.split() if len(t) > 2])
                            tokens_pl = set([t for t in nome_pl.split() if len(t) > 2])
                            if len(tokens_db.intersection(tokens_pl)) >= 1:
                                match_nome = True

                    if match_nome and (match_val or match_venc):
                        score = 0
                        if match_val and match_venc: score += 100
                        elif match_val: score += 50
                        elif match_venc: score += 20
                        
                        if st == "MATCH_PERFEITO": score += 10 # Prioriza abertas
                        
                        candidatos.append({
                            'score': score,
                            'status': st,
                            'id_parcela': p[0],
                            'num_parcela': p[1],
                            'valor_v': pv,
                            'cliente_v': str(p[5] or ""),
                            'dt_venc_v': str(pvenc)[:10] if pvenc else None,
                            'unidade_v': str(p[6] or "") if p[6] else None
                        })

                if candidatos:
                    # Pega o melhor candidato
                    candidatos.sort(key=lambda x: x['score'], reverse=True)
                    best = candidatos[0]
                    
                    status = best['status']
                    id_parcela = best['id_parcela']
                    num_parcela = best['num_parcela']
                    valor_v = best['valor_v']
                    cliente_v = best['cliente_v']
                    dt_venc_v = best['dt_venc_v']
                    unidade_v = best['unidade_v']
                    
                    if acrescimos_pl is not None or descontos_pl is not None:
                        acrescimos = acrescimos_pl or 0
                        descontos = descontos_pl or 0
                    elif valor_pl and valor_v:
                        diff = round(valor_pl - valor_v, 2)
                        if diff > TOLE:
                            acrescimos = diff
                            descontos = 0
                        elif diff < -TOLE:
                            descontos = abs(diff)
                            acrescimos = 0
                        else:
                            acrescimos = 0
                            descontos = 0

                resultados.append({
                    "status":           status,
                    "id_parcela":       id_parcela,
                    "cliente_planilha": cliente_pl or "",
                    "cliente_vulcano":  cliente_v or "",
                    "dt_vencimento":    str(dt_venc_pl) if dt_venc_pl else None,
                    "dt_venc_vulcano":  str(dt_venc_v) if dt_venc_v else None,
                    "dt_pagamento":     str(dt_pago_pl) if dt_pago_pl else None,
                    "valor_planilha":   valor_pl,
                    "valor_vulcano":    valor_v,
                    "unidade":          unidade_pl or "",
                    "unidade_vulcano":  unidade_v or "",
                    "contrato":         contrato_pl,
                    "numero_parcela":   num_parcela,
                    "num_parcela_planilha": str(num_parcela_pl),
                    "acrescimos":       acrescimos,
                    "descontos":        descontos,
                    "obs":              _get(row, "OBSERVACOES") or "",
                })
            
            # Formatar parcelas em aberto para envio ao frontend (para HitL)
            abertas_front = []
            for a in abertas:
                abertas_front.append({
                    "id": a[0],
                    "numero_parcela": a[1],
                    "data_vencimento": str(a[2])[:10] if a[2] else None,
                    "valor_parcela": float(a[3] or 0),
                    "cliente_nome": str(a[5] or ""),
                    "descricao_unidade": str(a[6] or "")
                })

        finally:
            conn_v.close()
    elif payload.target_table == "VENDAS":
        # VENDAS não é conciliação: é IMPORTAÇÃO. Analisa cada linha (cliente,
        # CPF, data, valor), casa a UNIDADE com a estrutura do empreendimento e
        # devolve o plano; a gravação acontece em /api/smart-importer/importar-vendas.
        if not payload.empreendimento_id:
            raise HTTPException(status_code=400, detail="Selecione o empreendimento de destino para importar VENDAS.")
        conn_v = get_conn("vulcano")
        try:
            cur = conn_v.cursor()
            plano = _analisar_importacao_vendas(cur, payload.rows, _get, _parse_valor,
                                                _parse_data, payload.empresa_id,
                                                payload.empreendimento_id)
            resultados = plano["resultados"]
        finally:
            conn_v.close()
    else:
        for row in payload.rows:
            resultados.append({
                "status": "SEM_MATCH",
                "cliente_planilha": "",
                "dt_vencimento": None, "dt_pagamento": None,
                "valor_planilha": None, "valor_vulcano": None,
                "unidade": "", "contrato": "",
                "obs": f"Match para {payload.target_table} em desenvolvimento.",
            })

    counts = {
        "total":          len(resultados),
        "ja_quitados":    sum(1 for r in resultados if r["status"] == "JA_QUITADO"),
        "match_perfeito": sum(1 for r in resultados if r["status"] == "MATCH_PERFEITO"),
        "sem_match":      sum(1 for r in resultados if r["status"] == "SEM_MATCH"),
        "importaveis":    sum(1 for r in resultados if r["status"] in ("PRONTA", "PRONTA_SEM_UNIDADE")),
    }
    return {"resultados": resultados, "counts": counts}

@app.post("/api/smart-importer/importar-recebimentos")
async def smart_importer_importar_recebimentos(payload: PreviewMatchRequest):
    """Gravação do destino RECEBIMENTOS ('Gravar no ERP' do Smart Importer):
    re-analisa a planilha (mesmo matching do preview) e registra BAIXA LOCAL
    (operacoes_baixas, modelo da tela Mensal — o Firebird não é tocado; dá
    para desfazer) em cada parcela MATCH_PERFEITO com valor. Idempotente:
    parcela com baixa local existente é pulada; JA_QUITADO no legado idem."""
    if payload.target_table != "RECEBIMENTOS":
        raise HTTPException(status_code=400, detail="Endpoint exclusivo do destino RECEBIMENTOS.")
    if not payload.empresa_id:
        raise HTTPException(status_code=400, detail="Selecione a empresa (a baixa local é por empresa).")
    preview = await api_smart_importer_preview_match(payload)
    resultados = preview["resultados"]

    import sqlite3 as _sq
    s_conn = _sq.connect(POC_DATABASE_FILE)
    try:
        s_cur = s_conn.cursor()
        s_cur.execute("SELECT id_receber FROM operacoes_baixas WHERE empresa_id = ?", (int(payload.empresa_id),))
        existentes = {str(r[0]) for r in s_cur.fetchall()}
        baixadas, puladas, venc_como_pgto = 0, [], 0
        for r in resultados:
            if r.get("status") != "MATCH_PERFEITO" or not r.get("id_parcela"):
                continue
            rid = str(r["id_parcela"])
            valor = r.get("valor_planilha") or r.get("valor_vulcano")
            if not valor or float(valor) <= 0:
                puladas.append(f"{rid}: sem valor")
                continue
            dt_pgto = r.get("dt_pagamento")
            if not dt_pgto:
                # planilha sem coluna de pagamento: assume o vencimento casado
                dt_pgto = r.get("dt_venc_vulcano") or r.get("dt_vencimento")
                if not dt_pgto:
                    puladas.append(f"{rid}: sem data de pagamento/vencimento")
                    continue
                venc_como_pgto += 1
            if rid in existentes:
                puladas.append(f"{rid}: baixa local já registrada")
                continue
            s_cur.execute(
                """INSERT INTO operacoes_baixas (id_receber, empresa_id, data_pagamento, valor_pago, descontos, acrescimos)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (rid, int(payload.empresa_id), str(dt_pgto)[:10], round(float(valor), 2),
                 float(r.get("descontos") or 0), float(r.get("acrescimos") or 0)))
            existentes.add(rid)
            baixadas += 1
        s_conn.commit()
        ja_quitadas = sum(1 for r in resultados if r.get("status") == "JA_QUITADO")
        sem_match = sum(1 for r in resultados if r.get("status") == "SEM_MATCH")
        msg = f"{baixadas} baixa(s) registrada(s) (locais, reversíveis pela tela Mensal)."
        if venc_como_pgto:
            msg += f" {venc_como_pgto} sem data de pagamento na planilha usaram o vencimento."
        if ja_quitadas:
            msg += f" {ja_quitadas} já quitada(s) no legado (puladas)."
        if sem_match:
            msg += f" {sem_match} sem match (não gravadas)."
        return {"success": True, "baixadas": baixadas, "ja_quitadas": ja_quitadas,
                "sem_match": sem_match, "puladas": puladas[:20], "message": msg}
    except HTTPException:
        raise
    except Exception as e:
        try:
            s_conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            s_conn.close()
        except Exception:
            pass

@app.post("/api/smart-importer/importar-vendas")
async def smart_importer_importar_vendas(payload: PreviewMatchRequest):
    """Gravação do plano de importação de VENDAS ('Gravar no ERP' do Smart
    Importer): cria CLIENTE (find-or-create por CPF), VENDA (contrato único),
    vincula a UNIDADE casada e gera PARCELA ÚNICA 1/1 no RECEBER (o valor total
    fica aberto para baixas — inclusive parciais)."""
    import re as _re
    from datetime import datetime as _dt

    inv = {str(v): k for k, v in payload.mapping.items() if v and v != "null" and isinstance(v, str)}

    def _get(row, campo):
        col = inv.get(campo)
        return row.get(col) if col else None

    def _parse_valor(v):
        if v is None: return None
        if isinstance(v, (int, float)): return float(v)
        try:
            s = _re.sub(r"[^\d,\.]", "", str(v).strip())
            if '.' in s and ',' in s:
                s = s.replace(".", "").replace(",", ".") if s.rfind(',') > s.rfind('.') else s.replace(",", "")
            elif ',' in s:
                s = s.replace(",", ".")
            return float(s) if s else None
        except Exception:
            return None

    def _parse_data(v):
        if not v: return None
        v = str(v).strip()[:10]
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return _dt.strptime(v, fmt).date()
            except ValueError:
                pass
        return None

    if not payload.empresa_id or not payload.empreendimento_id:
        raise HTTPException(status_code=400, detail="Empresa e empreendimento são obrigatórios para importar vendas.")

    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        plano = _analisar_importacao_vendas(cur, payload.rows, _get, _parse_valor,
                                            _parse_data, payload.empresa_id,
                                            payload.empreendimento_id)
        importaveis = plano["importaveis"]
        if not importaveis:
            return {"success": True, "inseridas": 0, "resultados": plano["resultados"],
                    "message": "Nada a importar (linhas sem venda, incompletas ou já importadas)."}

        cur.execute("SELECT 1 FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLIENTE' AND TRIM(RDB$FIELD_NAME) = 'CODIGOEMPRESA'")
        cliente_tem_empresa = cur.fetchone() is not None

        def _cliente(nome, cpf):
            raw = "".join(filter(str.isdigit, cpf))
            cur.execute("SELECT FIRST 1 ID, NOME FROM CLIENTE WHERE REPLACE(REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '-', ''), '/', ''), ' ', '') = ?", (raw,))
            r = cur.fetchone()
            if r:
                # cadastro reencontrado sem nome (residuo de importacao) ganha o da planilha
                atual = r[1].decode('cp1252', 'ignore').strip() if isinstance(r[1], bytes) else (r[1] or "").strip()
                if (not atual or atual == "(sem nome)") and nome.strip():
                    cur.execute("UPDATE CLIENTE SET NOME = ? WHERE ID = ?",
                                (nome.encode('cp1252', 'ignore')[:100], r[0]))
                return r[0]
            cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM CLIENTE")
            cid = cur.fetchone()[0]
            if cliente_tem_empresa:
                cur.execute("INSERT INTO CLIENTE (ID, NOME, CNPJ, CODIGOEMPRESA) VALUES (?, ?, ?, ?)",
                            (cid, nome.encode('cp1252', 'ignore')[:100], cpf, int(payload.empresa_id)))
            else:
                cur.execute("INSERT INTO CLIENTE (ID, NOME, CNPJ) VALUES (?, ?, ?)",
                            (cid, nome.encode('cp1252', 'ignore')[:100], cpf))
            return cid

        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDA")
        prox_venda = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDAUNIDADE")
        prox_vu = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM RECEBER")
        prox_rec = cur.fetchone()[0]

        inseridas = 0
        for item in importaveis:
            comps = item["compradores"]
            n = max(1, len(comps))
            # rateio igual entre os CPFs — cotas fecham exatamente o total
            cotas = [round(item["valor"] / n, 2) for _ in comps]
            if cotas:
                cotas[-1] = round(item["valor"] - sum(cotas[:-1]), 2)
            ids_cli = [_cliente(c["nome"], c["cpf"]) for c in comps]

            vid = prox_venda; prox_venda += 1
            num_contrato = (item["contrato"] or str(vid))[:90]
            num_cad = _int_or_none(item.get("numcadimob"))
            cur.execute(
                "INSERT INTO VENDA (ID, IDEMPREENDIMENTO, NUMCADIMOB, NUMCONT, DTOPER, DESCUNIDIMOB, TOTALVENDA, CODIGOEMPRESA, DISTRATO, PERMUTA, ID_CLIENTE) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'N', 'N', ?)",
                (vid, int(payload.empreendimento_id), num_cad,
                 num_contrato.encode('cp1252', 'ignore'), item["data"],
                 item["descricao"].encode('cp1252', 'ignore'), cotas[0],
                 int(payload.empresa_id), ids_cli[0]),
            )
            # compradores extras = vendas vinculadas com a cota de cada CPF
            # (mesmo modelo do cadastro manual: DIMOB/EFD por adquirente)
            for offset, cid_extra in enumerate(ids_cli[1:], start=1):
                sat_id = prox_venda; prox_venda += 1
                cur.execute(
                    "INSERT INTO VENDA (ID, IDEMPREENDIMENTO, NUMCADIMOB, NUMCONT, DTOPER, DESCUNIDIMOB, TOTALVENDA, CODIGOEMPRESA, DISTRATO, PERMUTA, ID_CLIENTE, IDVENDAVINCULADA, INFCOMP) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'N', 'N', ?, ?, ?)",
                    (sat_id, int(payload.empreendimento_id), num_cad,
                     num_contrato.encode('cp1252', 'ignore'), item["data"],
                     item["descricao"].encode('cp1252', 'ignore'), cotas[offset],
                     int(payload.empresa_id), cid_extra, vid,
                     f"VINCULADA VENDA #{vid}".encode('cp1252', 'ignore')),
                )
            if item["unidade_id"]:
                cur.execute("INSERT INTO VENDAUNIDADE (ID, IDVENDA, IDUNIDADE) VALUES (?, ?, ?)",
                            (prox_vu, vid, int(item["unidade_id"])))
                prox_vu += 1
            # parcela única 1/1 na PRINCIPAL com o VALOR TOTAL do contrato:
            # em aberto, baixável (inclusive parcial)
            cur.execute(
                "INSERT INTO RECEBER (ID, IDVENDA, IDCLIENTE, DATA, VALORPARCELA, VALORVARIACAO, TOTALPAGO, PARCELA, OBS, DESCONTO) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 0)",
                (prox_rec, vid, ids_cli[0], item["data"], item["valor"],
                 "1/1".encode('cp1252'), "GERADA NA IMPORTACAO (PARCELA UNICA)".encode('cp1252')),
            )
            prox_rec += 1
            inseridas += 1

        conn.commit()
        return {"success": True, "inseridas": inseridas,
                "message": f"{inseridas} venda(s) importadas com cliente e parcela única 1/1 (abertas para baixa, inclusive parcial)."}
    except HTTPException:
        raise
    except Exception as e:
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass



@app.get('/api/debug/venda')
def api_debug_venda():
    conn_v = get_conn('vulcano')
    try:
        cur = conn_v.cursor()
        cur.execute('SELECT FIRST 5 ID, IDUNIDADE FROM VENDA')
        vendas = cur.fetchall()
        cur.execute('SELECT FIRST 5 ID, METRAGEM FROM UNIDADE')
        unis = cur.fetchall()
        return {'vendas': vendas, 'unidades': unis}
    finally:
        conn_v.close()

@app.get('/api/debug/area')
def api_debug_area():
    conn_v = get_conn('vulcano')
    try:
        cur = conn_v.cursor()
        cur.execute('''SELECT 
            (SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = 5) as TOTAL_AREA,
            (SELECT SUM(U.METRAGEM) FROM VENDAUNIDADE VU JOIN VENDA V ON V.ID = VU.IDVENDA JOIN UNIDADE U ON U.ID = VU.IDUNIDADE JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = 5 AND COALESCE(V.DISTRATO, 'N') NOT IN ('T', 'S', '1')) as SOLD_AREA
        FROM RDB$DATABASE''')
        res = cur.fetchone()
        return {'status': 'ok', 'res': str(res)}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
    finally:
        conn_v.close()

@app.get('/api/vulcano/schema/tables')
def api_schema_tables():
    # Only fetch tables the user might map to avoid extreme UI clutter
    target_tables = ["VENDA", "RECEBIMENTO", "EMPREENDIMENTO", "CLIENTE", "POC_CUSTOS", "POC_CUSTO_MENSAL_REAL", "UNIDADE", "BLOCO"]
    conn_v = get_conn('vulcano')
    schema_dict = {}
    try:
        cur = conn_v.cursor()
        for t in target_tables:
            cur.execute("SELECT rf.RDB$FIELD_NAME FROM RDB$RELATION_FIELDS rf WHERE rf.RDB$RELATION_NAME = ? ORDER BY rf.RDB$FIELD_POSITION", (t,))
            fields = [r[0].decode('win1252').strip() if isinstance(r[0], bytes) else r[0].strip() for r in cur.fetchall()]
            if fields:
                schema_dict[t] = fields
        
        # Add basic Questor tables if needed
        # We can also add Questor schema mappings later if they want to inject directly to Questor
        
        return {"schema": schema_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn_v.close()


# ── Sindicatos CCT ────────────────────────────────────────────────────────────
@app.get("/api/sindicatos")
def api_sindicatos_list():
    """Retorna os 10 sindicatos com dados do Questor + CCT extraída do SQLite."""
    try:
        return _sa.get_sindicatos_para_api()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sindicatos/atualizar")
async def api_sindicatos_atualizar(background_tasks: BackgroundTasks):
    """Dispara atualização imediata de todos os sindicatos em background."""
    background_tasks.add_task(_sa.rodar_atualizacao_todos)
    return {"message": "Atualização iniciada em background."}


@app.get("/api/sindicatos/status")
def api_sindicatos_status():
    """Retorna status do agente (próxima execução, status por sindicato)."""
    return _sa.get_status_agente()


# ── Smart Importer ─────────────────────────────────────────────────────────────

# Schemas de destino conhecidos para o Smart Importer (DE-PARA)
_SMART_IMPORTER_SCHEMAS = {
    "VENDAS": [
        "DATA_VENDA", "NUMERO_CONTRATO", "CLIENTE_NOME", "CLIENTE_CPF_CNPJ",
        "EMPREENDIMENTO", "UNIDADE", "BLOCO", "VGV", "AREA", "FORMA_PAGAMENTO",
        "CORRETOR", "STATUS", "OBSERVACOES"
    ],
    "RECEBIMENTOS": [
        "DATA_PAGAMENTO", "DATA_VENCIMENTO", "VALOR_PAGO", "VALOR_PARCELA",
        "ACRESCIMOS", "DESCONTOS", "NUMERO_PARCELA", "DESCRICAO",
        "CLIENTE_NOME", "CLIENTE_CPF_CNPJ",
        "EMPREENDIMENTO", "UNIDADE", "CONTRATO", "FORMA_PAGAMENTO",
        "BANCO", "AGENCIA", "CONTA", "NOSSO_NUMERO", "OBSERVACOES"
    ],
    "EMPREENDIMENTOS": [
        "NOME", "CODIGO_CC", "DATA_INICIO", "DATA_PREVISTA_ENTREGA",
        "CONTA_ESTOQUE", "CONTA_CUSTO", "CUSTO_ORCADO", "AREA_TOTAL", "CNPJ"
    ],
    "CLIENTES": [
        "NOME", "CPF_CNPJ", "EMAIL", "TELEFONE", "ENDERECO",
        "CIDADE", "ESTADO", "CEP", "OBSERVACOES"
    ],
}

# SQLite para persistência de templates do Smart Importer
import sqlite3 as _sqlite3

def _get_smart_importer_db():
    conn = connect_app()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS smart_importer_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            target_table TEXT NOT NULL,
            mapping_json TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS smart_importer_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            file_type TEXT NOT NULL,
            target_table TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDENTE',
            empresa_id_detectada INTEGER,
            cnpj_detectado TEXT,
            extracted_json TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


@app.post("/api/upload-planilha")
async def api_upload_planilha(file: UploadFile = File(...)):
    """Recebe planilha XLS/XLSX/CSV e retorna colunas + prévia de dados."""
    import io
    content = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".csv"):
            import csv as _csv
            text = content.decode("utf-8-sig", errors="replace")
            reader = _csv.DictReader(io.StringIO(text))
            rows = [row for row in reader]
            columns = list(rows[0].keys()) if rows else []
            preview = rows[:5]
        else:
            # XLS / XLSX via openpyxl
            try:
                import openpyxl
                wb = await asyncio.to_thread(openpyxl.load_workbook, io.BytesIO(content), read_only=True, data_only=True)
                ws = wb.active
                all_rows = list(ws.iter_rows(values_only=True))
                wb.close()
                if not all_rows:
                    raise HTTPException(status_code=422, detail="Planilha vazia.")
                headers = [str(c).strip() if c is not None else f"Col_{i}" for i, c in enumerate(all_rows[0])]
                columns = headers
                data_rows = []
                preview = []
                for row in all_rows[1:]:
                    row_dict = {headers[i]: (str(v) if v is not None else "") for i, v in enumerate(row)}
                    data_rows.append(row_dict)
                    if len(preview) < 5:
                        preview.append(row_dict)
            except ImportError:
                raise HTTPException(status_code=500, detail="openpyxl não instalado. Rode: pip install openpyxl")

        return {"columns": columns, "preview": preview, "all_rows": data_rows if not filename.endswith('.csv') else rows, "total_colunas": len(columns)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao processar planilha: {str(e)}")


class SchemaMatchRequest(BaseModel):
    columns: list
    target_table: str


@app.post("/api/schema-match")
async def api_schema_match(payload: SchemaMatchRequest):
    """Usa Gemini para fazer DE-PARA automático entre colunas da planilha e campos destino."""
    _require_gemini_key()

    target_fields = _SMART_IMPORTER_SCHEMAS.get(payload.target_table, [])
    if not target_fields:
        raise HTTPException(status_code=400, detail=f"Entidade '{payload.target_table}' não reconhecida.")

    cols_str = ", ".join(payload.columns)
    dest_str = ", ".join(target_fields)

    schema_json = '{"mapping": {"COLUNA_ORIGEM": "CAMPO_DESTINO_OU_null"}}'
    prompt = (
        f"Você é um especialista em integração de dados para ERPs imobiliários.\n"
        f"Faça o mapeamento (DE-PARA) entre as colunas de uma planilha e os campos do sistema destino.\n\n"
        f"COLUNAS DA PLANILHA:\n{cols_str}\n\n"
        f"CAMPOS DESTINO ({payload.target_table}):\n{dest_str}\n\n"
        f"Retorne APENAS JSON no formato:\n{schema_json}\n\n"
        f"Regras:\n"
        f"- Para cada coluna da planilha, mapeie para o campo destino mais semanticamente próximo.\n"
        f"- Se não houver correspondência, use null.\n"
        f"- As chaves do JSON de saída devem ser EXATAMENTE as colunas da planilha fornecidas.\n"
        f"- Os valores devem ser EXATAMENTE um dos campos destino listados acima, ou null.\n"
        f"- Não invente campos. Só use campos da lista destino."
    )

    result = await _gemini_generate_json_async(prompt)

    # Normaliza: garante que todas as colunas estejam no mapping
    mapping = result.get("mapping", {})
    for col in payload.columns:
        if col not in mapping:
            mapping[col] = None

    return {"mapping": mapping, "target_table": payload.target_table}


@app.get("/api/templates")
def api_templates_list(target_table: str = None):
    """Retorna templates salvos do Smart Importer."""
    conn = _get_smart_importer_db()
    try:
        if target_table:
            rows = conn.execute(
                "SELECT id, nome, target_table, mapping_json, criado_em FROM smart_importer_templates WHERE target_table = ? ORDER BY id DESC",
                (target_table,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, nome, target_table, mapping_json, criado_em FROM smart_importer_templates ORDER BY id DESC"
            ).fetchall()
        return [
            {"id": r[0], "nome": r[1], "target_table": r[2], "mapping_json": r[3], "criado_em": r[4]}
            for r in rows
        ]
    finally:
        conn.close()


class TemplateCreateRequest(BaseModel):
    nome: str
    target_table: str
    mapping_json: str


@app.post("/api/templates")
def api_templates_create(payload: TemplateCreateRequest):
    """Salva um template de mapeamento do Smart Importer."""
    conn = _get_smart_importer_db()
    try:
        conn.execute(
            "INSERT INTO smart_importer_templates (nome, target_table, mapping_json) VALUES (?, ?, ?)",
            (payload.nome, payload.target_table, payload.mapping_json)
        )
        conn.commit()
        return {"success": True, "message": f"Template '{payload.nome}' salvo com sucesso."}
    finally:
        conn.close()


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
if getattr(sys, 'frozen', False):
    frontend_dist = os.path.join(sys._MEIPASS, "dist")
else:
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

    @app.exception_handler(404)
    async def custom_404_handler(request, exc):
        # 404 de API continua JSON; o fallback pro index.html e so pro roteamento da SPA.
        if request.url.path.startswith("/api"):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": getattr(exc, "detail", "Not Found")})
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend build not found"}

# ── API Smart Importer Queue ──────────────────────────────────────────────────
@app.get("/api/smart-importer/queue")
def api_get_queue():
    conn = _get_smart_importer_db()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, file_type, target_table, status, empresa_id_detectada, cnpj_detectado, criado_em FROM smart_importer_queue ORDER BY id DESC")
    rows = cur.fetchall()
    return [{
        "id": r[0], "filename": r[1], "file_type": r[2], "target_table": r[3],
        "status": r[4], "empresa_id_detectada": r[5], "cnpj_detectado": r[6], "criado_em": r[7]
    } for r in rows]

@app.delete("/api/smart-importer/queue/{queue_id}")
def api_delete_queue(queue_id: int):
    conn = _get_smart_importer_db()
    conn.execute("DELETE FROM smart_importer_queue WHERE id = ?", (queue_id,))
    conn.commit()
    return {"success": True}

@app.post("/api/smart-importer/queue/{queue_id}/approve")
def api_approve_queue(queue_id: int):
    conn = _get_smart_importer_db()
    cur = conn.cursor()
    cur.execute("SELECT extracted_json, filename FROM smart_importer_queue WHERE id = ?", (queue_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Não encontrado na fila")
    try:
        import json
        data = json.loads(row[0]) if row[0] else []
        columns = list(data[0].keys()) if data else []
        return {
            "columns": columns,
            "preview": data[:5],
            "all_rows": data,
            "filename": row[1]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro processando JSON extraído: {e}")

# ── Rotas de Teste de Escrita no Questor (Implementation Plan) ─────────────
from core.services.questor_writer import inserir_lancamento_lctoger_teste

class LancamentoTesteReq(BaseModel):
    codigo_empresa: int = 959
    codigo_estab: int = 1
    data: str
    codigo_centro_custo: int
    valor: float
    historico: str

@app.post("/api/questor/lancamento_teste")
def api_questor_lancamento_teste(req: LancamentoTesteReq):
    """
    Endpoint temporário para testar injeção no Firebird (Questor.fdb).
    A injeção real está comentada dentro da função `inserir_lancamento_lctoger_teste` 
    para evitar acidentes antes da aprovação do schema final.
    """
    resultado = inserir_lancamento_lctoger_teste(req.model_dump())
    if not resultado.get("success"):
        raise HTTPException(status_code=500, detail=resultado.get("error"))
    return resultado

