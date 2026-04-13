---
tags: [orfaos, backend, integridade]
---

# ⚖️ Motor de Conciliação de Órfãos

A conciliação de "Órfãos" é o ponto central onde o **Questor** (contabilidade real) entra em conflito com o **Vulcano** (motor societário em memória).

## O Problema
Na contabilidade, nem toda movimentação do sistema A entra no sistema B com a mesma data cravada, devido à falhas humanas. Exemplo: um pagamento cai no Banco num dia e é conciliado no Questor em outro. Nós chamamos um lado com saldo flutuante sem "par" no outro lado de **Lanamento Órfão**.

## Mecanismo de Ação (Endpoint `/api/auditoria/concilia-orfaos`)
1. **Varredura Paralela**: Pegamos as matrizes de Créditos e Débitos do Questor e cruzamos com as contabilidades virtuais de 2 Motores Vulcano Paralelos (o Antigo legadão versus o Novo IFRS 15).
2. **Clusterização**: Os laçamentos não conciliados diretos são jogados em um repositório isolado.
3. **Cross-Match Heurístico**: Disparado do frontend (Componente `CrossMatchPanel`), o servidor passa todos os Órfãos pelo motor [[docs/MOCs/Deep_Dives/Fuzzy_Matching|Fuzzy Matching]].
4. **Alerta Visual**: Quando existem "candidatos" possíveis (lançamentos de mesmo valor aproximado e datas próximas), ele aciona os alertas coloridos na Board, sugerindo que o Operador apenas "Aceite" a indicação da máquina para regularizar o saldo contábil estourado!

👉 *Retornar para* [[docs/MOCs/Logica_e_LLM|Lógica Principal]]
