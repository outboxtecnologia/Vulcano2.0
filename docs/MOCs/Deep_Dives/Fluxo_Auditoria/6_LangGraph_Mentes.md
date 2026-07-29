# 5. A Orquestração LangGraph (Futura V2)
A Visão de Graph Routing no Backend para Agentes que não dependem da base do Smart Importer.

**Graph Schema Visual (Agentes):**
`python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(StateDict)
builder.add_node("Investigador", agente_investigador)
builder.add_node("Revisao_HITL", nodo_humano) 
builder.add_node("Autocorrecao", nodo_auto_correcao)

# Tool do Python consumida pelo Agente:
@tool
def analisar_estoque_lctoger(cc_empreendimento: int):
    """Cruza o saldo base do centro de custo na 5639 para IFRS15."""
    ...
`

**Como funciona:**
Se os orfãos sobrarem da esteira Splink/RapidFuzz, eles caem via Roteador Condicional para o Agente Investigador. Ele ativa ferramentas passivas contra o *Firebird* puramente para ver se a auditoria os escondeu ou se precisa alocar a baixa do Questor. Se alocado, pausa no Revisao_HITL e solicita um Clique no botão Vue (Human-In-The-Loop) para persistir o SQL INSERT.
