# Sindicatos CCT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exibir os 10 primeiros sindicatos do Questor com piso salarial, data base, e cláusulas de alimentação/transporte extraídas da CCT real do MTE Mediador via Gemini, com agente que atualiza diariamente.

**Architecture:** `sindicato_agent.py` centraliza toda lógica de scraping (MTE Mediador), extração (Gemini+pdfplumber) e persistência (SQLite). `main.py` expõe 3 endpoints e inicia o agente no startup via lifespan. `SindicatosView.jsx` exibe os cards; `App.jsx` adiciona a rota.

**Tech Stack:** FastAPI, APScheduler, httpx (já instalado), pdfplumber (já instalado), google-generativeai (já instalado), SQLite, React, Tailwind CSS, Lucide React

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/sindicato_agent.py` | Criar | Todo lógica: SQLite init, leitura Questor, scraping MTE, extração Gemini, scheduler |
| `backend/main.py` | Modificar | Lifespan startup, 3 novos endpoints |
| `backend/requirements.txt` | Modificar | Adicionar `apscheduler` |
| `frontend/src/SindicatosView.jsx` | Criar | Cards dos 10 sindicatos |
| `frontend/src/App.jsx` | Modificar | NavItem + rota `sindicatos` |

---

## Task 1: Instalar APScheduler e criar tabela SQLite

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/sindicato_agent.py`

- [ ] **Step 1: Instalar APScheduler**

```bash
cd C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend
pip install apscheduler
```

Expected output: `Successfully installed apscheduler-3.x.x`

- [ ] **Step 2: Adicionar ao requirements.txt**

Abrir `backend/requirements.txt` e adicionar linha:
```
apscheduler
```

- [ ] **Step 3: Criar `backend/sindicato_agent.py` com init do SQLite**

```python
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
from datetime import datetime, date
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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("sindicato_agent")

# ── SQLite ────────────────────────────────────────────────────────────────────
def init_sindicato_table() -> None:
    """Cria a tabela sindicato_cct se ainda não existir."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sindicato_cct (
            codigosind          INTEGER PRIMARY KEY,
            nome                TEXT,
            sigla               TEXT,
            cnpj                TEXT,
            piso_salarial       REAL,
            piso_data           TEXT,
            database_mes        INTEGER,
            database_ano        INTEGER,
            alimentacao_valor   TEXT,
            alimentacao_clausula TEXT,
            transporte_valor    TEXT,
            transporte_clausula  TEXT,
            url_pdf             TEXT,
            hash_pdf            TEXT,
            status              TEXT DEFAULT 'pendente',
            erro_msg            TEXT,
            ultima_atualizacao  TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Tabela sindicato_cct verificada/criada.")
```

- [ ] **Step 4: Verificar que o arquivo foi criado**

```bash
python3 -c "import sindicato_agent; print('ok')" 2>&1
```

Expected: `Tabela sindicato_cct verificada/criada.` + `ok`

---

## Task 2: Leitura dos 10 sindicatos do Questor

**Files:**
- Modify: `backend/sindicato_agent.py` (append)

- [ ] **Step 1: Adicionar função `read_sindicatos_from_questor` ao final do arquivo**

```python
# ── Questor reader ────────────────────────────────────────────────────────────
def read_sindicatos_from_questor() -> list[dict]:
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
```

- [ ] **Step 2: Testar manualmente**

```bash
cd /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend
python3 -c "
from dotenv import load_dotenv; load_dotenv('.env')
from sindicato_agent import read_sindicatos_from_questor
sinds = read_sindicatos_from_questor()
for s in sinds: print(s['codigosind'], s['nome'][:30], s['cnpj'], s['piso_salarial'])
"
```

Expected: 10 linhas com nome, CNPJ e piso de cada sindicato.

---

## Task 3: Scraper MTE Mediador

**Files:**
- Modify: `backend/sindicato_agent.py` (append)

- [ ] **Step 1: Adicionar função `_limpar_cnpj`**

```python
# ── MTE Mediador scraper ──────────────────────────────────────────────────────
def _limpar_cnpj(cnpj: str) -> str:
    """Remove pontuação do CNPJ: '12.345.678/0001-90' → '12345678000190'"""
    return re.sub(r"\D", "", cnpj or "")
```

- [ ] **Step 2: Adicionar função `buscar_cct_mte`**

