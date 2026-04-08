import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import api_contabilizacoes

res = api_contabilizacoes(ano=2024, mes=4, empresa_id=959, empreendimento_id=335)
with open('out5.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
