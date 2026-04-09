# Sindicatos CCT — Design Spec
**Data:** 2026-04-09  
**Projeto:** questor_explorer

---

## Problema

O banco Questor armazena piso salarial e data base nas tabelas `SINDNORMATIVO` e `SINDCONVENCAO`, mas **não armazena cláusulas de alimentação e transporte**. O usuário precisa visualizar essas informações a partir da CCT (Convenção Coletiva de Trabalho) real, buscada no MTE Mediador.

---

## Escopo

- 10 primeiros sindicatos (`CODIGOSIND` 0–9) da tabela `SINDICATO` do Questor
- Campos a exibir por sindicato: piso salarial, data base, alimentação (valor + trecho da cláusula), transporte (valor + trecho da cláusula)
- Agente assíncrono que roda diariamente e detecta mudanças nos PDFs das CCTs
- Carga inicial executada no startup da aplicação

---

## Arquitetura

```
Questor FDB ──► GET /api/sindicatos
                     │
                     ▼
            SQLite: tabela sindicato_cct
            (piso, alimentacao, transporte, database, url_pdf, hash_pdf, ultima_atualizacao)
                     │
                     ▼
            React: SindicatosView.jsx (cards por sindicato)

MTE Mediador ──► scraper async ──► Gemini extract ──► SQLite
                     ▲
                     │
            APScheduler (diário 06:00) + POST /api/sindicatos/atualizar
```

---

## Backend

### Novos endpoints

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/sindicatos` | GET | Retorna os 10 sindicatos com dados do Questor + CCT do SQLite |
| `/api/sindicatos/atualizar` | POST | Dispara atualização imediata (background task) |
| `/api/sindicatos/status` | GET | Status do agente (última rodada, próxima, erros por sindicato) |

### Fluxo de atualização por sindicato

1. Lê `SINDICATO.INSCRFEDERAL` (CNPJ) do Questor
2. Busca CCT no MTE Mediador via HTTP usando o CNPJ
3. Localiza e baixa o PDF da convenção mais recente
4. Calcula MD5 do PDF — se igual ao hash armazenado, encerra (sem mudança)
5. Envia PDF ao Gemini com prompt estruturado para extrair:
   - Piso salarial base (valor numérico + data de vigência)
   - Alimentação: valor ou percentual + trecho literal da cláusula
   - Transporte: valor ou percentual + trecho literal da cláusula
   - Data base (mês/ano)
6. Salva resultado no SQLite com timestamp e URL do PDF

### Agente assíncrono

- **Biblioteca:** `APScheduler` (AsyncIOScheduler)
- **Início:** `@app.on_event("startup")` — dispara uma carga inicial imediata + agenda recorrência diária às 06:00
- **Paralelismo:** `asyncio.gather` com semáforo de 3 para não sobrecarregar o Mediador
- **Log:** `backend/sindicato_agent.log`
- **Resilência:** erro em um sindicato não impede os demais; status `'erro'` salvo no SQLite com mensagem

---

## Banco de dados SQLite — tabela `sindicato_cct`

```sql
CREATE TABLE IF NOT EXISTS sindicato_cct (
  codigosind       INTEGER PRIMARY KEY,
  nome             TEXT,
  sigla            TEXT,
  cnpj             TEXT,
  piso_salarial    REAL,
  piso_data        TEXT,          -- ISO date string
  database_mes     INTEGER,       -- 1–12 do Questor (fallback)
  database_ano     INTEGER,
  alimentacao_valor    TEXT,      -- texto livre: "R$ 35,00/dia"
  alimentacao_clausula TEXT,      -- trecho literal da CCT
  transporte_valor     TEXT,
  transporte_clausula  TEXT,
  url_pdf          TEXT,
  hash_pdf         TEXT,
  status           TEXT,          -- 'ok' | 'erro' | 'pendente' | 'pdf_nao_encontrado'
  erro_msg         TEXT,
  ultima_atualizacao TEXT         -- ISO datetime
);
```

---

## Frontend — `SindicatosView.jsx`

Grade responsiva de cards, um por sindicato. Visual consistente com o estilo da app (dark, #ff4d00 accent).

### Card layout

```
┌──────────────────────────────────────────────┐
│ SITICOM                              [CCT ↗] │
│ Construção Civil Grande Fpolis               │
│ ──────────────────────────────────────────── │
│ PISO SALARIAL         R$ 2.336,00            │
│ DATA BASE             Maio / 2025            │
│ ALIMENTAÇÃO           R$ 35,00/dia           │
│   "Cláusula 12ª - VR no valor de..."        │
│ TRANSPORTE            6% do salário          │
│   "Cláusula 15ª - Vale transporte..."       │
│ ──────────────────────────────────────────── │
│ ✅ Atualizado 08/04/2026            [🔄]     │
└──────────────────────────────────────────────┘
```

### Estados visuais

- `✅ ok` — dados presentes, cor normal
- `⏳ pendente` — spinner, "Buscando CCT..."
- `⚠️ erro` — badge vermelho com mensagem resumida
- `📄 pdf_nao_encontrado` — badge amarelo, "CCT não localizada no MTE"

### Navegação

Nova entrada no sidebar da app: `NavItem` com ícone `Users` e label `"Sindicatos CCT"` → `currentView === 'sindicatos'`

---

## Restrições e decisões

- **Fonte de dados primária:** MTE Mediador (fonte oficial das CCTs)
- **Extração de cláusulas:** Gemini (já configurado no projeto via `GEMINI_API_KEY`)
- **Fallback de piso/data base:** se PDF não encontrado, usa dados do Questor (`SINDNORMATIVO.NORMATBASICO`, `SINDCONVENCAO.MESDATABASE`)
- **Sindicato 0** ("Tratamento Interno do Sistema") é incluído mas provavelmente não terá CCT — status `pdf_nao_encontrado` esperado
- **Sem mock:** extração real do Mediador desde o primeiro startup
