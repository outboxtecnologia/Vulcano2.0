from main import api_saldo_contas
import json
res = api_saldo_contas(empresa_id=959, mes=1, ano=2026, contas="4845,4910,4995,5855,5866", empreendimento_id="19")
print(json.dumps(res, indent=2))
