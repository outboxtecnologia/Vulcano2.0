from langchain_core.tools import tool
from main import get_conn
import json

@tool
def buscar_saldo_tabelas(conta_alvo: str) -> str:
    """Ferramenta para consultar saldos no Firebird Questor e Vulcano Legado."""
    try:
        conn = get_conn("questor")
        cur = conn.cursor()
        
        # Simulação simples de detecção na LANCAMENTO_CONTABIL (no real, o Investigador passaria os parêmetros).
        # A intenção é dar a ferramenta real para um agente investigar e agregar o JSON
        
        # Consulta fake de amostra (simplificada para scaffolding)
        res = f"Consulta simulada realizada para {conta_alvo}. Saldo Físico: 15.000,00"
        return json.dumps({"status": "success", "resultado": res})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@tool
def pesquisar_historico_ancora(conta_alvo: str) -> str:
    """Consulta a memória de longo prazo (Few-Shot) para verificar se existem correções prévias para esta conta."""
    # Scaffold / Mock
    if conta_alvo == "4.01.01":
        return "Historico encontrado: Usuário frequentemente altera classif para Custo Capitalizado"
    return "Nenhum histórico encontrado para esta conta."
