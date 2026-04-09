"""
sindicato_agent.py
Responsável por:
- Inicializar a tabela sindicato_cct no SQLite
- Ler os 10 sindicatos do Questor (Firebird)
- Buscar CCT no MTE Mediador por CNPJ
- Extrair cláusulas via Gemini
- Agendar atualização diária
"""

import os
import sqlite3
import hashlib
import logging
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

import httpx
import pdfplumber
import google.generativeai as genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Configurações ─────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
SQLITE_PATH = str(_HERE / "poc_database.sqlite")
LOG_PATH = str(_HERE / "sindicato_agent.log")

# Firebird (lidos do ambiente — mesmos valores que main.py usa)
FB_HOST = os.environ.get("FIREBIRD_HOST", "localhost")
FB_PORT = int(os.environ.get("FIREBIRD_PORT", "3050"))
FB_USER = os.environ.get("FIREBIRD_USER", "SYSDBA")
FB_PASS = os.environ.get("FIREBIRD_PASSWORD", "masterkey")
FB_DB_QUESTOR = os.environ.get(
    "DB_PATH_QUESTOR",
    r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB",
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# MTE Mediador
MTE_BASE = "https://mediador.mte.gov.br"
MTE_SEARCH = f"{MTE_BASE}/Mediador/Resumos/ConsultarInstrumentoColetivo"

# ── Logging ───────────────────────────────────────────────────────────────────
_log_handlers: list[logging.Handler] = [logging.StreamHandler()]
try:
    _log_handlers.append(logging.FileHandler(LOG_PATH, encoding="utf-8"))
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_log_handlers,
)
logger = logging.getLogger("sindicato_agent")


# ── SQLite ────────────────────────────────────────────────────────────────────
def init_sindicato_table() -> None:
    """Cria a tabela sindicato_cct se ainda não existir."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sindicato_cct (
            codigosind           INTEGER PRIMARY KEY,
            nome                 TEXT,
            sigla                TEXT,
            cnpj                 TEXT,
            piso_salarial        REAL,
            piso_data            TEXT,
            database_mes         INTEGER,
            database_ano         INTEGER,
            alimentacao_valor    TEXT,
            alimentacao_clausula TEXT,
            transporte_valor     TEXT,
            transporte_clausula  TEXT,
            url_pdf              TEXT,
            hash_pdf             TEXT,
            status               TEXT DEFAULT 'pendente',
            erro_msg             TEXT,
            ultima_atualizacao   TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Tabela sindicato_cct verificada/criada.")


# ── Questor reader ────────────────────────────────────────────────────────────
def read_sindicatos_from_questor() -> list:
    """
    Lê os 10 primeiros sindicatos do Questor (por CODIGOSIND) e enriquece
    com o piso salarial mais recente (SINDNORMATIVO) e data base (SINDCONVENCAO).
    Retorna lista de dicts com chaves: codigosind, nome, sigla, cnpj,
    piso_salarial, piso_data, database_mes.
    """
    import firebirdsql

    conn = firebirdsql.connect(
        host=FB_HOST, port=FB_PORT,
        user=FB_USER, password=FB_PASS,
        database=FB_DB_QUESTOR,
        charset="WIN1252",
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT s.CODIGOSIND, s.NOMESIND, s.SIGLASIND, s.INSCRFEDERAL,
               n.NORMATBASICO, n.DATAINICIAL,
               c.MESDATABASE, c.DATAINICIAL
        FROM SINDICATO s
        LEFT JOIN SINDNORMATIVO n ON n.CODIGOSIND = s.CODIGOSIND
            AND n.DATAINICIAL = (
                SELECT MAX(n2.DATAINICIAL) FROM SINDNORMATIVO n2
                WHERE n2.CODIGOSIND = s.CODIGOSIND
            )
        LEFT JOIN SINDCONVENCAO c ON c.CODIGOSIND = s.CODIGOSIND
            AND c.DATAINICIAL = (
                SELECT MAX(c2.DATAINICIAL) FROM SINDCONVENCAO c2
                WHERE c2.CODIGOSIND = s.CODIGOSIND
            )
        WHERE s.CODIGOSIND <= 9
        ORDER BY s.CODIGOSIND
    """)

    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        cod, nome, sigla, cnpj, piso, piso_data, db_mes, conv_data = row
        result.append({
            "codigosind": int(cod),
            "nome": (nome or "").strip(),
            "sigla": (sigla or "").strip(),
            "cnpj": (cnpj or "").strip(),
            "piso_salarial": float(piso) if piso else None,
            "piso_data": str(piso_data) if piso_data else None,
            "database_mes": int(db_mes) if db_mes else None,
        })

    logger.info(f"Lidos {len(result)} sindicatos do Questor.")
    return result


