# Auditoria LCTOGER X IFRS 15: Lógica de Conciliação Físico/Virtual

Esta documentação cristaliza o comportamento definitivo que forjamos no motor de reconciliação de Custos de Obra (Conta 5639 e equivalentes de Estoque).

## 1. Coluna Questor (O Físico: Motor "Dual-Fetch" Bruto)

Quando o contador lança notas fiscais, pedreiros ou materiais de construção, a regra contábil é lançar debitando **Imóveis a Comercializar (5639)** com a flag de **Centro de Custo = 35 (Stuttgart)**. 
No banco Firebird, essa operação gera espelhos tanto no `LCTOCTB` (tabela mestre sem CC) quanto no `LCTOGER` (tabela de mapeamento gerencial com CC).

A tela de Auditoria, para espelhar a "verdade física" exata, executa um *Dual-Fetch*:
- Lê **todos os lançamentos nativos do LCTOCTB** vinculados à conta 5639.
- Lê **todos os lançamentos do LCTOGER** vinculados ao Centro de Custo 35.
- Deduz os sobrepostos através da `CHAVELCTOCTB`, dando preferência à fragmentação do CC.

**Resultado:** O painel extrai tudo! Ele captura a alocação de material de construção correta (via LCTOGER) e **também captura os lançamentos que o contador esqueceu de preencher o C.C.** (que ficaram presos somente na conta, invisíveis ao módulo de custos gerenciais).

---

## 2. Coluna Vulcano 2.0 (O Societário Simulador: Injeção "Gross")

O simulador Vulcano 2.0 (que gera as provisões IFRS 15) não erra por digitação humana. Seu objetivo primário nas contas de estoque é ser uma máquina analítica inquebrável, isolando exclusivamente o Custo Físico que foi validado com Centro de Custo.

Anteriormente, o Vulcano agrupava as entradas e estornos do LCTOGER e injetava um saldo LÍQUIDO (`mov_gasto = débitos - créditos`). Resultando em totais de débito na tela aparentemente menores que os exibidos na coluna do Questor real.

**Estrutura Corrigida:**
Hoje, injetamos duas linhas sintéticas distintas (Gross Fetch) por mês:
- `mov_debito_mes`: LCTOGER Bruto mapeado como `NATURLCTOCTB = 1`.
- `mov_credito_mes`: LCTOGER Bruto mapeado como `NATURLCTOCTB = -1` (estornos ou créditos à obra).

**Resultado:** A barra de Débitos do Vulcano reflete com 100% de isonomia os débitos da obra contabilizada pelo ERP. 

---

## 3. O Fechamento Mágico de Ouros (Detecção de Erros Automática)

Devido às duas engenharias arquitetadas acima, criamos a "armadilha perfeita" de auditoria:

Se a coluna de `Débitos no Questor` na conta 5639 estiver marcando R$ 1.000.000 e a de `Débitos no Vulcano` estiver marcando R$ 900.000, e não houver divergência de saldo numérico, o raciocínio matemático imediato do sistema diz:
> **"Temos exatamente R$ 100.000 lançados manualmente na conta contábil raiz (LCTOCTB 5639) aos quais C.C. = 35 não foi devidamente amarrado."**

Na aba de detalhamento, a tela separará as transações corretas do Vulcano (com chaves LCTOGER) das "Órfãs Questor sem par" contendo sumariamente todos as N.F.'s sem centro de custo.

### Requisitos Contábeis Nativos do Vulcano IFRS 15:
- **Provisão de Custo Mês (CPV):** É gerado via `POC_NATIVO`, deduzindo da conta 5639 por crédito. 
- **Receitas POC:** São auferidas simultaneamente a essa baixa. No Vulcano, a contrapartida de CPV é deduzida artificialmente, portanto a conta 5639 sofrerá a injeção simulada dessa "Baixa de Custo" que compensará os Débitos Brutos injetados passo a passo.
