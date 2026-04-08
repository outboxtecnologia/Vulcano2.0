import sys
from main import api_custos_sincronizar_totalizadores

try:
    ret = api_custos_sincronizar_totalizadores(id_emp=208, mes=12, ano=2026, empresa_id=959)
    print("RESULT:", ret)
except Exception as e:
    print("EXCEPTION:", e)