# ── MTE Mediador scraper ──────────────────────────────────────────────────────
def _limpar_cnpj(cnpj: str) -> str:
    """Remove pontuação do CNPJ: '12.345.678/0001-90' → '12345678000190'"""
    return re.sub(r"\D", "", cnpj or "")


async def buscar_cct_mte(cnpj: str, timeout: int = 30) -> dict:
    """
    Busca a CCT mais recente no MTE Mediador pelo CNPJ do sindicato.
    Retorna dict com chaves: url_pdf (str|None), erro (str|None).
    """
    cnpj_limpo = _limpar_cnpj(cnpj)
    if not cnpj_limpo:
        return {"url_pdf": None, "erro": "CNPJ vazio"}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    try:
        async with httpx.AsyncClient(
            headers=headers, timeout=timeout, follow_redirects=True
        ) as client:
            # GET inicial para obter cookies
            await client.get(MTE_BASE)

            # POST com CNPJ
            resp = await client.post(
                MTE_SEARCH,
                data={"cnpj": cnpj_limpo, "tipo": "CCT"},
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            html = resp.text

            # Padrão 1: links de download diretos
            pdf_links = re.findall(
                r'href=["\']([^"\']*(?:Download|pdf|Arquivo)[^"\']*)["\']',
                html,
                re.IGNORECASE,
            )

            if not pdf_links:
                # Padrão 2: links contendo instrumento/convencao
                pdf_links = re.findall(
                    r'href=["\']([^"\']*(?:instrumento|convencao|acordo)[^"\']*)["\']',
                    html,
                    re.IGNORECASE,
                )

            if not pdf_links:
                return {
                    "url_pdf": None,
                    "erro": "Nenhum PDF/CCT encontrado no Mediador para este CNPJ",
                }

            url = pdf_links[0]
            if not url.startswith("http"):
                url = MTE_BASE + ("" if url.startswith("/") else "/") + url

            logger.info(f"CNPJ {cnpj_limpo}: PDF encontrado → {url}")
            return {"url_pdf": url, "erro": None}

    except httpx.HTTPStatusError as e:
        return {"url_pdf": None, "erro": f"HTTP {e.response.status_code} ao consultar Mediador"}
    except httpx.TimeoutException:
        return {"url_pdf": None, "erro": "Timeout ao consultar Mediador MTE"}
    except Exception as e:
        return {"url_pdf": None, "erro": f"Erro scraping Mediador: {str(e)}"}


async def baixar_pdf(url: str, timeout: int = 60) -> dict:
    """
    Baixa o PDF da URL e retorna dict com:
    conteudo (bytes|None), hash_md5 (str|None), erro (str|None).
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            conteudo = resp.content
            hash_md5 = hashlib.md5(conteudo).hexdigest()
            return {"conteudo": conteudo, "hash_md5": hash_md5, "erro": None}
    except Exception as e:
        return {"conteudo": None, "hash_md5": None, "erro": f"Erro download PDF: {str(e)}"}


# ── Gemini extractor ──────────────────────────────────────────────────────────
def _extrair_texto_pdf(conteudo_bytes: bytes) -> str:
    """Extrai texto de PDF em memória usando pdfplumber."""
    import io
    texto_total = []
    with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto_total.append(t)
    return "\n".join(texto_total)


async def extrair_clausulas_gemini(texto_pdf: str, nome_sindicato: str) -> dict:
    """
    Envia o texto da CCT ao Gemini e extrai em JSON:
    piso_salarial, data_base_mes, data_base_ano,
    alimentacao_valor, alimentacao_clausula,
    transporte_valor, transporte_clausula.
    Retorna dict com esses campos + chave 'erro' (None se ok).
    """
    if not GEMINI_API_KEY:
        return {"erro": "GEMINI_API_KEY não configurada"}

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Limita texto para não exceder contexto (primeiras 40k chars)
    texto_truncado = texto_pdf[:40000]

    prompt = f"""Você é um especialista em direito trabalhista brasileiro.
Analise a CCT (Convenção Coletiva de Trabalho) do sindicato "{nome_sindicato}" abaixo e extraia exatamente as informações pedidas.

RETORNE APENAS JSON VÁLIDO, sem texto adicional, sem markdown, sem ```json.

Formato exato:
{{
  "piso_salarial": <número decimal ou null>,
  "data_base_mes": <inteiro 1-12 ou null>,
  "data_base_ano": <inteiro 4 dígitos ou null>,
  "alimentacao_valor": "<texto descritivo do valor/benefício, ex: 'R$ 35,00 por dia útil' ou null>",
  "alimentacao_clausula": "<trecho literal da cláusula sobre alimentação/refeição/VR, máx 300 chars, ou null>",
  "transporte_valor": "<texto descritivo, ex: '6% do salário' ou 'R$ 250,00/mês' ou null>",
  "transporte_clausula": "<trecho literal da cláusula sobre vale-transporte/VT, máx 300 chars, ou null>"
}}

Regras:
- piso_salarial: valor numérico em reais do piso salarial normativo base (sem R$)
- Para campos de clausula: copie o trecho literal do documento, não parafraseie
- Se alguma informação não constar no documento, use null

TEXTO DA CCT:
{texto_truncado}
"""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt),
        )
        raw = response.text.strip()

        # Remove markdown code fences se presentes
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        dados = json.loads(raw)
        dados["erro"] = None
        return dados

    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido do Gemini para {nome_sindicato}: {e}")
        return {"erro": f"Resposta JSON inválida do Gemini: {str(e)}"}
    except Exception as e:
        logger.error(f"Erro Gemini para {nome_sindicato}: {e}")
        return {"erro": f"Erro Gemini: {str(e)}"}


# ── SQLite upsert ─────────────────────────────────────────────────────────────
def _upsert_sindicato(data: dict) -> None:
    """Insere ou atualiza um registro em sindicato_cct."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        INSERT INTO sindicato_cct (
            codigosind, nome, sigla, cnpj,
            piso_salarial, piso_data, database_mes, database_ano,
            alimentacao_valor, alimentacao_clausula,
            transporte_valor, transporte_clausula,
            url_pdf, hash_pdf, status, erro_msg, ultima_atualizacao
        ) VALUES (
            :codigosind, :nome, :sigla, :cnpj,
            :piso_salarial, :piso_data, :database_mes, :database_ano,
            :alimentacao_valor, :alimentacao_clausula,
            :transporte_valor, :transporte_clausula,
            :url_pdf, :hash_pdf, :status, :erro_msg, :ultima_atualizacao
        )
        ON CONFLICT(codigosind) DO UPDATE SET
            nome=excluded.nome, sigla=excluded.sigla, cnpj=excluded.cnpj,
            piso_salarial=excluded.piso_salarial, piso_data=excluded.piso_data,
            database_mes=excluded.database_mes, database_ano=excluded.database_ano,
            alimentacao_valor=excluded.alimentacao_valor,
            alimentacao_clausula=excluded.alimentacao_clausula,
            transporte_valor=excluded.transporte_valor,
            transporte_clausula=excluded.transporte_clausula,
            url_pdf=excluded.url_pdf, hash_pdf=excluded.hash_pdf,
            status=excluded.status, erro_msg=excluded.erro_msg,
            ultima_atualizacao=excluded.ultima_atualizacao
    """, {**data, "ultima_atualizacao": datetime.now().isoformat()})
    conn.commit()
    conn.close()


def _get_hash_atual(codigosind: int):
    """Retorna o hash_pdf armazenado para o sindicato, ou None se ainda não existe."""
    conn = sqlite3.connect(SQLITE_PATH)
    row = conn.execute(
        "SELECT hash_pdf FROM sindicato_cct WHERE codigosind = ?", (codigosind,)
    ).fetchone()
    conn.close()
    return row[0] if row else None


# ── Atualização por sindicato ─────────────────────────────────────────────────
async def atualizar_sindicato(s: dict, semaforo: asyncio.Semaphore) -> None:
    """
    Fluxo completo para um sindicato:
    1. Grava status 'pendente' se ainda não existe registro
    2. Busca PDF no Mediador
    3. Se hash igual ao armazenado → pula (sem mudança)
    4. Extrai cláusulas via Gemini
    5. Salva resultado no SQLite
    """
    cod = s["codigosind"]
    nome = s["nome"] or f"Sindicato {cod}"

    async with semaforo:
        logger.info(f"[{cod}] Iniciando atualização: {nome[:40]}")

        # Garante registro 'pendente' visível no front antes de iniciar
        hash_atual = _get_hash_atual(cod)
        if hash_atual is None:
            _upsert_sindicato({
                **s,
                "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": None, "hash_pdf": None,
                "status": "pendente", "erro_msg": None,
            })

        # 1. Busca PDF no Mediador
        cct = await buscar_cct_mte(s["cnpj"])

        if cct["erro"]:
            logger.warning(f"[{cod}] {cct['erro']}")
            _upsert_sindicato({
                **s,
                "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": None, "hash_pdf": None,
                "status": "pdf_nao_encontrado", "erro_msg": cct["erro"],
            })
            return

        # 2. Download do PDF
        pdf = await baixar_pdf(cct["url_pdf"])

        if pdf["erro"]:
            logger.warning(f"[{cod}] {pdf['erro']}")
            _upsert_sindicato({
                **s,
                "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": cct["url_pdf"], "hash_pdf": None,
                "status": "erro", "erro_msg": pdf["erro"],
            })
            return

        # 3. Verifica mudança de hash — pula se PDF igual
        if pdf["hash_md5"] == hash_atual:
            logger.info(f"[{cod}] PDF sem mudanças — pulando extração.")
            return

        # 4. Extrai texto do PDF
        try:
            texto = _extrair_texto_pdf(pdf["conteudo"])
        except Exception as e:
            msg = f"Erro ao extrair texto do PDF: {str(e)}"
            logger.error(f"[{cod}] {msg}")
            _upsert_sindicato({
                **s,
                "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": cct["url_pdf"], "hash_pdf": pdf["hash_md5"],
                "status": "erro", "erro_msg": msg,
            })
            return

        # 5. Extração via Gemini
        clausulas = await extrair_clausulas_gemini(texto, nome)

        if clausulas.get("erro"):
            _upsert_sindicato({
                **s,
                "database_ano": clausulas.get("data_base_ano"),
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": cct["url_pdf"], "hash_pdf": pdf["hash_md5"],
                "status": "erro", "erro_msg": clausulas["erro"],
            })
            return

        # 6. Salva resultado completo
        _upsert_sindicato({
            "codigosind": cod,
            "nome": nome,
            "sigla": s["sigla"],
            "cnpj": s["cnpj"],
            "piso_salarial": clausulas.get("piso_salarial") or s.get("piso_salarial"),
            "piso_data": s.get("piso_data"),
            "database_mes": clausulas.get("data_base_mes") or s.get("database_mes"),
            "database_ano": clausulas.get("data_base_ano"),
            "alimentacao_valor": clausulas.get("alimentacao_valor"),
            "alimentacao_clausula": clausulas.get("alimentacao_clausula"),
            "transporte_valor": clausulas.get("transporte_valor"),
            "transporte_clausula": clausulas.get("transporte_clausula"),
            "url_pdf": cct["url_pdf"],
            "hash_pdf": pdf["hash_md5"],
            "status": "ok",
            "erro_msg": None,
        })
        logger.info(f"[{cod}] Atualizado com sucesso.")


# ── Runner + Scheduler ────────────────────────────────────────────────────────
async def rodar_atualizacao_todos() -> None:
    """Atualiza todos os 10 sindicatos em paralelo (semáforo de 3)."""
    logger.info("=== Iniciando rodada de atualização de sindicatos ===")
    try:
        sindicatos = read_sindicatos_from_questor()
    except Exception as e:
        logger.error(f"Erro lendo Questor: {e}")
        return

    semaforo = asyncio.Semaphore(3)
    tarefas = [atualizar_sindicato(s, semaforo) for s in sindicatos]
    await asyncio.gather(*tarefas, return_exceptions=True)
    logger.info("=== Rodada concluída ===")


# Instância global do scheduler (iniciado pelo main.py via start_scheduler)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


def start_scheduler() -> None:
    """
    Inicia o agente: agenda rodada diária às 06:00 e dispara carga
    inicial imediata em background.
    """
    init_sindicato_table()

    scheduler.add_job(
        rodar_atualizacao_todos,
        trigger="cron",
        hour=6,
        minute=0,
        id="sindicato_daily",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler de sindicatos iniciado (diário às 06:00).")

    # Carga inicial imediata
    asyncio.get_event_loop().create_task(rodar_atualizacao_todos())


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler de sindicatos parado.")


# ── Leitura para API ──────────────────────────────────────────────────────────
def get_sindicatos_para_api() -> list:
    """
    Retorna os sindicatos combinando dados do Questor com os do SQLite.
    Usado pelo endpoint GET /api/sindicatos.
    """
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM sindicato_cct ORDER BY codigosind"
    ).fetchall()
    conn.close()

    if not rows:
        # Ainda não populado — retorna estrutura vazia do Questor
        sinds = read_sindicatos_from_questor()
        return [
            {
                **s,
                "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": None, "hash_pdf": None,
                "status": "pendente", "erro_msg": None,
                "ultima_atualizacao": None,
            }
            for s in sinds
        ]

    return [dict(r) for r in rows]


def get_status_agente() -> dict:
    """Retorna status do agente: próxima execução, status por sindicato."""
    prox = None
    job = scheduler.get_job("sindicato_daily")
    if job and job.next_run_time:
        prox = job.next_run_time.isoformat()

    conn = sqlite3.connect(SQLITE_PATH)
    rows = conn.execute(
        "SELECT codigosind, nome, status, erro_msg, ultima_atualizacao "
        "FROM sindicato_cct ORDER BY codigosind"
    ).fetchall()
    conn.close()

    return {
        "proxima_execucao": prox,
        "sindicatos": [
            {
                "codigosind": r[0], "nome": r[1], "status": r[2],
                "erro": r[3], "ultima_atualizacao": r[4],
            }
            for r in rows
        ],
    }
