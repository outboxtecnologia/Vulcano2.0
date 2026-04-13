from typing import TypedDict, Annotated
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
