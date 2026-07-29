import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.services.combinatorial_analyzer import IFRS15Analyzer

try:
    res = IFRS15Analyzer.gerar_dossie_temporal(35, 959, conta_alvo='Conta 5639', limite_amostra=5)
    for u in res["dossie"]["amostra_unidades"]:
        print(u["unidade"], "Credits:", sum(m.get('credito_questor', 0) for m in u["grid_temporal"]))
except Exception as e:
    import traceback
    traceback.print_exc()
