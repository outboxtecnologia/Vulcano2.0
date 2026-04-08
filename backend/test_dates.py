import sys
sys.path.append('backend')
from main import get_receitas_caixa
import json

try:
    res = get_receitas_caixa(empresa_id=1, data_ini="2025-01-01", data_fim="2025-01-31")
    d1 = res.get("dashboard_data", [])
    print("Items with dates:", len(d1))
    
    res2 = get_receitas_caixa(empresa_id=1, data_ini=None, data_fim=None)
    d2 = res2.get("dashboard_data", [])
    print("Items without dates:", len(d2))
except Exception as e:
    import traceback
    traceback.print_exc()
