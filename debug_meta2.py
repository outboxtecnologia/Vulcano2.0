import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import get_receitas_caixa

res = get_receitas_caixa(empresa_id=959, data_ini="2024-01", data_fim="2024-12")
meta = res.get("dashboard_meta", {}).get("RESIDENCIAL STUTTGART", {})
print("Meta Stuttgart 2024:", meta)
