import sys, json
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import api_saldo_contas

res = api_saldo_contas(empresa_id=959, mes=2, ano=2025, contas="4910", empreendimento_id="335")
print(json.dumps(res, indent=2))
