import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import api_contabilizacoes
import traceback

print("Calling APICONT...")
try:
    res = api_contabilizacoes(ano=2024, mes=4, empresa_id=959, empreendimento_id=None)
    print("Success! Keys:", res.keys())
    print("Data length:", len(res.get("data", [])))
except Exception as e:
    print("CRASH IN API:")
    traceback.print_exc()
