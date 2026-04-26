"""Testa o endpoint api_sero_maodeobra diretamente, sem uvicorn."""
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

# Simula o contexto do main
from main import api_sero_maodeobra

print("=== Testando api_sero_maodeobra (empresa=959, ano=2026, mes=01) ===")
try:
    result = api_sero_maodeobra(empresa_id=959, ano=2026, mes=1)
    import json
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    import traceback; traceback.print_exc()
