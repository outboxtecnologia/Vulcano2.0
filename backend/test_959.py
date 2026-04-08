import sys
sys.path.append('backend')
from main import get_receitas_caixa
import json

try:
    res = get_receitas_caixa(empresa_id=959)
    print("Dashboard data len:", len(res["dashboard_data"]))
    print("Meta len:", len(res["dashboard_meta"]))
except Exception as e:
    import traceback
    traceback.print_exc()
