import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from core.agents.auditoria_graph import graph_app
from langchain_core.messages import HumanMessage

estado_inicial = {
    "conta_alvo": "5639",
    "prompt_calibracao": "",
    "dossie_heuristico": {},
    "messages": [],
    "passos_executados": [],
    "resultados_db": []
}

config = {"configurable": {"thread_id": "test_graph_123"}}
for step in graph_app.stream(estado_inicial, config, stream_mode="values"):
    print("------- PASSO -------")
    print(step.get("passos_executados", []))
