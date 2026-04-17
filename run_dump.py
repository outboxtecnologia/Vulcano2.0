import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from core.services.combinatorial_analyzer import IFRS15Analyzer
dossie = IFRS15Analyzer.gerar_dossie_temporal(35, 959, limite_amostra=5)
with open('RESULTADO_PYTHON_IFRS.json', 'w', encoding='utf-8') as f:
    json.dump(dossie, f, ensure_ascii=False, indent=2)
print("Saved!")
