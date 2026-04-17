import urllib.request
import json

req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639"}', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
val = data["state"]["prompt_calibracao"]
print("Prompt End:", repr(val[-500:]))