```python
async def buscar_cct_mte(cnpj: str, timeout: int = 30) -> dict:
    """
    Busca a CCT mais recente no MTE Mediador pelo CNPJ do sindicato.
    Retorna dict com chaves: url_pdf (str|None), erro (str|None).
    """
    cnpj_limpo = _limpar_cnpj(cnpj)
    if not cnpj_limpo:
        return {"url_pdf": None, "erro": "CNPJ vazio"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
            # Primeiro: GET na página de busca para obter cookies/token CSRF
            resp = await client.get(MTE_SEARCH)
            resp.raise_for_status()

            # Segundo: POST com CNPJ para buscar instrumentos
            resp2 = await client.post(
                MTE_SEARCH,
                data={"cnpj": cnpj_limpo, "tipo": "CCT"},
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            )
            resp2.raise_for_status()
            html = resp2.text

            # Procura links para PDFs na resposta HTML
            # Padrão típico: href=".../.../Download?id=XXXX" ou href="...pdf"
            pdf_links = re.findall(
                r'href=["\']([^"\']*(?:Download|pdf|Arquivo)[^"\']*)["\']',
                html,
                re.IGNORECASE,
            )

            if not pdf_links:
                # Fallback: procura qualquer link que contenha "instrumento" ou "convencao"
                pdf_links = re.findall(
                    r'href=["\']([^"\']*(?:instrumento|convencao|acordo)[^"\']*)["\']',
                    html,
                    re.IGNORECASE,
                )

            if not pdf_links:
                return {"url_pdf": None, "erro": "Nenhum PDF encontrado no Mediador para este CNPJ"}

            # Pega o primeiro link (mais recente na listagem)
            url = pdf_links[0]
            if not url.startswith("http"):
                url = MTE_BASE + ("" if url.startswith("/") else "/") + url

            logger.info(f"CNPJ {cnpj_limpo}: PDF encontrado → {url}")
            return {"url_pdf": url, "erro": None}

    except httpx.HTTPStatusError as e:
        return {"url_pdf": None, "erro": f"HTTP {e.response.status_code} ao consultar Mediador"}
    except Exception as e:
        return {"url_pdf": None, "erro": f"Erro scraping Mediador: {str(e)}"}
```

- [ ] **Step 3: Adicionar função `baixar_pdf`**

```python
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
```

- [ ] **Step 4: Testar scraper com CNPJ de teste (sindicato 3)**

```bash
cd /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend
python3 -c "
import asyncio
from dotenv import load_dotenv; load_dotenv('.env')
from sindicato_agent import read_sindicatos_from_questor, buscar_cct_mte

sinds = read_sindicatos_from_questor()
# Pega sindicato 3 (SIND.BARES/HOTEIS/REST. FPOLIS)
s = sinds[3]
print('Testando CNPJ:', s['cnpj'])

async def test():
    r = await buscar_cct_mte(s['cnpj'])
    print('Resultado:', r)

asyncio.run(test())
"
```

Expected: `{'url_pdf': 'https://...', 'erro': None}` OU `{'url_pdf': None, 'erro': 'Nenhum PDF encontrado...'}`.
Ambos são respostas válidas — o importante é não ter exceção não tratada.

---

## Task 4: Extração de cláusulas via Gemini

**Files:**
- Modify: `backend/sindicato_agent.py` (append)

- [ ] **Step 1: Adicionar função `extrair_clausulas_gemini`**

```python
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
        response = await asyncio.get_event_loop().run_in_executor(
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
```

---

## Task 5: Loop principal do agente + scheduler

**Files:**
- Modify: `backend/sindicato_agent.py` (append)

- [ ] **Step 1: Adicionar função `_upsert_sindicato`**

```python
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
```

- [ ] **Step 2: Adicionar função `_get_hash_atual`**

```python
def _get_hash_atual(codigosind: int) -> str | None:
    """Retorna o hash_pdf armazenado para o sindicato, ou None se ainda não existe."""
    conn = sqlite3.connect(SQLITE_PATH)
    row = conn.execute(
        "SELECT hash_pdf FROM sindicato_cct WHERE codigosind = ?", (codigosind,)
    ).fetchone()
    conn.close()
    return row[0] if row else None
```

- [ ] **Step 3: Adicionar função `atualizar_sindicato`**

