import sys
sys.path.append('backend')
from main import get_receitas_caixa
import json

try:
    res = get_receitas_caixa(empresa_id=1)
    with open("dump.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Dumped to dump.json")
except Exception as e:
    import traceback
    traceback.print_exc()
