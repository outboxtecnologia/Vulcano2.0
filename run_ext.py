import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.services.combinatorial_analyzer import IFRS15Analyzer
try:
    dossie = IFRS15Analyzer.gerar_dossie_temporal(35, 959, limite_amostra=5)
    print("STATUS:", dossie.get("status"))
    print("UNIDADES:", len(dossie.get("dossie", {}).get("amostra_unidades", [])))
    print("JSON PREVIEW:", json.dumps(dossie, ensure_ascii=False)[:300])
except Exception as e:
    import traceback
    traceback.print_exc()