```python
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

        # Garante que existe um registro 'pendente' para exibir no front
        hash_atual = _get_hash_atual(cod)
        if hash_atual is None:
            _upsert_sindicato({
                **s, "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": None, "hash_pdf": None,
                "status": "pendente", "erro_msg": None,
            })

        # 1. Busca PDF
        cct = await buscar_cct_mte(s["cnpj"])

        if cct["erro"]:
            logger.warning(f"[{cod}] {cct['erro']}")
            _upsert_sindicato({
                **s, "database_ano": None,
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
                **s, "database_ano": None,
                "alimentacao_valor": None, "alimentacao_clausula": None,
                "transporte_valor": None, "transporte_clausula": None,
                "url_pdf": cct["url_pdf"], "hash_pdf": None,
                "status": "erro", "erro_msg": pdf["erro"],
            })
            return

        # 3. Verifica mudança de hash
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
                **s, "database_ano": None,
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
                **s, "database_ano": clausulas.get("data_base_ano"),
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
```

- [ ] **Step 4: Adicionar função `rodar_atualizacao_todos` e o scheduler**

```python
# ── Runner + Scheduler ────────────────────────────────────────────────────────
async def rodar_atualizacao_todos() -> None:
    """Atualiza todos os 10 sindicatos em paralelo (semáforo de 3)."""
    logger.info("=== Iniciando rodada de atualização de sindicatos ===")
    try:
        sindicatos = read_sindicatos_from_questor()
    except Exception as e:
        logger.error(f"Erro lendo Questor: {e}")
        return

    semaforo = asyncio.Semaphore(3)  # máx 3 requisições simultâneas ao Mediador
    tarefas = [atualizar_sindicato(s, semaforo) for s in sindicatos]
    await asyncio.gather(*tarefas, return_exceptions=True)
    logger.info("=== Rodada concluída ===")


# Instância global do scheduler (iniciado pelo main.py)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


def start_scheduler() -> None:
    """
    Inicia o agente: agenda rodada diária às 06:00 e dispara uma
    rodada imediata em background para popular os dados no startup.
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

    # Dispara carga inicial imediata em background
    asyncio.get_event_loop().create_task(rodar_atualizacao_todos())


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler de sindicatos parado.")


# ── Leitura para API ──────────────────────────────────────────────────────────
def get_sindicatos_para_api() -> list[dict]:
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
            {**s, "database_ano": None,
             "alimentacao_valor": None, "alimentacao_clausula": None,
             "transporte_valor": None, "transporte_clausula": None,
             "url_pdf": None, "hash_pdf": None,
             "status": "pendente", "erro_msg": None,
             "ultima_atualizacao": None}
            for s in sinds
        ]

    return [dict(r) for r in rows]


def get_status_agente() -> dict:
    """Retorna status do agente: próxima execução, último log."""
    prox = None
    job = scheduler.get_job("sindicato_daily")
    if job and job.next_run_time:
        prox = job.next_run_time.isoformat()

    conn = sqlite3.connect(SQLITE_PATH)
    rows = conn.execute(
        "SELECT codigosind, nome, status, erro_msg, ultima_atualizacao FROM sindicato_cct ORDER BY codigosind"
    ).fetchall()
    conn.close()

    return {
        "proxima_execucao": prox,
        "sindicatos": [
            {"codigosind": r[0], "nome": r[1], "status": r[2],
             "erro": r[3], "ultima_atualizacao": r[4]}
            for r in rows
        ],
    }
```

- [ ] **Step 5: Verificar syntax do arquivo inteiro**

```bash
cd /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend
python3 -m py_compile sindicato_agent.py && echo "OK - sem erros de syntax"
```

Expected: `OK - sem erros de syntax`

---

## Task 6: Lifespan + 3 endpoints em main.py

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Adicionar import e lifespan logo após `app = FastAPI(...)`**

Localizar a linha `app = FastAPI(title="Questor Data Explorer API")` (linha ~284) e substituir por:

```python
from contextlib import asynccontextmanager
import sindicato_agent as _sa

@asynccontextmanager
async def lifespan(app_):
    _sa.start_scheduler()
    yield
    _sa.stop_scheduler()

app = FastAPI(title="Questor Data Explorer API", lifespan=lifespan)
```

- [ ] **Step 2: Adicionar os 3 endpoints ao final de main.py (antes do último bloco `if __name__`)**

Localizar o fim do arquivo (ou o bloco `if __name__ == "__main__"`) e inserir antes dele:

```python
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
```

- [ ] **Step 3: Verificar que `BackgroundTasks` está importado**

Checar se `BackgroundTasks` já está no import do FastAPI no topo de main.py:

