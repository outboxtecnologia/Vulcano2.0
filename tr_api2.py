import urllib.request
import json

req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639"}', headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    state_keys = data.get("state", {}).keys()
    print("STATE KEYS:", list(state_keys))
    if "prompt_calibracao" in data.get("state", {}):
        val = data["state"]["prompt_calibracao"]
        print("prompt_calibracao found. Length:", len(val) if val else 0)
        print("Preview:", repr(val[:50]) + "...")
    else:
        print("MISSING prompt_calibracao in response state!")
except Exception as e:
    print("Request failed:", e)
