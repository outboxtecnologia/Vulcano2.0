---
tags: [ia, llm, vertex]
---

# 🤖 Árbitro de IA (Integração LLM GenAI)

Quando toda a lógica determinística falha (os valores diferem, e as descrições dos lançamentos de origem do Sienge e de destino no banco não conversam nem com regex e nem com lógica Fuzzy), o Vulcano recorre aos Grandes Modelos de Linguagem (LLM).

## Como funciona?
Passamos os arquivos brutais e emaranhados e pedimos para que o Modelo atue como um **Auditor Contábil Neutro**.

### Fluxo Obrigatório de Regras (`AGENTS.md`)
O sistema segue regras muito rígidas na API para evitar custos (Veja [[docs/MOCs/Skills_e_Agentes|as regras de Agentes]] para mais info).

1. **Vertex AI Primário**: Se rodar num ambiente na Google Cloud, utiliza conexão autenticada via Service Account (`HAS_VERTEXAI = True`).
2. **Tratamento de Pensamento (CoT)**: O modelo padrão é `gemini-2.5-flash`. A IA recebe a task com a ordem **`thinking_budget: 0`**. Como as saídas são de extração de dados JSON restritivos e não de reflexão filosófica, desligar o *Chain of Thought* corta segundos preciosos de espera e custos da operação.
3. **Threads Assíncronas**: Leituras de PDF (`pdfplumber`) e requests do LLM disparam centenas de threads simultâneas travadas por Semáforos `asyncio`, sem gargalos imperativos.

---
### 🚀 Futuro: Agenciamento Stateful com LangGraph
O projeto atual adota um fluxo linear para a IA. Contudo, nossa próxima meta arquitetural é converter toda esta camada passiva num motor de Agentes Autônomos.
👉 **Descubra o plano:** [[docs/MOCs/Deep_Dives/Roadmap_LangGraph|Acesse o Blueprint do Motor Automático]]

👉 *Retornar para* [[docs/MOCs/Logica_e_LLM|Lógica Principal]]
