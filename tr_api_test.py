import urllib.request
import json
req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639"}', headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    print(data.get("state", {}).keys())
except Exception as e:
    print(e)
