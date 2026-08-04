# Banco operacional do app — SQLite → Postgres (APP_DB_KIND)

O Vulcano 2.0 usa três armazenamentos:

| Dados | Onde |
|---|---|
| Questor (ERP) | Postgres (`QUESTOR_DB_KIND=postgres`, tradutor em `db_pg.py`) |
| Vulcano legado (vendas/parcelas) | Firebird (`DB_PATH_VULCANO`) |
| **Operacional do app** (baixas, projetadas, usuários, parsers, importer, conversor, SERO, POC, cross-match, memória de arraste) | **`db_app.py`**: SQLite (default) **ou** Postgres |

## Por que migrar o operacional para Postgres

No deploy (Dokploy) o SQLite fica num volume isolado do container: as baixas do
deploy não conversam com as da instância local, sem backup central e com um único
escritor. Com `APP_DB_KIND=postgres`, local e deploy compartilham o database
`vulcano2` no mesmo servidor do Questor.

## Como funciona (`backend/db_app.py`)

`connect_app()` devolve conexão com **contrato sqlite3**: placeholders `?`,
`conn.execute(...)`, `cursor.lastrowid` (via `lastval()`), `row_factory =
sqlite3.Row` (linhas por índice E nome), DDL inline traduzida
(`AUTOINCREMENT`→identity, `DATETIME`→timestamptz, `datetime('now')`→`now()`),
e reconexão automática em queda (consumidores de vida longa, ex. queue_watcher).
Todos os ~40 pontos do backend passaram a usá-lo (main.py, sync_projetadas,
graph_logic_builder, tools). Ficam fora, em arquivos SQLite próprios: janitor
(`janitor_metrics.sqlite`) e checkpoint do langgraph (`agente_checkpoints.sqlite`).

## Passo a passo para ligar o Postgres

1. **Admin do PG** (uma vez, no servidor 192.168.16.242 — `sigra_gravacao` não
   tem permissão de criar database):
   ```sql
   CREATE DATABASE vulcano2 OWNER sigra_gravacao ENCODING 'UTF8';
   ```
2. **Schema**: `python bootstrap_schema.py --target app-pg`
3. **Dados atuais**: `python migrar_app_para_pg.py` (`--dry-run` para conferir;
   idempotente — pula linhas já existentes; realinha as sequences).
4. **Ligar**: no `.env` (local e do deploy): `APP_DB_KIND=postgres`
   (+ `APP_PG_DB=vulcano2`; host/user/senha herdam de `QUESTOR_PG_*` se omitidos).
5. Reiniciar o backend. Rollback: remover/comentar `APP_DB_KIND`.

## PG PRÓPRIO do Vulcano 2.0 (decisão 03/08/2026 — não usar o servidor do Questor)

- **Local**: PostgreSQL 16 portátil em `pg16\` (gitignored), dados em `dados\pgdata`,
  porta **5433**, user `vulcano`, database `vulcano2` (senha no `.env`/`dados\pg_pw.txt`).
  O `.vbs` sobe o PG junto com Firebird e backend. Já ativo (`APP_DB_KIND=postgres`),
  com as 474 mil projetadas e usuários migrados.
- **Deploy**: adicionar um serviço `postgres:16-alpine` no compose do Dokploy com
  volume próprio e as mesmas `APP_PG_*` no backend.
- Local e deploy têm PGs separados (estados independentes); para compartilhar,
  aponte o `APP_PG_HOST` local para o PG do deploy.

## Parcelas em aberto = RECEBER.TOTALPAGO = 0 (desde 03/08/2026)

Com a base viva, o RECEBER contém todas as parcelas (abertas com `TOTALPAGO=0`).
As **projeções** (`parcelas_abertas_projetadas`) foram **desativadas** nas telas
(recebimentos, detalhe da venda, conciliador) — eliminava duplicação. Para bases
antigas sem as parcelas futuras no RECEBER, reative com `PROJETADAS_ATIVAS=1`.

## Notas de schema (PG)

- `operacoes_baixas.id_receber` é **TEXT** (recebe `prazo_<id>` das projetadas —
  no SQLite era INTEGER dinâmico).
- Datas operacionais (`data_pagamento`, `data_venc`) permanecem **texto ISO**,
  fiéis ao comportamento atual do app (comparações de string).
- Booleans como texto (`ativo` = 'T'/'F'); valores em `double precision`.
- Timestamps do SQLite são UTC naive — a migração os carrega como UTC.
