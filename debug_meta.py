import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import get_receitas_caixa

res = get_receitas_caixa(empresa_id=959, data_ini="2024-04", data_fim="2024-04")
meta = res.get("dashboard_meta", {}).get("RESIDENCIAL STUTTGART", {})
print("Meta Stuttgart:")
for k, v in meta.items():
    print(k, "->", v)
