# Fiscal / SPED — Guias RET e F200 (tela FiscalSpedView)

> Fluxo ponta-a-ponta das abas **RET** e **F200** da tela Fiscal/SPED.
> Motores: `backend/injector_sped.py::processar_ret` e `::processar_f200` ·
> Rotas: `GET/POST /api/sped/{ret|f200}/{preview|commit}` ·
> Tela: `frontend/src/FiscalSpedView.jsx`.
> Regra de ouro: **cada parcela recebida vai para exatamente UM bloco** — obra optante
> do RET (a partir de `DATAINICIORET`) → bloco 1800 (`EFDINCORPIMOBRET`); todo o resto
> → F200 comum (`EFDUNIDIMOBVENDIDA`). Os dois motores usam o MESMO critério, invertido.

## Regra de seleção (o que entra na apuração)

Recebimentos (`RECEBER.TOTALPAGO > 0`) da competência (mês/ano pela data da parcela),
somados por empreendimento, **apenas** de obras optantes:

- `EMPREENDIMENTO.RET = 'S'` (opt-in cadastrado na Aba Fiscal/RET do empreendimento —
  ver `docs/DOCUMENTACAO_EMPREENDIMENTOS.md`);
- respeitando `DATAINICIORET` (parcelas anteriores à adesão ficam de fora);
- excluindo vendas distratadas (`VENDA.DISTRATO = 'S'`);
- alíquota por obra: `EMPREENDIMENTO.ALIQRET` (fallback 4%). Existem obras a 1% (PMCMV).

## Cálculo

- `BCRET` (base) = Σ `TOTALPAGO` da obra na competência.
- `RECFINRET` (receita financeira) = Σ `VALORVARIACAO` (juros/correção — no vulcano,
  `TOTALPAGO = VALORPARCELA + VALORVARIACAO`); `RECRECEBRET` = base − financeira.
- `VLRECUNI` (guia unificada) = `BCRET × ALIQRET`.
- Composição exibida na tela (informativa; a guia é unificada):
  - 4%: PIS 0,37 · COFINS 1,71 · CSLL 0,66 · IRPJ 1,26
  - 1% (PMCMV): PIS 0,09 · COFINS 0,44 · CSLL 0,16 · IRPJ 0,31
  - outras alíquotas: rateio proporcional à composição dos 4%.

## Mapeamento obra → Questor (de-para derivado do histórico)

Cada obra vira uma linha em `EFDINCORPIMOBRET` amarrada a um **estabelecimento**
(`CODIGOESTAB` + `CNPJINCIMOB` = CNPJ da filial da incorporação). O de-para é derivado
do **histórico já lançado** na própria `EFDINCORPIMOBRET` (o escritório lançava
manualmente): match do nome da obra (`EMPREENDIMENTO.NOME`) contra `INCIMOB`,
normalizado (maiúsculas, sem acento, espaços colapsados); o lançamento mais recente
fornece também `CODIGOIMPOSTO` (4095), `VARIACAOIMPOSTO`, `FORMAFATURAMENTO` (501) e
`CODIGOTABCTBFIS`.

**Consequência**: obra nova (sem nenhum lançamento histórico) aparece como
`SEM DE-PARA` — o primeiro lançamento dela deve ser manual no Questor; do segundo mês
em diante o sistema mapeia sozinho.

## Status por obra (preview)

| Status | Significado | No commit |
|---|---|---|
| `PRONTO` | calculada e mapeada | é inserida |
| `JÁ LANÇADO` | já existe linha p/ o estab na competência | pulada (idempotência — nunca duplica) |
| `SEM DE-PARA` | sem histórico no Questor | pulada; exige 1º lançamento manual |

## Colunas gravadas (commit)

`CODIGOEMPRESA` (= código da empresa no vulcano, igual ao Questor), `CODIGOESTAB`,
`DATALCTOFIS` = **1º dia da competência**, `SEQ` = próximo por estab/data,
`CNPJINCIMOB`, `INCIMOB` (nome histórico), `RECRECEBRET`, `RECFINRET`, `BCRET`,
`ALIQRET`, `VLRECUNI`, `DTRECUNI` = **dia 20 do mês seguinte**, `CODIGOIMPOSTO`,
`VARIACAOIMPOSTO`, `FORMAFATURAMENTO`, `CODIGOTABCTBFIS`, `ORIGEMDADO = 2`.
PK real: `(CODIGOEMPRESA, CODIGOESTAB, DATALCTOFIS, SEQ)`.

## Validação (31/07/2026)

Empresa 2147, competência 01/2026: 9 obras optantes apuradas; **7 bateram ao centavo**
com os lançamentos manuais do escritório (ex.: GARDEN CLUB II R$ 4.236.131,29). As 2
divergências (GARDEN HOME RESORT +6,9k; BOSQUE MILANO +161,6k) são compatíveis com
baixas ajustadas após o lançamento manual — conferir na virada de competência.

---

# Aba F200 — Receita imobiliária por unidade vendida

## Regra de seleção

Recebimentos da competência agregados por **venda/unidade** (`RECEBER × VENDA`),
excluindo distratos e **excluindo parcelas de obras optantes do RET** (`RET='S'` a
partir de `DATAINICIORET` — essas vão pelo bloco 1800). Validado nos dados: a diferença
vulcano × Questor fecha em 0,00 nas empresas 95 e 1505 exatamente com esse filtro.

## De-para unidade → Questor (campos-espelho da VENDA)

