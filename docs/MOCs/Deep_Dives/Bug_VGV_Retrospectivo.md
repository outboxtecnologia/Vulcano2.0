---
tags: [bug, vgv, poc, retrospectivo]
---

# 🐛 O Bug do VGV Retrospectivo (Venda de Unidades Prontas)

Na régua de controle do motor societário IFRS 15, o reconhecimento de receita baseia-se fortemente no andamento da obra (Avaliação POC).
Contudo, surgiu um comportamento letal num cenário específico: **Vender uma unidade num empreendimento já 100% obrado**.

## A Causa Matemática
Quando o sistema calculava a receita do mês alvo dessa nova venda, as premissas matemáticas somavam os recebimentos atemporais e abatiam com o "histórico já reconhecido". Como a obra estava em 100%, o algoritmo rateava o reconhecimento em anos anteriores inexistentes para o cliente recém chegado.

## O Sintoma Contábil (O que aparecia na tela?)
A Receita do Mês Alvo (VGV Retrospectivo) de um cara que acabou de comprar o imóvel na planta completa era violentamente **Zero** no painel de auditoria. Ou seja, as rubricas bagunçaram totalmente e a diferença "Órfã" explodiu na reconciliação paralela entre Questor x Vulcano 2.0.

## A Solução Lógica
A intervenção exigiu a **imposição de Zeros forçados** no comparativo de POC Histórico durante novas vendas em meses que o POC já bateu 100%, obrigando o Pipeline a realizar o reconhecimento financeiro retroativo imediato (Ato de Venda = Ato de Receita plena, mantendo intacta as contas atreladas de Cliente x Receita).

👉 *Retornar para* [[docs/MOCs/Formulas_e_Calculos|Fórmulas e Cálculos]]
