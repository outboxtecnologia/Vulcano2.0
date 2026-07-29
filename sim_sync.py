import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.services.combinatorial_analyzer import IFRS15Analyzer
import json

res = IFRS15Analyzer.gerar_dossie_temporal(35, 959, limite_amostra=3)
print(res["status"])
if "dossie" in res:
    print("Amostra unidades exists:", "amostra_unidades" in res["dossie"])
else:
    print("Exception message:", res)
