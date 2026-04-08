import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.main import get_conn, get_receitas_caixa

res = get_receitas_caixa(empresa_id=959, data_ini="2024-04", data_fim="2024-04")
print("dashboard_meta keys:", res.get("dashboard_meta", {}).keys())
for key, val in res.get("dashboard_meta", {}).items():
    print(key, val)

print("impostos_config:", res.get("impostos_config"))
