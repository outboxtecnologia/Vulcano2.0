import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import api_contabilizacoes
from unittest.mock import patch

original_api = api_contabilizacoes

# This is just to test. We can't easily hook into local variables inside api_contabilizacoes without modifying main.py.
# Instead, let's just use Python to load out5.json and literally print what accounts Stuttgart actually has!
with open('out5.json', 'r', encoding='utf-8') as f:
    res = json.load(f)

for e in res.get("data", []):
    if e.get("empreendimento_id") == 335:
        print("CONTAS FOR STUTTGART:")
        for c in e.get("contas", []):
            print(f"  {c['conta']} - {c['nome']} | liq: {c['movimento_liquido']}")
            for det in c.get('detalhes', []):
                if det.get('virtual'):
                    print(f"    - Virtual: {det['natureza']} {det['valor']} -> {det['historico']}")
