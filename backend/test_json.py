import sys
sys.path.append('backend')
from main import get_receitas_caixa
import json

try:
    res = get_receitas_caixa(empresa_id=1)
    j = json.dumps(res)
    print("Serialization OK, length:", len(j))
    print("Payload sample:", j[:200])
except Exception as e:
    import traceback
    traceback.print_exc()
