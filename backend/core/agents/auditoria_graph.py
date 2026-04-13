from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from core.agents.state import AuditoriaGraphState
from core.agents.llm_provider import get_agent_llm
from core.agents.tools import buscar_saldo_tabelas, pesquisar_historico_ancora
import sqlite3
import os

# Configuração do Checkpointer (Squad Memória)
db_path = "agente_checkpoints.sqlite"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

def historico_node(state: AuditoriaGraphState):
    llm = get_agent_llm()
    conta = state.get("conta_alvo", "")
    
    # Chama a Tool manualmente (ou via agent_executor) para fins de scaffolding
    hist = pesquisar_historico_ancora.invoke({"conta_alvo": conta})
    
    return {
        "historico_aprendizado": [{"mensagem": f"Histórico recuperado: {hist}"}],
        "passos_executados": ["historico_node executed"]
    }

def investigador_node(state: AuditoriaGraphState):
    conta = state.get("conta_alvo", "")
    
    # Aqui o agente faria o ReAct disparando tools. Para o Scaffold, damos a chamada hardcoded.
    res = buscar_saldo_tabelas.invoke({"conta_alvo": conta})
    
    return {
        "resultados_db": [{"query": "busca saldos", "resultado": res}],
        "passos_executados": ["investigador_node executed"]
    }

def avaliador_node(state: AuditoriaGraphState):
    # Aqui o LLM Pesa o Histórico e a Query DB do passo anterior e chega a uma sugestão
    sugestao = {
        "conta": state.get("conta_alvo"),
        "proposicao": "Sugerimos classificar o valor divergente como Despesa Eventual",
        "confianca": "Alta"
    }
    
    # Marcador de pausa (HITL)
    return {
        "sugestao_correcao": sugestao,
        "passos_executados": ["avaliador_node executed, waiting for approval..."]
    }

# Construindo o Grafo
workflow = StateGraph(AuditoriaGraphState)

workflow.add_node("Historiador", historico_node)
workflow.add_node("Investigador", investigador_node)
workflow.add_node("Avaliador", avaliador_node)

workflow.set_entry_point("Historiador")
workflow.add_edge("Historiador", "Investigador")
workflow.add_edge("Investigador", "Avaliador")
workflow.add_edge("Avaliador", END)  # Após o pont de pausa, o fim ou um retorno iterativo

# Compila o grafo injetando o Checkpointer e o HITL Interrupt antes de fechar o ciclo
graph_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["Avaliador"]  # Interrupção antes do nó ou 'Avaliador' pode preparar tudo e parar logo depois
    # Aqui vamos usar o interrupt_before como pedido, parando a thread antes da avaliação ou após ela.
    # No caso do plano, a aprovação vem depois da sugestão gerada, então vamos alterar a interrupt para o próximo nó.
)
