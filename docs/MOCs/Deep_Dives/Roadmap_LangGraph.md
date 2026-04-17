---
tags: [langgraph, agenciamento, futuro, vertex]
---

# 🚀 Roadmap de Integração: Agentes LangGraph no Vulcano

Este documento serve como blueprint (projeto arquitetônico futuro) sugerido pela IA Antigravity, visando evoluir o Vulcano de uma lógica hardcoded e estática (Scripts Python -> Chamada LLM Simples via Vertex) para um motor stateful governado por múltiplos agentes usando **LangGraph**.

## 🎯 Por que dar este salto?
A conciliação patrimonial que temos hoje esbarra no limite da "Adivinhação". Quando enviamos um texto quebrado para o LLM sem banco de dados por trás (ex: "lançamento XXX não encontrado"), o modelo assume hipóteses (One-Shot). 
Se construirmos um **Grafo Investigativo**, permitiremos ao modelo acessar as *Ferramentas do Sistema (Tools)* para interagir ativamente com o `Firebird` do Questor e cruzar os pontos antes de emitir a decisão.

---

## 🗺️ A Proposta de Arquitetura em Grafos

Ao iniciar a conciliação do mês de um empreendimento, instânciaremos um **Grafo de Estado**.

## 📋 Roadmap de Implementação (Tarefas)

Marque `[x]` quando as etapas do LangGraph forem construídas e implementadas na arquitetura.

- [x] 1. **Transformar o "Árbitro de IA" em um Agente Investigativo**
  - O Agente acessa as `Tools` e roda SQL diretamente no Banco (Firebird/SQLite) para caçar notas em vez de adivinhar.
  - ✅ Entregue: 6 tools (analisar_lancamentos_questor, verificar_receitas_custos_poc, buscar_conta_no_plano, buscar_proximidade_passivos_fiscais, analisar_estoque_lctoger, agrupar_creditos_por_apto)
- [x] 2. **Fluxos com Human-in-the-Loop (Decisão de Risco)**
  - O grafo é pausado (`Interrupt`) em conciliações de alto impacto. O sistema só avança e grava no banco após você aprovar na interface do Explorer.
  - ✅ Entregue: nodo Revisão com interrupt_before + frontend HITL modal com Aprovar/Rejeitar.
  - ✅ Entregue: **Dossiê Heurístico Temporal**: Painel visual dinâmico com tabela matriz comparando Mês-a-Mês métricas do Custo Questor vs IFRS V2 vs Fluxo vs POC/CUB para embasar a validação humana inteligente. [Ver Lousa Visual](Fluxo_Heuristico_Temporal.canvas)
- [x] 3. **Ciclos de Autocorreção Reflexiva (Self-Correction)**
  - Retorno em Loop nas extrações quebra-cabeça que quebrarem a extração de Sienge PDF. O próprio sistema avista o JSON errado, diz "quebrei" e arruma sem a mão humana.
  - ✅ Entregue: nodo AutoCorrecao + roteador _route_ferramentas + budget MAX_AUTOCORRECOES=2
- [ ] 4. **Orquestração Multi-Agente Avançada**
  - Ramificação de Especialistas: Agente Fiscal (DARFs e Guias), Agente Imobiliário (Cálculos de POC/VGV) e Agente de Síntese (Montador de JSON).

---

## 📦 Como Implementaremos

**Bibliotecas Instaladas (Base):**
- `langgraph` (Para orquestração dos Nós e Arestas)
- `langchain-core`
- `langchain-google-vertexai` (Ponte direta com noss modelo `gemini-2.5-flash` ativo).

**Conexão Base (Vertex):**
```python
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, START, END

# Já temos a Service Account no ambiente!
llm = ChatVertexAI(model="gemini-2.5-flash")

# Exemplo rudimentar estrutural futuro:
builder = StateGraph(StateDict)
builder.add_node("investigador", meu_agente_investigador)
builder.add_node("human_review", node_de_interface_humana)
builder.add_edge("investigador", "human_review")
graph = builder.compile()
```

*Este arquivo é orgânico e deve pautar a próxima etapa arquitetural quando quisermos aposentar as funções engessadas do `main.py`.*
