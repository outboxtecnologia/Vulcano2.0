import urllib.request
import json
req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639"}', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
val = data["state"].get("prompt_calibracao", "--NOT-FOUND--")
if val == "--NOT-FOUND--":
    print("KEY NOT FOUND")
elif not val:
    print("KEY IS EMPTY STRING")
else:
    print("PROMPT LENGTH:", len(val))
    print("PREVIEW:", repr(val[-300:]))
