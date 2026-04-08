import sys
sys.path.append('backend')
from main import get_receitas_caixa

res = get_receitas_caixa(empresa_id=1, data_ini="2025-01-01", data_fim="2025-01-31")
print("dashboard_data len:", len(res["dashboard_data"]))
print("dashboard_meta len:", len(res["dashboard_meta"]))

total_unidades = sum(len(m["unidades"]) for m in res["dashboard_meta"].values())
print("total_unidades inside dashboard_meta:", total_unidades)
