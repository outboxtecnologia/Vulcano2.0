import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from core.agents.auditoria_graph import workflow, memory
from langchain_core.messages import HumanMessage

estado_inicial = {
    "conta_alvo": "5639",
    "prompt_calibracao": "",
    "dossie_heuristico": {},
    "messages": [],
    "passos_executados": [],
    "resultados_db": []
}

graph_app = workflow.compile(checkpointer=memory) 
config = {"configurable": {"thread_id": "test_graph_999"}}

try:
    for event in graph_app.stream(estado_inicial, config, stream_mode="updates"):
        for node_name, state_delta in event.items():
            print("=======", node_name, "=======")
            if "passos_executados" in state_delta and state_delta["passos_executados"]:
                print(state_delta["passos_executados"][-1])
            if "messages" in state_delta and state_delta["messages"]:
                print(state_delta["messages"][-1].content[:200])
except Exception as e:
    import traceback
    traceback.print_exc()
