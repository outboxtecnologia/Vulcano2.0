from main import get_conn
import asyncio
from core.agents.auditoria_graph import graph_app
from main import AuditoriaGraphState, _serialize_agent_state
import uuid

async def test_graph():
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = AuditoriaGraphState(
        pergunta="Auditoria de rotina iniciada",
        conta_alvo="Conta 5639 - RECEITA DE VENDA",
        passos_executados=[],
        resultados_db=[],
        historico_aprendizado=[],
        sugestao_correcao={},
        aprovado_pelo_usuario=False,
        feedback_usuario="",
        prompt_calibracao="",
        messages=[],
        tentativas_autocorrecao=0,
    )
    res = graph_app.invoke(initial_state, config)
    state = graph_app.get_state(config)
    print("KEYS EXPORTED: ", res.keys())
    if "prompt_calibracao" in res:
        print("prompt_calibracao LENGTH: ", len(res["prompt_calibracao"]))
    else:
        print("NO prompt_calibracao IN RES!")

asyncio.run(test_graph())
