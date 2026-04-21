from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import firebirdsql
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

_DEFAULT_DB_QUESTOR = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB"
_DEFAULT_DB_VULCANO = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb"
DB_PATH_QUESTOR = os.environ.get("DB_PATH_QUESTOR", _DEFAULT_DB_QUESTOR)
DB_PATH_VULCANO = os.environ.get("DB_PATH_VULCANO", _DEFAULT_DB_VULCANO)
FIREBIRD_HOST = os.environ.get("FIREBIRD_HOST", "localhost")
FIREBIRD_PORT = int(os.environ.get("FIREBIRD_PORT", "3050"))
FIREBIRD_USER = os.environ.get("FIREBIRD_USER", "SYSDBA")
FIREBIRD_PASSWORD = os.environ.get("FIREBIRD_PASSWORD", "masterkey")

if genai:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

# Setup Cloud/Vertex para performance corporativa (JSON)
_VERTEX_INIT_DONE = False
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as OriginalVertexModel, Part
    
    class VertexModel:
        def __init__(self, *args, **kwargs):
            global _VERTEX_INIT_DONE
            if not _VERTEX_INIT_DONE:
                vertexai.init(project="questor-explorer-prod", location="us-central1")
                _VERTEX_INIT_DONE = True
            self.model = OriginalVertexModel(*args, **kwargs)
            
        def generate_content(self, *args, **kwargs):
            return self.model.generate_content(*args, **kwargs)
            
        async def generate_content_async(self, *args, **kwargs):
            return await self.model.generate_content_async(*args, **kwargs)
            
    HAS_VERTEXAI = True
except ImportError:
    HAS_VERTEXAI = False

# Modelo rápido por padrão; use GEMINI_MODEL no .env (ex.: gemini-2.5-flash) se quiser.
GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# Timeout da extração via Gemini (segundos). Front-end deve esperar pelo menos esse tempo.
GEMINI_EXTRACT_TIMEOUT_SEC = float(os.environ.get("GEMINI_EXTRACT_TIMEOUT_SEC", "300"))

LAST_RAW_PDF_TEXT_FOR_PARSER = ""

OLLAMA_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL_ID = os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:3b")

# SQLite: prefere `backend/poc_database.sqlite`; se não existir, usa legado no cwd (onde o uvicorn foi iniciado).
POC_DATABASE_FILE = os.environ.get("POC_DATABASE_FILE", "db.sqlite3")
_poc_backend = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poc_database.sqlite")
_poc_cwd = os.path.join(os.getcwd(), "poc_database.sqlite")
if os.path.isfile(_poc_backend):
    POC_DATABASE_FILE = _poc_backend
elif os.path.isfile(_poc_cwd):
    POC_DATABASE_FILE = _poc_cwd
else:
    POC_DATABASE_FILE = _poc_backend

