import sys

with open(r'backend/core/agents/tools.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_tool = '''
@tool
def dossie_amostral_unidades_vulcano(cc_empreendimento: int, empresa_id: int = 959, limite_amostra: int = 5) -> str:
    """Ferramenta Analítica. Extrai uma malha temporal hiper-estruturada de N unidades (Mês a Mês do Fluxo Financeiro, Custos e Fração).
    Útil caso o cálculo macro de 'calcular_custo_realizado_poc_metragem' falhe em explicar a diferença, permitindo ao LangGraph 
    caçar por erros de cronologia de apropriação ou estorno."""
    try:
        from core.services.combinatorial_analyzer import IFRS15Analyzer
        resultado = IFRS15Analyzer.gerar_dossie_temporal(cc_empreendimento, empresa_id, limite_amostra)
        import json
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        return f'{{"status": "error", "message": "Erro no dossie amostral: {e}"}}'
'''

if "def dossie_amostral_unidades_vulcano" not in text:
    old_list = "calcular_custo_realizado_poc_metragem,"
    new_list = "calcular_custo_realizado_poc_metragem,\n    dossie_amostral_unidades_vulcano,"
    
    text = text + "\n\n" + new_tool
    text = text.replace(old_list, new_list)
    
    with open(r'backend/core/agents/tools.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Tool dossie inserida sucesso.")
else:
    print("Tool dossie já existia.")
