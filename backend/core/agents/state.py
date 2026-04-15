from typing import TypedDict, Annotated, Any
import operator

class AuditoriaGraphState(TypedDict):
    pergunta: str
    conta_alvo: str
    passos_executados: Annotated[list[str], operator.add]
    resultados_db: list[dict]
    historico_aprendizado: list[dict]
    sugestao_correcao: dict
    aprovado_pelo_usuario: bool
    feedback_usuario: str
    # Histórico de mensagens LLM para o loop ReAct
    messages: Annotated[list[Any], operator.add]
    # Contador de ciclos de autocorreção (evita loop infinito)
    tentativas_autocorrecao: int
