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

graph_app = workflow.compile(checkpointer=memory) # no interruptions
config = {"configurable": {"thread_id": "test_graph_555"}}

try:
    for step in graph_app.stream(estado_inicial, config, stream_mode="values"):
        if "passos_executados" in step:
            print("P->", step["passos_executados"][-1])
except Exception as e:
    import traceback
    traceback.print_exc()
