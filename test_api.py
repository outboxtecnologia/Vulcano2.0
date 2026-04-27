import urllib.request
import json

data = json.dumps({
    "empresa_id": 959,
    "threshold": 0.38,
    "orfaos_questor": [{"conta": 123, "valor": 10.0, "historico": "Teste", "natureza": "D", "data": "2023-01-01"}],
    "orfaos_vulcano": [{"conta": 123, "valor": 10.0, "historico": "Teste", "natureza": "D", "data": "2023-01-01"}]
}).encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:8000/api/auditoria/concilia-orfaos', data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    print(response.read().decode('utf-8'))