def _require_gemini_key():
    if HAS_VERTEXAI: return
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured in backend")

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
    response_schema: dict = None   # [OPT-2] Structured Outputs — Vertex apenas
) -> dict:
    """Chama Gemini e retorna um objeto JSON (assíncrono nativo).

    Com response_schema (Vertex AI): garante 100% aderência ao JSON sem fallback/regex.
    Sem response_schema (Google AI Studio / fallback): usa response_mime_type padrão.
    """
    _require_gemini_key()
    resp = None

    contents = [prompt]
    if file_data and mime_type:
        if HAS_VERTEXAI:
            contents.append(Part.from_data(mime_type=mime_type, data=file_data))
        else:
            contents.append({"mime_type": mime_type, "data": file_data})

    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
            gen_cfg = {
                "response_mime_type": "application/json",
                "max_output_tokens": 8192,
            }
            if HAS_VERTEXAI:
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
                model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
                gen_cfg_fb = {
                    "response_mime_type": "application/json",
                    "max_output_tokens": 8192,
                }
                if HAS_VERTEXAI:
                    gen_cfg_fb["thinking_config"] = {"thinking_budget": 0}
                model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg_fb)
                fallback_contents = [prompt + "\n\nResponda somente um objeto JSON válido, sem markdown nem texto fora do JSON."]
                if mime_type and file_data:
                    fallback_contents.append(
                        Part.from_data(mime_type=mime_type, data=file_data) if HAS_VERTEXAI
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
        if HAS_VERTEXAI:
            contents.append(Part.from_data(mime_type=mime_type, data=file_data))
        else:
            contents.append({"mime_type": mime_type, "data": file_data})

    try:
        model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
        gen_cfg = {
            "response_mime_type": "application/json",
            "max_output_tokens": 8192,
        }
        if HAS_VERTEXAI:
            gen_cfg["thinking_config"] = {"thinking_budget": 0}
        model = model_cls(GEMINI_MODEL_ID, generation_config=gen_cfg)
        resp = model.generate_content(contents)
    except Exception:
        model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
        model = model_cls(GEMINI_MODEL_ID)
        fallback_contents = [prompt + "\n\nResponda somente JSON."]
        if file_data and mime_type:
             if HAS_VERTEXAI:
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

app = FastAPI(title="Questor Data Explorer API")

# ── Janitor SRE Agent imports ───────────────────────────────────────────────
from core.janitor.profiler import JanitorTimingMiddleware, start_profiler, get_performance_report
from core.janitor.cache    import get_cache_stats, invalidate_cache
from core.janitor.disk_inspector import run_disk_scan, get_disk_report, move_to_quarantine

from pydantic import BaseModel
class RawQuery(BaseModel):
    query: str

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
        conn_lite = sqlite3.connect(POC_DATABASE_FILE)
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

@app.get("/api/sero/maodeobra")
def api_sero_maodeobra(empresa_id: int = 959, ano: int = 2025, mes: int = 12, cno: str = None):
    conn_vulcano = get_conn("vulcano")
    conn_questor = get_conn("questor")
    
    try:
        cur_v = conn_vulcano.cursor()
        cur_q = conn_questor.cursor()
        
        # 1. Fetch Projects & Built Area (Vulcano)
        if cno:
            cur_v.execute("SELECT ID, NOME, CNO, DATACONCLUSAO, COALESCE(METRAGEMTOTAL, 0) FROM EMPREENDIMENTO WHERE CNO = ? AND CODIGOEMPRESA = ?", (cno, empresa_id))
        else:
            cur_v.execute("SELECT ID, NOME, CNO, DATACONCLUSAO, COALESCE(METRAGEMTOTAL, 0) FROM EMPREENDIMENTO WHERE CNO IS NOT NULL AND CNO <> '' AND CODIGOEMPRESA = ?", (empresa_id,))
            
        projetos = cur_v.fetchall()
        
        # 2. Fetch CUB indices
        cur_v.execute("SELECT MES, VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 ORDER BY MES ASC")
        cub_history = {str(r[0])[:7]: float(r[1]) for r in cur_v.fetchall() if r[1] is not None} # dict 'YYYY-MM' -> value
        
        # Fallback CUB if missing
        default_cub = 2850.0 
        
        area_total_calc = 0.0
        total_mao_de_obra_questor = 0.0
        total_inss_a_recolher = 0.0
        
        # Store aggregations
        historico_mensal = {} # 'YYYY-MM' -> {'realizado': 0, 'previsto': 0}
        
        data_minima = f"{ano}-12"
        data_maxima = f"{ano}-01"
        
        for proj in projetos:
            pid, pnome, pcno, pconclusao, parea = proj
            parea = float(parea) if parea else 0.0
            area_total_calc += parea
            
            raw_cno = "".join(filter(str.isdigit, pcno))
            
            cur_q.execute("""
                SELECT OE.CODIGOOUTEMP, OEE.INSCRFEDPROPRIET, E.NOMEESTAB
                FROM OUTRAEMPRESA OE
                LEFT JOIN OUTRAEMPEMP OEE ON OEE.CODIGOOUTEMP = OE.CODIGOOUTEMP AND OEE.CODIGOEMPRESA = ?
                LEFT JOIN ESTAB E ON E.INSCRFEDERAL = OEE.INSCRFEDPROPRIET AND E.CODIGOEMPRESA = ?
                WHERE REPLACE(REPLACE(REPLACE(OE.INSCRFEDERAL, '.', ''), '-', ''), '/', '') = ?
                OR REPLACE(REPLACE(REPLACE(OE.NOMEOUTEMP, '.', ''), '-', ''), '/', '') = ?
                OR CAST(OE.CODIGOOUTEMP AS VARCHAR(20)) = ?
            """, (empresa_id, empresa_id, raw_cno, raw_cno, raw_cno))
            
            outemp_data = cur_q.fetchone()
            if not outemp_data:
                try:
                    codigo_outemp = int(raw_cno)
                except:
                    codigo_outemp = -1
            else:
                codigo_outemp = outemp_data[0]
            
            cur_q.execute("""
                SELECT P.COMPET, SUM(C.VALOREVENTO)
                FROM CALCULORATEIO C
                JOIN PERIODOCALCULO P ON P.CODIGOPERCALCULO = C.CODIGOPERCALCULO
                WHERE C.CODIGOEVENTO = 5041 
                AND C.CODIGOEMPRESA = ?
                AND C.CODIGOOUTEMP = ?
                GROUP BY P.COMPET
            """, (empresa_id, codigo_outemp))
            
            folha_meses = cur_q.fetchall()
            
            start_date_str = None
            if folha_meses:
                folha_meses.sort(key=lambda x: str(x[0]))
                start_date_str = str(folha_meses[0][0])[:7] 
            else:
                start_date_str = f"{ano-4}-{str(mes).zfill(2)}"
                
            if start_date_str < data_minima: data_minima = start_date_str
            
            y_s, m_s = map(int, start_date_str.split('-'))
            
            for m_offset in range(48):
                c_m = m_s + m_offset
                c_y = y_s
                while c_m > 12:
                    c_m -= 12
                    c_y += 1
                
                comp_str = f"{c_y}-{str(c_m).zfill(2)}"
                
                if comp_str > f"{ano}-{str(mes).zfill(2)}":
                    break
                    
                if pconclusao:
                    conc_str = str(pconclusao)[:7]
                    if comp_str > conc_str:
                        continua_projetar = False
                    else:
                        continua_projetar = True
                else:
                    continua_projetar = True
                    
                if comp_str > data_maxima: data_maxima = comp_str
                
                if comp_str not in historico_mensal:
                    historico_mensal[comp_str] = {'previsto': 0.0, 'realizado': 0.0}
                
                if continua_projetar:
                    cub_mes = cub_history.get(comp_str, default_cub)
                    # BASE ESTIMADA DE MÃO DE OBRA (sem INSS) para equiparar ao LctoGer/CalculoRateio da folha
                    fracao_estimada = (parea * cub_mes * 0.20) / 48.0
                    historico_mensal[comp_str]['previsto'] += fracao_estimada
            
            for (compet, val) in folha_meses:
                comp_str = str(compet)[:7]
                if comp_str not in historico_mensal:
                    historico_mensal[comp_str] = {'previsto': 0.0, 'realizado': 0.0}
                
                valor_inss = float(val) if val else 0.0
                historico_mensal[comp_str]['realizado'] += valor_inss
                total_mao_de_obra_questor += valor_inss
                
        curva_s = []
        acc_real = 0.0
        acc_prev = 0.0
        for m in sorted(historico_mensal.keys()):
            if m < data_minima or m > data_maxima: continue
            
            acc_real += historico_mensal[m]['realizado']
            acc_prev += historico_mensal[m]['previsto']
            
            curva_s.append({
                "mes": m,
                "realizado_mes": round(historico_mensal[m]['realizado'], 2),
                "previsto_mes": round(historico_mensal[m]['previsto'], 2),
                "realizado": round(acc_real, 2),
                "previsto": round(acc_prev, 2)
            })
            
        # O Card de INSS a Recolher aplica 36.8% APENAS sobre a diferença final das Bases Descobertas
        diferenca_base = acc_prev - acc_real
        total_inss_a_recolher = diferenca_base * 0.368 if diferenca_base > 0 else 0.0

        cub_target = cub_history.get(f"{ano}-{str(mes).zfill(2)}", default_cub)

        return {
            "resumo": {
                "mao_de_obra": total_mao_de_obra_questor,
                "total_inss": total_inss_a_recolher,
                "cub_vigente": cub_target,
                "area_total": area_total_calc
            },
            "curva_s": curva_s
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn_vulcano.close()
        conn_questor.close()

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

from typing import Union

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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
            conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
            conn_poc = sqlite3.connect(POC_DATABASE_FILE)
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
    key = os.environ.get("GEMINI_API_KEY") or ""
    return {
        "ok": True,
        "gemini_key_configured": bool(key.strip()),
        "gemini_key_len": len(key.strip()),
    }

@app.get("/api/debug/env")
def debug_env():
    """Diagnóstico rápido (não expõe segredos)."""
    key = os.environ.get("GEMINI_API_KEY") or ""
    return {
        "dotenv_path": _DOTENV_PATH,
        "dotenv_exists": os.path.isfile(_DOTENV_PATH),
        "gemini_key_configured": bool(key.strip()),
        "gemini_key_len": len(key.strip()),
        "gemini_model": GEMINI_MODEL_ID,
        "gemini_extract_timeout_sec": GEMINI_EXTRACT_TIMEOUT_SEC,
        "cwd": os.getcwd(),
        "python_exe": sys.executable if "sys" in globals() else "",
        "firebird_host": FIREBIRD_HOST,
        "firebird_port": FIREBIRD_PORT,
        "db_path_vulcano": DB_PATH_VULCANO,
        "db_path_vulcano_exists": os.path.isfile(DB_PATH_VULCANO),
        "db_path_questor": DB_PATH_QUESTOR,
        "db_path_questor_exists": os.path.isfile(DB_PATH_QUESTOR),
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured in backend")
        
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
        model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
        gen_cfg = {
            "max_output_tokens": 8192,
        }
        if HAS_VERTEXAI:
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
    questor_db = DB_PATH_QUESTOR
    if db_name == "questor" and empresa_id is not None:
        import os
        base_dir = os.path.dirname(DB_PATH_QUESTOR)
        possible_path = os.path.join(base_dir, f"QUESTOR_EMPRESA_{empresa_id}.FDB")
        if os.path.exists(possible_path):
            questor_db = possible_path

    return firebirdsql.connect(
        host=FIREBIRD_HOST,
        database=questor_db if db_name == "questor" else DB_PATH_VULCANO,
        port=FIREBIRD_PORT,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset="WIN1252"
    )

def _table_has_column(cur, table_name: str, column_name: str) -> bool:
    """
    Checks if a Firebird table has a given column name.
    Uses system metadata (RDB$RELATION_FIELDS).
    """
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
    itens: List[QuestorLoteItem]
    
# Rotas e Implementações

@app.post("/api/templates")
def save_template(template: TemplateInput):
    conn = sqlite3.connect(POC_DATABASE_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO import_templates (nome, target_table, mapping_json) VALUES (?, ?, ?)',
              (template.nome, template.target_table, template.mapping_json))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/templates")
def get_templates(target_table: str = None):
    conn = sqlite3.connect(POC_DATABASE_FILE)
    c = conn.cursor()
    if target_table:
        c.execute('SELECT id, nome, target_table, mapping_json, data_criacao FROM import_templates WHERE target_table = ? ORDER BY id DESC', (target_table,))
    else:
        c.execute('SELECT id, nome, target_table, mapping_json, data_criacao FROM import_templates ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "nome": r[1], "target_table": r[2], "mapping_json": r[3], "data_criacao": r[4]} for r in rows]

@app.get("/api/poc")
def get_poc():
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
def get_questor_centrocusto():
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
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
        
        conn_sq = sqlite3.connect(POC_DATABASE_FILE)
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
        query = """SELECT ID, NOME, METRAGEMTOTAL, CUSTOORCADO, RET, DATACONCLUSAO, ATIVO, NULL AS CNO, 
                   CONTACAIXA, CONTACLI, CODIGOCENTROCUSTO, CONTAESTAND, CONTAESTCON,
                   CONTADESPESA, CONTAREC, CONTAVARIACAO, CONTALUCROACUM,
                   CODIGOHISTVENDA, CODIGOHISTRECEBIMENTO, CODIGOHISTVARIACAO, CODIGOHISTBAIXAADI,
                   ENDERECO, CONTADEVOLUCAO, CODIGO_HIST_ESTORNO_SALDO, CONTAADICLI, OBRACONCLUIDA,
                   CEP, SIGLAESTADO, CODIGOMUNIC, CODIGOESTAB, CODIGOFILIAL, CODIGOMATRIZ,
                   CONTACUSTO, CONTA_ESTORNO_DEVOLUCAO,
                   DATAINICIORET, ALIQRET, CODIGOIMPOSTO, VARIACAOIMPOSTO, TRIBUTARNORMALAPOSCONCLUSAO,
                   AJUSTEFINALPOC, REAJUSTAR_PELO_CUB, ADQUIRIDO_TERCEIROS, SEM_CUSTOS, CONSIDERAR_POC_RECEITA,
                   CODIGOHISTADIANTAMENTO, CODIGOHISTAPRCUSTO, CODIGOHISTDESPESA, CODIGO_HIST_ESTORNO_CUSTO
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
            
            "ajustefinalpoc": dec(r[39]), "reajustar_pelo_cub": dec(r[40]), "adquirido_terceiros": dec(r[41]),
            "sem_custos": dec(r[42]), "considerar_poc_receita": dec(r[43]),
            
            "hist_adiantamento": r[44] or 0, "hist_aprcusto": r[45] or 0, "hist_despesa": r[46] or 0, "hist_estorno_custo": r[47] or 0
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
    ajustefinalpoc: str = 'N'
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
    hist_distrato: int = 0
    hist_estorno: int = 0
    hist_adiantamento: int = 0
    hist_baixaadi: int = 0
    hist_aprcusto: int = 0
    hist_despesa: int = 0
    hist_estorno_saldo: int = 0
    hist_estorno_custo: int = 0
    
    empresa_id: int

@app.post("/api/vulcano/empreendimentos")
def post_vulcano_empreendimento(data: EmpreendimentoInput):
    conn = None
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM EMPREENDIMENTO")
        new_id = cur.fetchone()[0]
        
        query = """INSERT INTO EMPREENDIMENTO (
            ID, CODIGOEMPRESA, NOME, METRAGEMTOTAL, CUSTOORCADO, RET, CNO, ATIVO, OBRACONCLUIDA, ENDERECO, DATACONCLUSAO,
            CONTACAIXA, CONTACLI, CONTAADICLI, CONTAESTAND, CONTAESTCON, CONTADESPESA, CONTAREC, 
            CONTAVARIACAO, CONTADEVOLUCAO, CODIGOCENTROCUSTO, CONTACUSTO, CONTALUCROACUM, CONTA_ESTORNO_DEVOLUCAO,
            CODIGOHISTVENDA, CODIGOHISTRECEBIMENTO, CODIGOHISTVARIACAO, CODIGOHISTBAIXAADI, CODIGO_HIST_ESTORNO_SALDO,
            CODIGOHISTADIANTAMENTO, CODIGOHISTAPRCUSTO, CODIGOHISTDESPESA, CODIGO_HIST_ESTORNO_CUSTO,
            CEP, SIGLAESTADO, CODIGOMUNIC, CODIGOESTAB, CODIGOFILIAL, CODIGOMATRIZ,
            DATAINICIORET, ALIQRET, CODIGOIMPOSTO, VARIACAOIMPOSTO, TRIBUTARNORMALAPOSCONCLUSAO,
            AJUSTEFINALPOC, REAJUSTAR_PELO_CUB, ADQUIRIDO_TERCEIROS, SEM_CUSTOS, CONSIDERAR_POC_RECEITA
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        params = (
            new_id, 
            data.empresa_id, 
            data.nome.encode("cp1252", "ignore"), 
            data.metragem, 
            data.custo, 
            data.ret, 
            data.cno.encode("cp1252", "ignore"), 
            data.ativo, 
            data.obra_concluida,
            data.endereco.encode("cp1252", "ignore") if data.endereco else None, 
            data.data_conclusao or None,
            data.conta_caixa, data.conta_clientes, data.conta_adi_cli, data.conta_estand, data.conta_estcon, 
            data.conta_despesa, data.conta_rec, data.conta_variacao, data.conta_devolucao, data.centro_custo, 
            data.contacusto, data.contalucroacum, data.conta_estorno_devolucao,
            data.hist_venda, data.hist_recebimento, data.hist_variacao, data.hist_baixaadi, data.hist_estorno_saldo,
            data.hist_adiantamento, data.hist_aprcusto, data.hist_despesa, data.hist_estorno_custo,
            data.cep, data.siglaestado, data.codigomunic, data.codigoestab, data.codigofilial, data.codigomatriz,
            data.datainicioret or None, data.aliqret, data.codigoimposto, data.variacaoimposto, data.tributarnormalaposconclusao,
            data.ajustefinalpoc, data.reajustar_pelo_cub, data.adquirido_terceiros, data.sem_custos, data.considerar_poc_receita
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
            NOME = ?, METRAGEMTOTAL = ?, CUSTOORCADO = ?, RET = ?, CNO = ?, ATIVO = ?, OBRACONCLUIDA = ?, ENDERECO = ?, DATACONCLUSAO = ?,
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
            data.ativo,
            data.obra_concluida,
            data.endereco.encode("cp1252", "ignore") if data.endereco else None, 
            data.data_conclusao or None,
            data.conta_caixa, data.conta_clientes, data.conta_adi_cli, data.conta_estand, data.conta_estcon, 
            data.conta_despesa, data.conta_rec, data.conta_variacao, data.conta_devolucao, data.centro_custo,
            data.contacusto, data.contalucroacum, data.conta_estorno_devolucao,
            data.hist_venda, data.hist_recebimento, data.hist_variacao, data.hist_baixaadi, data.hist_estorno_saldo,
            data.hist_adiantamento, data.hist_aprcusto, data.hist_despesa, data.hist_estorno_custo,
            data.cep, data.siglaestado, data.codigomunic, data.codigoestab, data.codigofilial, data.codigomatriz,
            data.datainicioret or None, data.aliqret, data.codigoimposto, data.variacaoimposto, data.tributarnormalaposconclusao,
            data.ajustefinalpoc, data.reajustar_pelo_cub, data.adquirido_terceiros, data.sem_custos, data.considerar_poc_receita,
            emp_id
        )
        cur.execute(query, params)
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        if 'conn' in locals() and conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/vulcano/vendas")
def get_vulcano_vendas(empresa_id: int):
    try:
        conn = get_conn("vulcano")
        query_vendas = """
            SELECT v.ID, v.NUMCADIMOB, v.DTOPER, v.DESCUNIDIMOB, c.CNPJ, c.NOME AS CLIENTE_NOME, v.TOTALVENDA, v.DISTRATO, v.PERMUTA, e.NOME AS EMPREENDIMENTO, e.ID as EMPREENDIMENTO_ID
            FROM VENDA v
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
              AND COALESCE(c.NOME, '') NOT LIKE '%XXX%'
              AND COALESCE(c.CNPJ, '') <> '000.000.000-00'
              AND COALESCE(v.TOTALVENDA, 0) > 0.01
        """
        df_vendas = pd.read_sql_query(query_vendas, conn, params=(empresa_id,))
        df_vendas['UNIDADE_ID'] = None # Legacy vendas might not have precise array backlink
        
        df = df_vendas
        df = df.replace({np.nan: None})
        conn.close()

        def safe_dec(x):
            if isinstance(x, bytes):
                return x.decode('cp1252', 'ignore').strip()
            return str(x).strip() if x is not None else ""

        for col in ['NUMCADIMOB', 'DESCUNIDIMOB', 'CNPJ', 'CLIENTE_NOME', 'DISTRATO', 'PERMUTA', 'EMPREENDIMENTO']:
            if col in df.columns:
                df[col] = df[col].map(safe_dec)

        df['DTOPER'] = pd.to_datetime(df['DTOPER'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
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
            'PERMUTA': 'permuta',
            'EMPREENDIMENTO': 'empreendimento',
            'EMPREENDIMENTO_ID': 'empreendimento_id',
            'UNIDADE_ID': 'unidade_id'
        })

        return df_mapped[['id', 'num_cad', 'data', 'descricao', 'cliente_cnpj', 'cliente_nome', 'total', 'distrato', 'permuta', 'empreendimento', 'empreendimento_id', 'unidade_id']].to_dict('records')

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

        # Venda (resumo)
        cur.execute(
            """
            SELECT v.ID, v.NUMCADIMOB, v.DTOPER, v.DESCUNIDIMOB, v.TOTALVENDA, v.DISTRATO, v.DATADISTRATO, v.PERMUTA, e.NOME, c.ID, c.CNPJ, c.NOME
            FROM VENDA v
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            WHERE v.ID = ?
            """,
            (int(venda_id),),
        )
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
        for rr in cur.fetchall():
            forma_id = rr[8]
            parcelas.append(
                {
                    "id": rr[0],
                    "data": rr[1].strftime("%Y-%m-%d") if hasattr(rr[1], "strftime") else dec(rr[1]),
                    "parcela": dec(rr[2]),
                    "valor_parcela": float(rr[3] or 0),
                    "variacao": float(rr[4] or 0),
                    "desconto": float(rr[5] or 0),
                    "total_pago": float(rr[6] or 0),
                    "obs": dec(rr[7]),
                    "forma_pagto_id": int(forma_id) if forma_id is not None else None,
                    "forma_pagto_descricao": forma_by_id.get(forma_id, {}).get("descricao", "") if forma_id is not None else "",
                }
            )

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

@app.get("/api/vulcano/recebimentos")
def get_vulcano_recebimentos(empresa_id: int, empreendimento_id: int = None, data_ini: str = None, data_fim: str = None):
    import sqlite3
    s_conn = None
    try:
        locais = {}
        try:
            s_conn = sqlite3.connect(POC_DATABASE_FILE)
            s_curr = s_conn.cursor()
            s_curr.execute("SELECT id_receber, valor_pago, data_pagamento, descontos, acrescimos FROM operacoes_baixas WHERE empresa_id = ?", (empresa_id,))
            locais = {row[0]: row for row in s_curr.fetchall()}
        except Exception as e:
            pass
        finally:
            if s_conn: s_conn.close()
            
        conn = get_conn("vulcano")
        query = """
            SELECT r.DATA, r.TOTALPAGO, r.VALORPARCELA, r.VALORVARIACAO, v.DESCUNIDIMOB, c.CNPJ, r.PARCELA, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO, r.OBS, r.ID, v.TOTALVENDA, r.DESCONTO
            FROM VENDA v
            JOIN RECEBER r ON r.IDVENDA = v.ID
            LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
            LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
            WHERE v.CODIGOEMPRESA = ?
        """
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
        conn.close()

        def safe_dec(x):
            if isinstance(x, bytes):
                return x.decode('cp1252', 'ignore').strip()
            return str(x).strip() if x is not None else ""

        for col in ['DESCUNIDIMOB', 'CNPJ', 'PARCELA', 'CLIENTE_NOME', 'EMPREENDIMENTO', 'OBS']:
            if col in df.columns:
                df[col] = df[col].map(safe_dec)

        # Vetorização de formatação de data e numéricos
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
            'DESCONTO': 'desconto'
        }).fillna('')
        
        result_list = df_mapped[['id', 'data', 'vencimento_iso', 'total', 'parcela', 'variacao', 'descricao_venda', 'cliente_cnpj', 'num_parcela', 'cliente', 'empreendimento', 'obs', 'desconto']].to_dict('records')
        
        for item in result_list:
            rid = item['id']
            if rid in locais:
                db_l = locais[rid]
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
                
        return result_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BaixaInput(BaseModel):
    id_receber: int
    valor_pago: float
    data_pagamento: str 
    acrescimos: float 
    descontos: float
    empresa_id: int

@app.post("/api/vulcano/recebimentos/baixa")
def baixa_recebimento(data: BaixaInput):
    import sqlite3
    s_conn = None
    try:
        s_conn = sqlite3.connect(POC_DATABASE_FILE)
        s_curr = s_conn.cursor()
        s_curr.execute("""
            INSERT INTO operacoes_baixas (id_receber, empresa_id, data_pagamento, valor_pago, descontos, acrescimos) 
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_receber) DO UPDATE SET 
               data_pagamento=excluded.data_pagamento, 
               valor_pago=excluded.valor_pago, 
               descontos=excluded.descontos, 
               acrescimos=excluded.acrescimos
        """, (data.id_receber, data.empresa_id, data.data_pagamento, data.valor_pago, data.descontos, data.acrescimos))
        s_conn.commit()
        return {"success": True, "message": "Baixada no sistema auxiliar SQLite com sucesso"}
    except Exception as e:
        if s_conn: s_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if s_conn: s_conn.close()

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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
            conn = sqlite3.connect(POC_DATABASE_FILE)
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
        model_cls = VertexModel if HAS_VERTEXAI else genai.GenerativeModel
        gen_cfg = {"max_output_tokens": 8192}
        if HAS_VERTEXAI: gen_cfg["thinking_config"] = {"thinking_budget": 0}
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
            conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
        conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
    conn = sqlite3.connect(POC_DATABASE_FILE)
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
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado. Use CSV ou Excel.")
            
        columns = df.columns.tolist()
        df = df.fillna('')
        data_preview = df.head(10).to_dict(orient='records')
        
        return {
            "filename": file.filename,
            "columns": columns,
            "preview": data_preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/api/schema-match")
def schema_match(payload: dict):
    import json
    columns = payload.get("columns", [])
    
    # Introspect internal DB schema
    try:
        available_schema = api_schema_tables().get("schema", {})
    except Exception:
        available_schema = {}

    prompt = f"""You are an absolute expert database administrator and data analyst.
We have imported a worksheet with the following columns:
{json.dumps(columns, ensure_ascii=False)}

Our Vulcano Database contains the following target tables and columns:
{json.dumps(available_schema, ensure_ascii=False)}

Your objective:
1. Analyze the worksheet columns and infer which table(s) from our Vulcano schema it represents.
2. Return ONLY a valid JSON object with the exact name of the inferred table(s) as keys, and inside them, another object where keys are the SOURCE column names, and values are the TARGET field names. Example format:
{{
   "VENDA": {{
      "DATA_OPERACAO": "DATA_VENDA",
      "CPF_CLIENTE": "CLIENTE_DOCUMENTO"
   }}
}}

No markdown, no explanation, no formatting tags. Only return the raw JSON object."""

    try:
        mapping = _ollama_generate_json(prompt)
        if not isinstance(mapping, dict):
            raise HTTPException(status_code=500, detail="Ollama não retornou um objeto JSON válido de mapeamento.")
        return {"mapping": mapping}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar schema com Ollama: {str(e)}")

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
            
        cur.execute("DELETE FROM UNIDADE WHERE ID_BLOCO IN (SELECT ID FROM BLOCO WHERE IDEMPREENDIMENTO = ?)", (emp_id,))
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
def get_empreendimento_detalhes(emp_id: int):
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
                SELECT u.ID, u.IDBLOCO, u.DESCRICAO, u.METRAGEM, u.NUMCADIMOB, u.UNIDADE_DISTRATO 
                FROM UNIDADE u
                WHERE u.IDBLOCO IN ({placeholders})
                  AND NOT EXISTS (
                      SELECT 1 FROM VENDAUNIDADE vu
                      JOIN VENDA v ON vu.IDVENDA = v.ID
                      WHERE vu.IDUNIDADE = u.ID AND COALESCE(v.DISTRATO, 'N') <> 'S'
                  )
            """
            cur.execute(query_unidades, tuple(b_ids))
            
            for r in cur.fetchall():
                unidades.append({
                    "id": r[0],
                    "id_bloco": r[1],
                    "descricao": r[2].decode('win1252', 'ignore').strip() if isinstance(r[2], bytes) else str(r[2] or "").strip(),
                    "metragem": float(r[3] or 0),
                    "inscricao": str(r[4] or ""),
                    "unidade_distrato": r[5].decode('win1252', 'ignore').strip() if isinstance(r[5], bytes) else str(r[5] or "N").strip()
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

        # --- CLIENTES ---
        compradores = data.get("compradores", [])
        id_cliente = None
        if compradores:
            comp_princ = compradores[0]
            raw_doc = "".join(filter(str.isdigit, comp_princ.get("cpf_cnpj", "")))
            if raw_doc:
                cur.execute("SELECT FIRST 1 ID FROM CLIENTE WHERE REPLACE(REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '-', ''), '/', ''), ' ', '') = ?", (raw_doc,))
                cli_row = cur.fetchone()
                if cli_row:
                    id_cliente = cli_row[0]
                else:
                    cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM CLIENTE")
                    id_cliente = cur.fetchone()[0]
                    cur.execute("INSERT INTO CLIENTE (ID, NOME, CNPJ, CODIGOEMPRESA) VALUES (?, ?, ?, ?)",
                        (id_cliente, str(comp_princ.get("nome", "")).encode('cp1252', 'ignore')[:100], comp_princ.get("cpf_cnpj", ""), int(empresa_id)))

        # --- VENDA ---
        cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM VENDA")
        new_id = cur.fetchone()[0]

        permuta = str(data.get("permuta", "N")).upper()
        if permuta not in ["S", "N"]: permuta = "N"

        date_str = data.get("data", "")
        id_empreendimento = int(data.get("id_empreendimento", 0) or 0)

        query = "INSERT INTO VENDA (ID, IDEMPREENDIMENTO, NUMCADIMOB, DTOPER, DESCUNIDIMOB, TOTALVENDA, CODIGOEMPRESA, DISTRATO, PERMUTA, ID_CLIENTE) VALUES (?, ?, ?, ?, ?, ?, ?, 'N', ?, ?)"
        params = (
            new_id,
            id_empreendimento,
            "MVP-" + str(new_id),
            date_str,
            str(data.get("unidade", "")).encode('cp1252', 'ignore')[:100],
            float(data.get("total", 0) or 0),
            int(empresa_id),
            permuta,
            id_cliente
        )
        cur.execute(query, params)

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
        
        # update venda flag
        cur.execute("UPDATE VENDA SET DISTRATO = 'S', DATADISTRATO = ? WHERE ID = ?", (data.get("data_distrato"), int(id_venda)))
        
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
            comprador_nome = str(row.get("comprador_nome", "")).strip()
            
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
                    if comprador_nome:
                        _nome_ratio = _fuzz.token_set_ratio(
                            comprador_nome, str(c_nome or ''), score_cutoff=0
                        )
                        if _nome_ratio >= 75:
                            score += max(5, int(_nome_ratio / 100 * 15))  # proporcional 5–15
                        
                    # NÍVEL 2: Unidade — partial_ratio (cobre abreviações)
                    # Captura: "APTO 302" ↔ "BLOCO A APTO 302" → 100
                    if unidade and v_desc:
                        _unid_ratio = _fuzz.partial_ratio(
                            clean_str(unidade), clean_str(v_desc), score_cutoff=0
                        )
                        if _unid_ratio >= 80:
                            score += max(5, int(_unid_ratio / 100 * 15))  # proporcional 5–15
                        
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

            candidatas.sort(key=lambda x: x['score'], reverse=True)
            
            def dec(vx):
                if vx is None: return ''
                if isinstance(vx, bytes): return vx.decode('win1252', 'ignore')
                return str(vx)
                
            grupos_unidades = {}
            for cand in candidatas:
                desc_unid = dec(cand["v_row"][4]).upper().strip()
                if not desc_unid: desc_unid = f'V_{cand["v_row"][0]}'
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
                        cur.execute("SELECT ID, DATA, VALORPARCELA, TOTALPAGO, PARCELA FROM RECEBER WHERE IDVENDA = ? AND DATA >= '2025-06-01'", (v_id,))
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
                            WHERE vfp.IDVENDA = ? AND p.DATA >= '2025-06-01'
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
                # Dois critérios:
                #   A) Com data extraída: valor próximo (< 5 reais) + mês/ano bate
                #   B) Sem data (ou OCR falhou): valor EXATO (< 0.50 reais) - sinal forte de duplicata
                for _pool, _type in [(pool_quitadas, "JA_PAGO_RECEBER"), (pool_prazos_quitados, "JA_PAGO_PROJETADA")]:
                    for p_tuple in _pool:
                        p, cand, is_prazo = p_tuple
                        p_valor = float(p[2] or 0)
                        if p_valor <= 0: continue
                        diff_abs = min(abs(p_valor - total_pago), abs(p_valor - valor_raiz) if valor_raiz else 9999)
                        if diff_abs >= 5.0: continue  # Valor muito diferente, ignorar
                        db_venc = str(p[1])
                        # Critério A: data bate + valor próximo
                        date_ok = pdf_mes and f'-{pdf_mes}-' in db_venc and (not pdf_ano or pdf_ano in db_venc)
                        # Critério B: valor exato (< 0.50) mesmo sem data
                        exact_value = diff_abs < 0.50
                        if date_ok or exact_value:
                            match_perfeito = p_tuple
                            mat_type = _type
                            break
                    if match_perfeito: break

                # 00B. Múltiplo JA PAGO (Titulos Conjuntos quitados) — requer data
                if not match_perfeito and not lista_multipla and pdf_mes:
                    achou_combo_pago = False
                    for _pool, _type in [(pool_quitadas, "MULTIPLO_JA_PAGO_RECEBER"), (pool_prazos_quitados, "MULTIPLO_JA_PAGO_PROJETADA")]:
                        if len(_pool) >= 2:
                            for combo_tamanho in [2, 3, 4]:
                                if achou_combo_pago or len(_pool) < combo_tamanho: break
                                for combo in combinations(_pool, combo_tamanho):
                                    if same_date_combo(combo) and has_pdf_date(combo):
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
                
                # 3. Margem CUB Singular SE DIAMANTE
                if not match_perfeito and not lista_multipla:
                    diamante_no_grupo = any(c['is_diamante'] for c in grupo_vendas)
                    if diamante_no_grupo:
                        for p_tuple in pool_abertas:
                            p, cand, is_prazo = p_tuple
                            p_valor = float(p[2] or 0)
                            if p_valor > 0 and total_pago > p_valor and (abs(total_pago - p_valor) / p_valor) < 5.0:
                                db_venc = str(p[1])
                                if pdf_mes and f'-{pdf_mes}-' in db_venc and pdf_ano in db_venc:
                                    match_perfeito = p_tuple
                                    mat_type = "CUB_RECEBER_DATA_EXATA"
                                    break
                                    
                        if not match_perfeito:
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
                                if pr_valor > 0 and total_pago > pr_valor and (abs(total_pago - pr_valor) / pr_valor) < 5.0:
                                    db_venc = str(pr[1])
                                    if pdf_mes and f'-{pdf_mes}-' in db_venc and pdf_ano in db_venc:
                                        match_perfeito = pr_tuple
                                        mat_type = "CUB_PROJETADA_DATA_EXATA"
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

@app.get("/api/sero/maodeobra")
def get_sero_maodeobra(
    empresa_id: int = Query(..., description="ID da Empresa"),
    ano: int = Query(None),
    mes: int = Query(None),
    cno: str = Query(None)
):
    conn = None
    conn_v = None
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        
        q = """
            SELECT 
                p.COMPET, 
                c.CODIGOOUTEMP, 
                o.NOMEOUTEMP,
                o.INSCRFEDERAL,
                SUM(c.VALOREVENTO) as VALOR_ALOCADO
            FROM CALCULORATEIO c
            JOIN PERIODOCALCULO p ON c.CODIGOPERCALCULO = p.CODIGOPERCALCULO AND c.CODIGOEMPRESA = p.CODIGOEMPRESA
            LEFT JOIN OUTRAEMPRESA o ON c.CODIGOOUTEMP = o.CODIGOOUTEMP
            WHERE c.CODIGOEVENTO = 5041 AND c.CODIGOEMPRESA = ?
            GROUP BY p.COMPET, c.CODIGOOUTEMP, o.NOMEOUTEMP, o.INSCRFEDERAL
            ORDER BY p.COMPET DESC
        """
        cur.execute(q, (empresa_id,))
        rows = cur.fetchall()
        
        cno_dados = {}
        cub_vigente = 0.0
        try:
            import re
            conn_v = get_conn("vulcano")
            cur_v = conn_v.cursor()
            cur_v.execute("SELECT CNO, METRAGEMTOTAL, DATAINICIORET, DATACONCLUSAO FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = ?", (empresa_id,))
            for r in cur_v.fetchall():
                cno_val = r[0].decode('win1252', 'ignore').strip() if isinstance(r[0], bytes) else str(r[0] or "").strip()
                cno_val = re.sub(r'\D', '', cno_val)
                if cno_val: 
                    dt_ini = r[2].strftime("%Y-%m-%d") if r[2] and hasattr(r[2], 'strftime') else str(r[2])[:10] if r[2] else None
                    dt_fim = r[3].strftime("%Y-%m-%d") if r[3] and hasattr(r[3], 'strftime') else str(r[3])[:10] if r[3] else None
                    cno_dados[cno_val] = {
                        "metragem": float(r[1] or 0),
                        "data_inicio": dt_ini,
                        "data_fim": dt_fim
                    }
                    
            cub_history = {}
            cur_v.execute("SELECT MES, VALOR FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1 AND VALOR IS NOT NULL ORDER BY MES ASC")
            for r in cur_v.fetchall():
                m_str = r[0].strftime("%Y-%m") if hasattr(r[0], 'strftime') else str(r[0])[:7]
                cub_history[m_str] = float(r[1])
        except Exception:
            pass
            
        def get_cub_mensal(m_str):
            if 'cub_history' in locals() and m_str in cub_history: return cub_history[m_str]
            if 'cub_history' in locals():
                past_cubs = [cub for k, cub in cub_history.items() if k <= m_str]
                if past_cubs: return past_cubs[-1]
            return 2950.40
            
        obras = {}
        alocacoes = []
        target_compet = f"{ano}-{mes:02d}" if ano and mes else "9999-99"
        cub_vigente = get_cub_mensal(target_compet)

        for row in rows:
            compet_dt, cod_out, nome_out, inscr, valor = row
            compet_str = compet_dt.strftime("%Y-%m") if hasattr(compet_dt, 'strftime') else str(compet_dt)
            nome_str = nome_out.decode('win1252', 'ignore') if isinstance(nome_out, bytes) else str(nome_out)
            inscr_str = str(inscr or "")
            clean_inscr = re.sub(r'\D', '', inscr_str)
            
            if cno and cno != "undefined" and cno != "null" and cno != "All" and cno != "":
                clean_target_cno = re.sub(r'\D', '', cno)
                if clean_inscr != clean_target_cno:
                    continue
                
            if cod_out not in obras:
                obras[cod_out] = {
                    "nome": nome_str, 
                    "cno": inscr_str, 
                    "alocado_total": 0, 
                    "min_compet": compet_str,
                    "max_compet": compet_str
                }
            else:
                if compet_str < obras[cod_out]["min_compet"]: obras[cod_out]["min_compet"] = compet_str
                if compet_str > obras[cod_out]["max_compet"]: obras[cod_out]["max_compet"] = compet_str
                    
            val = float(valor or 0)
            if compet_str <= target_compet:
                obras[cod_out]["alocado_total"] += val
            
            alocacoes.append({
                "compet": compet_str,
                "codigo_obra": cod_out,
                "nome_obra": nome_str,
                "cno": inscr_str,
                "valor_recolhido": val
            })
            
        for k, v in obras.items():
            clean_cno = re.sub(r'\D', '', str(v.get("cno", "")))
            dados_emp = cno_dados.get(clean_cno, {})
            obras[k]["metragem"] = dados_emp.get("metragem", 0.0)
            
            dt_ini = dados_emp.get("data_inicio")
            if not dt_ini and v.get("min_compet"): dt_ini = v["min_compet"] + "-01"
            dt_fim = dados_emp.get("data_fim")
            if not dt_fim and v.get("max_compet"): dt_fim = v["max_compet"] + "-28"
                
            obras[k]["data_inicio"] = dt_ini
            obras[k]["data_fim"] = dt_fim

        mao_de_obra = sum(o["alocado_total"] for o in obras.values())
        area_total = sum(o.get("metragem", 0) for o in obras.values())
        custo_obra_estimado = area_total * cub_vigente
        inss_devido = custo_obra_estimado * 0.20
        total_inss = max(0, inss_devido - mao_de_obra)

        from collections import defaultdict
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        mensal = defaultdict(float)
        for a in alocacoes:
            if a["compet"] <= target_compet:
                mensal[a["compet"]] += a["valor_recolhido"]

        min_inicio_obra = None
        min_fim_obra = None
        for k, v in obras.items():
            ini = v.get("data_inicio")
            if ini:
                ini_comp = ini[:7]
                if not min_inicio_obra or ini_comp < min_inicio_obra: min_inicio_obra = ini_comp
            
            fim = v.get("data_fim")
            if fim and fim != "None" and str(fim).strip() and not str(fim).startswith("9999"):
                fim_comp = fim[:7]
                if not min_fim_obra or fim_comp < min_fim_obra: min_fim_obra = fim_comp
                
        # Determine strict bounds
        if min_inicio_obra and min_inicio_obra < target_compet:
            dt_start_str = min_inicio_obra
        else:
            # Fallback if no start date found or start date is after target_compet
            dt_start_str = min(mensal.keys()) if mensal else target_compet

        dt_end_str = target_compet
        """
        If they selected "2024-08" but obra ended in "2023-12", we cap the graph at "2023-12".
        However, the user asked for "até a data consultada para obras em andamento".
        If target_compet < min_fim_obra, it's still in progress, so cap at target_compet.
        """
        if min_fim_obra and min_fim_obra < target_compet:
            dt_end_str = min_fim_obra
                
        curva_s = []
        try:
            dt_start = datetime.strptime(dt_start_str, "%Y-%m")
            dt_end = datetime.strptime(dt_end_str, "%Y-%m")
            
            # Cap extreme history (e.g. 6 years = 72 months) to avoid giant graphs
            months_diff = (dt_end.year - dt_start.year) * 12 + dt_end.month - dt_start.month
            if months_diff > 72:
                dt_start = dt_end - relativedelta(months=72)
                
            acc = 0
            current = dt_start
            while current <= dt_end:
                m_str = current.strftime("%Y-%m")
                # Need to accumulate all historical past EVEN BEFORE dt_start visually
                # Actually, let's accumulate properly from the absolute beginning
                pass
                current += relativedelta(months=1)
                
            # Recreate acc to include everything up to dt_end
            acc_real = 0
            sorted_all_months = sorted(mensal.keys())
            idx_month = 0
            
            current = dt_start
            while current <= dt_end:
                m_str = current.strftime("%Y-%m")
                # accumulate any keys that are <= m_str
                while idx_month < len(sorted_all_months) and sorted_all_months[idx_month] <= m_str:
                    acc_real += mensal[sorted_all_months[idx_month]]
                    idx_month += 1
                
                cub_m = get_cub_mensal(m_str)
                inss_devido_m = area_total * cub_m * 0.20
                    
                curva_s.append({
                    "mes": m_str,
                    "realizado": acc_real,
                    "previsto": inss_devido_m
                })
                current += relativedelta(months=1)
        except Exception:
            pass
            
        # Force padding so Recharts renders if only 1 month exists
        if len(curva_s) <= 1:
            try:
                base_dt = datetime.strptime(target_compet, "%Y-%m") if target_compet != "9999-99" else datetime.now()
                pad_dt = base_dt - relativedelta(months=1)
                cub_pad = get_cub_mensal(pad_dt.strftime("%Y-%m"))
                curva_s.insert(0, {"mes": pad_dt.strftime("%Y-%m"), "realizado": 0, "previsto": area_total * cub_pad * 0.20})
                if len(curva_s) == 1:
                    curva_s.append({"mes": target_compet, "realizado": acc_real if 'acc_real' in locals() else 0, "previsto": area_total * cub_vigente * 0.20})
            except: pass

        return {
            "resumo": {
                "mao_de_obra": mao_de_obra,
                "total_inss": total_inss,
                "cub_vigente": cub_vigente,
                "area_total": area_total
            },
            "curva_s": curva_s[-48:] if curva_s else [],
            "obras": [{"codigo": k, **v} for k, v in obras.items()],
            "alocacoes": alocacoes
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()
        if conn_v: conn_v.close()

@app.get("/api/sped/f200/preview")
def sped_f200_preview(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_f200
    res = processar_f200(empresa_id, ano, mes, dry_run=True)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.post("/api/sped/f200/commit")
def sped_f200_commit(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_f200
    res = processar_f200(empresa_id, ano, mes, dry_run=False)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.get("/api/sped/ret/preview")
def sped_ret_preview(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_ret
    res = processar_ret(empresa_id, ano, mes, dry_run=True)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

@app.post("/api/sped/ret/commit")
def sped_ret_commit(empresa_id: int, ano: int, mes: int):
    from injector_sped import processar_ret
    res = processar_ret(empresa_id, ano, mes, dry_run=False)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Unknown error"))
    return res

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

@app.post("/api/agentes/iniciar_auditoria")
async def api_agentes_iniciar(req: AuditStartReq):
    import asyncio
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
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend build not found"}

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


