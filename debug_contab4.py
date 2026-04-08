import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import api_contabilizacoes

res = api_contabilizacoes(ano=2024, mes=4, empresa_id=959, empreendimento_id=None)

for emp in res.get("data", []):
    print("Empreendimento:", emp.get("empreendimento_nome"))
    for conta in emp.get("contas", []):
        for det in conta.get("detalhes", []):
            if det.get("virtual"):
                print("   VIRTUAL:", conta.get("nome"), "->", det)
