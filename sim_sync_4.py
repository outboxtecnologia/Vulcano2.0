import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.services.combinatorial_analyzer import IFRS15Analyzer

try:
    res = IFRS15Analyzer.gerar_dossie_temporal(35, 959, conta_alvo='Conta 5639', limite_amostra=1)
    if "dossie" in res:
        grid = res["dossie"]["amostra_unidades"][0]["grid_temporal"]
        print("Total credits on first unit in grid:", sum(m.get('credito_questor', 0) for m in grid))
        for m in grid:
            if m.get('credito_questor', 0) > 0:
                print(f"Credit in {m['ano']}-{m['mes']}: {m['credito_questor']}")
    else:
        print("No dossie", res)
except Exception as e:
    import traceback
    traceback.print_exc()
