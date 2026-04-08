import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.main import get_conn, get_receitas_caixa, api_contabilizacoes

res = api_contabilizacoes(ano=2024, mes=4, empresa_id=959, empreendimento_id="6400000000003")

data = res.get("data", [])
count = 0
for emp in data:
    for c in emp["contas"]:
        virtual = any(det.get("virtual") for det in c["detalhes"])
        if virtual:
            for det in c["detalhes"]:
                if det.get("virtual"):
                    print("VIRTUAL INJECTION FOUND:", det)
                    count += 1
if count == 0:
    print("NO VIRTUAL INJECTIONS FOUND")
