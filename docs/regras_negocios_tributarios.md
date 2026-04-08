# Base de Conhecimento: Receita Societária (POC) vs Fiscal (Caixa)

Este documento guarda as regras de negócio vitais relacionadas ao processamento das receitas imobiliárias no Questor Explorer.

## 1. Princípio da Receita Operacional (Acréscimos)
Historicamente, o cálculo da **Receita Societária (POC)** costumava se basear apenas no *Valor Geral de Vendas (VGV)* do contrato original. Contudo, a regra de negócio atualizada exige que:

> **Regra:** Todos os acréscimos pagos pelos clientes (juros, multas, correções monetárias, taxas de atraso) configuram **Receita Operacional** legítima. 
> 
> **Impacto no Societário:** Esses acréscimos **devem ser somados** à base de cálculo do Societário (junto ao VGV original e progresso do POC). Se um cliente pagou acréscimos que superam o VGV da fração, o teto do cômputo societário não deve ser limitado cegamente ao VGV estático do contrato, pois a receita operacional final do empreendimento aumentou.

## 2. Motor de POC Congelado (Obras Concluídas)
- Obras sinalizadas como concluídas (`S`) possuem o seu progresso físico cravado em **100%**.
- A competência *Mensal* ("soc_mes") de uma obra concluída no passado resultará sempre em R$ 0,00 no presente, visto que 100% do VGV operacional já foi reconhecido até a data do encerramento da obra.
- Nestes cenários, a auditoria do cliente baseia-se unicamente no bloco de Receita Societária **Acumulada** (Lifetime).

## 3. Lógica do Diferimento/Adiantamento Contábil
- O Diferimento/Adiantamento exibido na interface deve ser calculado estritamente pela equação:  
  `Diferimento = Caixa Acumulado - Societário Acumulado`
- Esta visão consolidada (Lifetime) é a única que reflete se o cliente adiantou pagamento (Caixa > Societário reconhecido) ou se a construtora reconheceu mais avanço físico do que recebeu (Societário > Caixa).