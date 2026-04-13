---
tags: [llm, ia, vertex, fuzzy]
---

# 🧠 Lógica Analítica, IA e Heurísticas

A arquitetura de inteligência do Vulcano 2.0 não depende exclusivamente de Inteligência Artificial generativa. Ela adota uma abordagem em camadas (Triage Layering), onde algoritmos clássicos hiper-velozes filtram o ruído antes de invocar os modelos neurais.

### 🔀 Camada 1: Pareamento Probabilístico e Fuzzy matching
Antes de consumir tokens das APIs de IA, o sistema tenta inferir correspondências de contas contábeis e lançamentos financeiros usando técnicas de **Fuzzy Matching**.
👉 **Clique para aprofundar:** [[docs/MOCs/Deep_Dives/Fuzzy_Matching|O que é e como funciona a Lógica Fuzzy no Vulcano?]]

### ⚖️ Camada 2: O Motor de Conciliação de Órfãos
Quando existem lançamentos contábeis no Questor que não conversam com o Vulcano Legado ou com o IFRS 15, entra em cena a Conciliação de Órfãos.
👉 **Clique para aprofundar:** [[docs/MOCs/Deep_Dives/Conciliacao_Orfaos|Como o sistema lida com lançamentos "Órfãos"?]]

### 🤖 Camada 3: Árbitro de IA (Integração LLM GenAI)
Quando as regras determinísticas e a lógica Fuzzy falham, delegamos a decisão a um modelo de linguagem para atuar como Juiz Arbitral contábil.
👉 **Clique para aprofundar:** [[docs/MOCs/Deep_Dives/LLM_Arbitrator|Integração do LLM via Vertex AI e Gemini]]
