import requests
import json

try:
    resp = requests.post("http://localhost:8000/api/agentes/iniciar_auditoria", json={"conta_alvo": "Conta 5639"})
    data = resp.json()
    print("STATUS_CODE:", resp.status_code)
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
