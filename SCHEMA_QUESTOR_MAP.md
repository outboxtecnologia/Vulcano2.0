# 🗺 Mapeamento de Bancos de Dados: Vulcano ↔ Questor

Este documento consolida nosso conhecimento contínuo sobre a estrutura dos bancos de dados e os cruciais relacionamentos e chaves de acesso (JOINs) entre as plataformas. Use este arquivo como a "Fonte da Verdade" para automações.

## 1. Mapeamento de Obras & CNO

### Vulcano (Gestão de Incorporadoras)
- **Tabela Base:** `EMPREENDIMENTO`  
  - `ID` (Chave Primária)
  - `NOME` (Nome do projeto Constutrutivo)
  - `CNO` (Cadastro Nacional de Obras, inserido a partir do Questor)
  - `CODIGOEMPRESA` (Referência à Filial/Empresa mãe)
- **Tabela de Estrutura Constritiva:** `BLOCO` e `UNIDADE` (Onde fica a `METRAGEMTOTAL` para fracionamento de área exigido na Receita Federal).

### Questor (Sistema Contábil/Fiscal - Firebird)
- **Tabela Base de Obras:** `OUTRAEMPRESA`  
  Apesar de se chamar "Outra Empresa", é nesta tabela que o cadastro de Obra Físico (CNO) reside.
  - `CODIGOOUTEMP` (Chave Primária)
  - `NOMEOUTEMP` (Nome da Obra)
  - `INSCRFEDERAL` (Armazena de fato o **número do CNO**)
- **Tabela de Vínculo de Empresa:** `OUTRAEMPEMP`
  - Vincula o `CODIGOOUTEMP` com o `CODIGOEMPRESA` (Ex: 959).

### 📌 Regra do Matching CNO - Sincronização
Para linkarmos Obras do Vulcano para o Questor:
1. Puxamos o `NOMEOUTEMP` no Questor (Filtrado por `CODIGOEMPRESA`).
2. Realizamos um difflib match > 0.45 com o nome do `EMPREENDIMENTO` no Vulcano.
3. Gravamos `OUTRAEMPRESA.INSCRFEDERAL` dentro de `EMPREENDIMENTO.CNO` no Vulcano.

---

## 2. Mapeamento Fiscal & Contábil

### Injeções Específicas / Rotinas DIMOB e SPED
- **Obrigações RET (4%):** Tabela `EFDINCORPIMOBRET`. Depende do "Fato Fiscal" para garantir injeção contábil do Regime Especial de Tributação.
- **Vendas de Imóveis (F200):** Tabela `EFDUNIDIMOBVENDIDA` (Realiza as baixas de parcelas e a estruturação de venda na contabilidade do Questor). O sistema Vulcano exige uma amarração do Plano de Contas prévio.

### Aferição SERO (Próximo Passo do Roadmap)
A lógica SQL a ser consolidada exige:
- `EMPREENDIMENTO` ➜ Join ➜ `BLOCO` ➜ Join ➜ `UNIDADE` no banco do Vulcano, para distribuir a responsabilidade total do CNO nos lotes/apartamentos e enviar os fracionamentos de área corretamente no web service / robô do eCac.

---

## 3. Mapeamento de Custos e POC (IFRS 15)

### Apuração do Custo Físico Real Incorrido (Questor)
As contas de custo transitórias da obra (Ex: `3.5.1...`) são agrupadas pelo Questor usando um relacionamento direto entre as tabelas contábeis e gerenciais:
- **Tabela Gerencial do Lançamento:** `LCTOGER`
  `LCTOGER` detém a chave vital `CODIGOCENTROCUSTO` (Obras) e a multiplicação polarizada de valores `(VALORLCTOGER * NATURLCTOCTB)`.
- **Tabela Matriz Contábil:** `LCTOCTB`
- **Ligação SQL do Fato (JOIN):** 
  ```sql
  LEFT JOIN LCTOCTB ON LCTOCTB.CODIGOEMPRESA = LCTOGER.CODIGOEMPRESA 
  AND LCTOCTB.CHAVELCTOCTB = LCTOGER.CHAVELCTOCTB
  ```
- **Filtro de Encerramento:** Lançamentos com `codigohistctb = 370` e `naturlctoctb = -1` (Balanços Patrimoniais) são descartados da apropriação do Gasto.

### Cálculo de DRTEE (Fração)
- O **Gasto Real Acumulado** (Questor) é apurado no período requisitado.
- No Vulcano, a Fração Indireta (`% Vendido = Área Vendida / Área Total`) é computada.
- O Custo Finalizado é: `(Gasto Real * % Vendido * Evolução POC) - Custos já lançados na própria DRTEE`.

---
> **Nota de Inteligência:** Atualizar periodicamente este arquivo toda vez que descobrirmos novas tabelas críticas relacionadas à baixa de recebíveis (`FORMA_PAGTO_QUESTOR`), deduções patronais e NF-e de concreto no Questor.