```bash
grep "BackgroundTasks" /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/main.py | head -3
```

Se não aparecer nenhuma linha, adicionar `BackgroundTasks` ao import existente da linha 1:
```python
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Form, BackgroundTasks
```

- [ ] **Step 4: Testar que o backend sobe sem erros**

```bash
cd /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend
python3 -m py_compile main.py && echo "Syntax OK"
```

Expected: `Syntax OK`

- [ ] **Step 5: Testar os endpoints com curl após subir o backend**

```bash
# Em terminal separado: uvicorn main:app --reload --port 8000
curl -s http://127.0.0.1:8000/api/sindicatos/status | python3 -m json.tool | head -20
curl -s http://127.0.0.1:8000/api/sindicatos | python3 -m json.tool | head -30
```

Expected para `/status`: JSON com `proxima_execucao` e lista `sindicatos`.
Expected para `/sindicatos`: lista de 10 objetos (pode ter `status: "pendente"` inicialmente enquanto o agente roda).

---

## Task 7: SindicatosView.jsx — componente React

**Files:**
- Create: `frontend/src/SindicatosView.jsx`

- [ ] **Step 1: Criar o arquivo com o componente completo**

```jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, RefreshCw, ExternalLink, AlertTriangle,
  CheckCircle2, Clock, FileX, ChevronDown, ChevronUp
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";

const MESES = [
  '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

function StatusBadge({ status }) {
  const map = {
    ok:                { icon: <CheckCircle2 size={12} />, label: 'Atualizado',          cls: 'text-[#34c759] border-[#34c759]/30 bg-[#34c759]/10' },
    pendente:          { icon: <Clock size={12} className="animate-pulse" />, label: 'Buscando CCT...', cls: 'text-[#ffcc00] border-[#ffcc00]/30 bg-[#ffcc00]/10' },
    erro:              { icon: <AlertTriangle size={12} />, label: 'Erro',                cls: 'text-[#ff4d00] border-[#ff4d00]/30 bg-[#ff4d00]/10' },
    pdf_nao_encontrado:{ icon: <FileX size={12} />, label: 'CCT não encontrada',        cls: 'text-[#888] border-[#888]/30 bg-[#888]/10' },
  };
  const cfg = map[status] || map.pendente;
  return (
    <span className={`flex items-center gap-1 text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-sm border ${cfg.cls}`}>
      {cfg.icon}{cfg.label}
    </span>
  );
}

function ClausulaExpand({ texto }) {
  const [aberto, setAberto] = useState(false);
  if (!texto) return null;
  const curto = texto.slice(0, 100);
  return (
    <div className="mt-1">
      <p className="text-[10px] text-[#555] italic leading-relaxed">
        "{aberto ? texto : curto}{!aberto && texto.length > 100 ? '...' : ''}"
      </p>
      {texto.length > 100 && (
        <button
          onClick={() => setAberto(v => !v)}
          className="flex items-center gap-1 text-[9px] text-[#ff4d00]/60 hover:text-[#ff4d00] mt-1 transition-colors"
        >
          {aberto ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          {aberto ? 'Menos' : 'Ver trecho completo'}
        </button>
      )}
    </div>
  );
}

function InfoRow({ label, valor, clausula }) {
  return (
    <div className="py-2 border-b border-white/5 last:border-0">
      <div className="flex justify-between items-start gap-2">
        <span className="text-[10px] font-black uppercase tracking-widest text-[#555]">{label}</span>
        <span className="text-[11px] font-bold text-white text-right">
          {valor || <span className="text-[#333] italic">—</span>}
        </span>
      </div>
      <ClausulaExpand texto={clausula} />
    </div>
  );
}

function SindicatoCard({ s, onAtualizar }) {
  const dataBase = s.database_mes
    ? `${MESES[s.database_mes]}${s.database_ano ? ' / ' + s.database_ano : ''}`
    : null;

  const piso = s.piso_salarial
    ? `R$ ${Number(s.piso_salarial).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
    : null;

  const dt = s.ultima_atualizacao
    ? new Date(s.ultima_atualizacao).toLocaleDateString('pt-BR')
    : null;

  return (
    <div className="bg-black/40 border border-white/5 rounded-sm hover:border-[#ff4d00]/20 transition-all duration-300 p-5 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-black text-[#ff4d00] uppercase tracking-widest mb-1">
            {s.sigla || `SIND-${s.codigosind}`}
          </p>
          <h3 className="text-sm font-black text-white leading-tight">
            {s.nome || `Sindicato ${s.codigosind}`}
          </h3>
          {s.cnpj && (
            <p className="text-[9px] text-[#444] mt-1 font-mono">{s.cnpj}</p>
          )}
        </div>
        {s.url_pdf && (
          <a
            href={s.url_pdf}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 p-1.5 bg-white/5 border border-white/10 rounded-sm hover:border-[#ff4d00]/40 hover:bg-[#ff4d00]/10 transition-all"
            title="Abrir CCT"
          >
            <ExternalLink size={12} className="text-[#888] hover:text-[#ff4d00]" />
          </a>
        )}
      </div>

      {/* Dados */}
      <div className="bg-black/20 rounded-sm px-3 py-1">
        <InfoRow label="Piso Salarial" valor={piso} />
        <InfoRow label="Data Base" valor={dataBase} />
        <InfoRow
          label="Alimentação"
          valor={s.alimentacao_valor}
          clausula={s.alimentacao_clausula}
        />
        <InfoRow
          label="Transporte"
          valor={s.transporte_valor}
          clausula={s.transporte_clausula}
        />
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-1">
        <StatusBadge status={s.status} />
        <div className="flex items-center gap-2">
          {dt && <span className="text-[9px] text-[#444]">{dt}</span>}
          <button
            onClick={() => onAtualizar(s.codigosind)}
            className="p-1.5 bg-white/5 border border-white/5 rounded-sm hover:border-[#ff4d00]/40 hover:text-[#ff4d00] text-[#555] transition-all"
            title="Forçar atualização"
          >
            <RefreshCw size={11} />
          </button>
        </div>
      </div>

      {/* Erro inline */}
      {s.erro_msg && (
        <p className="text-[9px] text-[#ff4d00]/60 border border-[#ff4d00]/10 bg-[#ff4d00]/5 px-2 py-1 rounded-sm leading-relaxed">
          {s.erro_msg}
        </p>
      )}
    </div>
  );
}

export function SindicatosView() {
  const [sindicatos, setSindicatos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [atualizando, setAtualizando] = useState(false);
  const [erro, setErro] = useState(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro(null);
    try {
      const resp = await fetch(`${API_BASE}/api/sindicatos`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setSindicatos(Array.isArray(data) ? data : []);
    } catch (e) {
      setErro(`Erro ao carregar sindicatos: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
    // Polling a cada 15s enquanto houver sindicatos pendentes
    const interval = setInterval(() => {
      setSindicatos(prev => {
        const temPendente = prev.some(s => s.status === 'pendente');
        if (temPendente) carregar();
        return prev;
      });
    }, 15000);
    return () => clearInterval(interval);
  }, [carregar]);

  const handleAtualizar = async () => {
    setAtualizando(true);
    try {
      await fetch(`${API_BASE}/api/sindicatos/atualizar`, { method: 'POST' });
      // Polling começa automaticamente
      setTimeout(carregar, 2000);
    } finally {
      setTimeout(() => setAtualizando(false), 3000);
    }
  };

  const pendentes = sindicatos.filter(s => s.status === 'pendente').length;
  const comErro = sindicatos.filter(s => s.status === 'erro').length;
  const ok = sindicatos.filter(s => s.status === 'ok').length;

  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-headline text-2xl font-black tracking-tighter text-white uppercase">
            Sindicatos — CCT
          </h2>
          <p className="text-[10px] text-[#555] uppercase tracking-widest mt-1">
            Convenções Coletivas via MTE Mediador · {sindicatos.length} sindicatos
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Contadores */}
          <div className="flex gap-2 text-[9px] font-black uppercase tracking-widest">
            {ok > 0 && <span className="px-2 py-1 bg-[#34c759]/10 border border-[#34c759]/20 text-[#34c759] rounded-sm">{ok} ok</span>}
            {pendentes > 0 && <span className="px-2 py-1 bg-[#ffcc00]/10 border border-[#ffcc00]/20 text-[#ffcc00] rounded-sm">{pendentes} buscando</span>}
            {comErro > 0 && <span className="px-2 py-1 bg-[#ff4d00]/10 border border-[#ff4d00]/20 text-[#ff4d00] rounded-sm">{comErro} erro</span>}
          </div>
          <button
            onClick={handleAtualizar}
            disabled={atualizando}
            className="flex items-center gap-2 px-4 py-2 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded-sm hover:bg-white transition-all disabled:opacity-50"
          >
            <RefreshCw size={12} className={atualizando ? 'animate-spin' : ''} />
            {atualizando ? 'Atualizando...' : 'Atualizar CCTs'}
          </button>
        </div>
      </div>

      {/* Erro global */}
      {erro && (
        <div className="border border-[#ff4d00]/30 bg-[#ff4d00]/5 text-[#ff4d00] text-xs font-bold px-4 py-3 rounded-sm">
          {erro}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-20">
          <RefreshCw className="animate-spin text-[#ff4d00]" size={28} />
        </div>
      )}

      {/* Grid de cards */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
          {sindicatos.map(s => (
            <SindicatoCard key={s.codigosind} s={s} onAtualizar={handleAtualizar} />
          ))}
          {sindicatos.length === 0 && (
            <div className="col-span-full text-center py-20 text-[#444] uppercase tracking-widest text-xs">
              Nenhum sindicato carregado ainda.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar que o arquivo foi criado sem erros de lint óbvios**

```bash
grep -c "export function SindicatosView" /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/frontend/src/SindicatosView.jsx
```

Expected: `1`

---

## Task 8: Adicionar rota em App.jsx

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Adicionar import do SindicatosView**

Localizar o bloco de imports no topo de `App.jsx` (por volta da linha 12) e adicionar:

```js
import { SindicatosView } from './SindicatosView';
```

- [ ] **Step 2: Adicionar `Users` ao import de lucide-react** (se não estiver)

Verificar:
```bash
grep "Users" /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/frontend/src/App.jsx | head -3
```

Se `Users` já está no import, pular. Se não, adicionar `Users` ao import existente de lucide-react.

- [ ] **Step 3: Adicionar NavItem no sidebar**

Localizar o grupo "Enterprise Suite" no sidebar (em torno da linha 251) e adicionar o novo item **antes** do `Raw Explorer`:

```jsx
<NavItem icon={<Users size={16}/>} label="Sindicatos CCT" active={currentView === 'sindicatos'} onClick={() => setCurrentView('sindicatos')} />
```

- [ ] **Step 4: Adicionar rota no bloco de views**

Localizar o bloco de `{currentView === 'explorer' && ...}` (em torno da linha 337) e adicionar ao lado:

```jsx
{currentView === 'sindicatos' && <SindicatosView />}
```

- [ ] **Step 5: Verificar no browser**

```bash
cd /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/frontend
npm run dev
```

Abrir `http://localhost:5173`, clicar em "Sindicatos CCT" no sidebar. Deve aparecer a grade de cards com status "Buscando CCT..." enquanto o agente roda em background.

- [ ] **Step 6: Commit final**

```bash
cd /c/Users/dirfe/.gemini/antigravity/scratch/questor_explorer
git add backend/sindicato_agent.py backend/main.py backend/requirements.txt frontend/src/SindicatosView.jsx frontend/src/App.jsx docs/
git commit -m "feat: sindicatos CCT — scraping MTE Mediador + extração Gemini + agente diário"
```

---

## Self-Review

**Spec coverage:**
- ✅ 10 sindicatos do Questor → Task 2
- ✅ Piso salarial, data base do Questor → Task 2 (fallback)
- ✅ Alimentação e transporte extraídos da CCT real → Task 4
- ✅ Interface com cards → Task 7
- ✅ Agente assíncrono diário → Task 5
- ✅ Carga inicial no startup → Task 5 (`start_scheduler` dispara `create_task`)
- ✅ Status visual por card (pendente/ok/erro/pdf_nao_encontrado) → Task 7
- ✅ Botão de atualização manual → Task 7 + Task 6
- ✅ Fallback Questor quando PDF não encontrado → Task 5 (`piso_salarial` usa valor do Questor se Gemini não retornar)

**Type consistency:**
- `_sa.rodar_atualizacao_todos` → definido em Task 5, usado em Task 6 ✅
- `_sa.get_sindicatos_para_api` → definido em Task 5, usado em Task 6 ✅
- `_sa.get_status_agente` → definido em Task 5, usado em Task 6 ✅
- `_sa.start_scheduler` / `_sa.stop_scheduler` → definido em Task 5, usado em Task 6 ✅
- `SindicatosView` (named export) → definido em Task 7, importado em Task 8 ✅

**Placeholders:** nenhum.