A `VENDA` do vulcano carrega espelho do Questor: `NUMCADIMOB` + `CODIGOESTAB` (match
95-99,5% com o PG), além de `INDOPER`, `UNIDIMOB`, `DESCUNIDIMOB`, `INDNATEMP`, `CNPJ`.
A chave é sempre `(CODIGOEMPRESA, CODIGOESTAB, NUMCADIMOB)` — `NUMCADIMOB` é sequência
POR ESTAB e colide entre estabs (não usar sozinho).

## Tabelas gravadas

1. `EFDUNIDIMOBILIARIA` (cadastro da unidade, PK empresa+estab+numcadimob) — inserida
   junto quando a unidade ainda não existe (`NOVO_CADASTRO`): identemp = obra em caixa
   alta, CPF/CNPJ do adquirente COM máscara, infcomp = nome do adquirente, origemdado 2.
2. `EFDUNIDIMOBVENDIDA` (movimento mensal, PK +compreceb) — `COMPRECEB` = 1º dia do
   mês; `VLTOTREC` = recebido no mês; `VLRECACUM` = encadeado do último lançamento
   anterior no Questor (fallback: acumulado do vulcano); `VLBC` = `VLTOTREC`;
   `PERCRECRECEB` = (acum+mês)/total da venda ×100 (pode passar de 100 c/ juros);
   `CSTPIS`/`CSTCOFINS` = 1; `CONSIDERAPROPORC` = '1'; `APURAECF` = '1'; origemdado 2.

## Regime tributário — herdado do histórico, nunca hardcoded

| Regime | Alíquotas | `TIPODEBITO` | `OPERACAOFIS` IRPJ/CSLL |
|---|---|---|---|
| Presumido (cumulativo) | PIS 0,65 / COFINS 3,00 | `4.3.05.54` | preenchidos |
| Real (não-cumulativo) | PIS 1,65 / COFINS 7,60 | `4.3.05.04` | NULL |

Template herdado do **último lançamento da própria unidade** (fallback: último da
empresa) — cobre a empresa 95, que convive com os dois regimes por empreendimento.

## Status por unidade

`PRONTO` (insere) · `NOVO_CADASTRO` (insere pai+filha) · `JÁ LANÇADO` (pulada —
idempotência) · `SEM_ESPELHO` (VENDA sem NUMCADIMOB — corrigir no vulcano) ·
`SEM_TEMPLATE` (empresa nunca usou F200 — 1º mês manual para fixar o regime).

## Validação (31/07/2026)

- Empresa 2803 (VERBENA ATLANTIC), 01/2026: 18 unidades, total R$ 808.244,97 —
  **centavo a centavo** com os lançamentos manuais; regime presumido detectado.
- Empresa 95, 01/2026: 138 unidades, nenhuma obra RET vazando para o F200.

---

# Telas do analista (layouts herdados do sistema legado)

Reproduzem as telas de trabalho do sistema anterior ("Arquivo Contabilidade"):

1. **Recebimentos — Mensal** (menu `Receb. Mensal`, `RecebimentosMensalView.jsx` +
   `GET /api/vulcano/recebimentos-mensal?empresa_id&ano&mes[&empreendimento_id]`):
   seleção por **mês de referência** (navegação ◀ ▶) e empreendimento; lista as
   parcelas do mês **mais** as abertas vencidas, com as colunas legadas: Nº (venda),
   CPF/CNPJ, Comprador, Unidade, Vlr Venda, Saldo Ant. (antes do mês), Data Pagto
   (das baixas novas — o legado não guarda a data no FDB), Valor Parcela, Desconto,
   Variação, Total Pago, Saldo Atual, Parcela, Observação; totais no rodapé
   (saldo atual somado por venda, sem duplicar). **Baixa inline**: clicar numa
   parcela em aberto abre Data/Valor/Variação/Desconto na própria linha (Enter
   salva, Esc cancela) → grava via `POST /api/vulcano/recebimentos/baixa`
   (`operacoes_baixas` no SQLite; total = valor + variação − desconto) e a visão
   funde as baixas novas (status PAGO, saldo da venda reduzido).
2. **Quadro Resumo** (aba na tela Fiscal/SPED, `GET /api/sped/resumo`): por
   empreendimento — Recebimentos, Valor Parcela, Variação, Distrato (vendas
   distratadas no mês via `DATADISTRATO`), Base/PIS/COFINS do F200 e Base/Valor do
   RET, com linha de totais. Une os previews dos dois motores; cada obra aparece em
   UM dos lados (regra de ouro RET×F200).
3. **Analítico F200/1800** (abas RET e F200 da mesma tela): os registros exatos que
   serão populados no Questor — F200 por unidade (cliente, data/total da venda,
   acumulado, parcela, variação, PIS/COFINS) e 1800 por obra (estab, alíquota, base,
   valor da guia) — com status de injeção por linha.

---

# Limitações conhecidas / pendências (RET e F200)

1. **Competência pelo vencimento da parcela** (`RECEBER.DATA`), não pela data do
   pagamento real — parcela baixada com atraso entra no mês do vencimento.
2. Os commits gravam direto na base **de produção** do Questor (PG 192.168.16.242) —
   só linhas novas, nunca alteram/duplicam; ainda assim, conferir o preview antes.
3. Base vulcano local é cópia de 24/04/2026 (baixas até fev) — para competências
   recentes, apontar `DB_PATH_VULCANO` para a base viva.
4. Stub legado `POST /api/fiscal/ret` (main.py) retorna simulação — não usar.
5. F205/F210 (custo orçado/incorrido) não são gerados — praticamente sem uso no
   histórico (0 e 1 linha).
