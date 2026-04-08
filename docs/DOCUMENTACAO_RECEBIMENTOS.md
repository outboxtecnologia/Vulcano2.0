# Tela / Entidade: Recebimentos e Baixas

## 1. Origem de Dados: Arquitetura em Duas Vias

Este módulo lida com dados extraídos do sistema legado (`RECEBER`) combinados aos novos dados financeiros auditados numa arquitetura local SQLite (`POC_DATABASE_FILE / operacoes_baixas`).

**Colunas base mapeadas da Query (Vulcano):**
- `r.ID`: Integrador numérico central (`Integer`).
- `r.DATA`: Data do vencimento do boleto/parcela (`Date`, transformado em texto %d/%m/%Y e formato ISO).
- `TOTALPAGO`, `VALORPARCELA`, `VALORVARIACAO`, `DESCONTO`: Todos convertidos em (`Float`) tratando lixos de nulos do ERP.
- `v.DESCUNIDIMOB`, `c.CNPJ`, `c.NOME`, `e.NOME`: Strings extraídas indiretamente via join (Unidade/Cliente/Obra).
- `r.PARCELA`: Texto nominativo da série do título (`String`). Ex ("002/036").
- `r.OBS`: Campo de texto livre do ERP (`String`).

**Injeção Adicional do Motor SQLite (A Receber / Baixados):**
Ao iterar pelo lote financeiro do legacy, o servidor enxerta os campos do back-end isolado.
- `data_pagamento`: (`String/Date`) Quando foi preenchida na renegociação nova.
- `desconto_local`, `acrescimo_local`: Numéricos (`Float`).
- `status_sistema`: Computado inteligentemente (`String`).

---

## 2. Abas de Visão do Operador (O Front-end)

A tela principal se ramifica em duas **abas centrais**, cujo propósito é separar o fluxo de caixa histórico das faturas pendentes de cobrança. O front-end processa o JSON dinâmico injetando e omitindo colunas cruciais dependendo da aba ativa:

### Aba 1: "A Receber" (Títulos em Aberto)
Foca apenas em registros cujo `status_sistema` seja classificado como "ABERTO" ou ausente de pagamentos (`total_pago <= 0`).
**Colunas da grade nesta visualização:**
- `Vencimento` (Data projetada do boleto)
- `Pago` (R$ - Geralmente zerado/atrasado nesta aba)
- `Parcela` (R$ Valor Corrente)
- `Variação` (R$ - Valor inflacionado pelo índice)
- `Unidade`
- `Comprador`
- `Origem` (Sistema originador)
- `Ação` (Botão para "Dar Baixa" chamando o modal de acerto).

### Aba 2: "Histórico" (Títulos Baixados)
Foca apenas nos registros efetivados (`status_sistema` diferente de ABERTO).
**Colunas da grade nesta visualização (Note as diferenças transacionais):**
- `Vencimento` (Data original que estava previsa)
- **`Dt Pgto` (Data transacional Efetiva - EXCLUSIVA DESTA ABA)**
- `Pago` (R$ efetivado na conta)
- `Parcela` (R$ valor original)
- **`Desconto` (R$ descontos concedidos da parcela - EXCLUSIVO DESTA ABA)**
- **`Acréscimo` (R$ multas e juros acrescidos - EXCLUSIVO DESTA ABA)**
- `Unidade`
- `Comprador`
- `Origem` (Baixado Novo, Legado, etc)

---

## 3. Estrutura Exata do JSON (API Response)

**Rota Utilizada:** `GET /api/vulcano/recebimentos?empresa_id={id}&empreendimento_id={opt}&data_ini={dt}&data_fim={dt}`
**Detalhamento do Modelo Tático:** O output padroniza o merge entre o legado Vulcano e o override do Questor Explorer. As flags da tabela de "Abas" descritas acima nascem desses status:

**Exemplo de Resposta (JSON):**
```json
[
  {
    "id": 984551,
    "data": "10/05/2025",
    "vencimento_iso": "2025-05-10",
    "total": 1500.0,
    "parcela": 1350.0,
    "variacao": 150.0,
    "descricao_venda": "SALA COMERCIAL 01",
    "cliente_cnpj": "55.666.777/0001-88",
    "num_parcela": "010/120",
    "cliente": "INVESTIDORES S/A",
    "empreendimento": "TORRE CORPORATIVA",
    "obs": "Pagamento INCC atualizado",
    "desconto": 0.0,
    "data_pagamento": "2025-05-09",
    "desconto_local": 0.0,
    "acrescimo_local": 0.0,
    "status_sistema": "BAIXADO_NOVO"
  },
  {
    "id": 984552,
    "data": "10/06/2025",
    "vencimento_iso": "2025-06-10",
    "total": 0.0, 
    "parcela": 1350.0,
    "variacao": 0.0,
    "descricao_venda": "SALA COMERCIAL 01",
    "cliente_cnpj": "55.666.777/0001-88",
    "num_parcela": "011/120",
    "cliente": "INVESTIDORES S/A",
    "empreendimento": "TORRE CORPORATIVA",
    "obs": "",
    "desconto": 0.0,
    "data_pagamento": "",
    "desconto_local": 0.0,
    "acrescimo_local": 0.0,
    "status_sistema": "ABERTO"
  }
]
```

---

## 4. Regras de Paginação e Volume de Dados

- **Filtros Mandatórios:** Não há `LIMIT/OFFSET`. O front-end usa os parâmetros de `empreendimento_id`, `data_ini` e `data_fim` de forma estrita para evitar payloads imensos.
- **Scroll Client-Side:** Devido à densidade extrema de transações bancárias (dezenas de milhares de boletos), ao invés da página congelar, o fluxo é fatiado numa view Paginada de arrays (`paginatedData.slice()`) e implementa flags visíveis do balanço geral das abas `(A Receber ({qtd}))`.
