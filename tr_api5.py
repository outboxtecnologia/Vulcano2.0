import urllib.request
import json
req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639"}', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))

state = data.get("state", {})
dossie_heuristico = state.get("dossie_heuristico")
prompt_calibracao = state.get("prompt_calibracao")

print("Dossie Heuristico Type:", type(dossie_heuristico), "Size:", len(dossie_heuristico) if dossie_heuristico else 0)
print("Dossie keys:", dossie_heuristico.keys() if isinstance(dossie_heuristico, dict) else None)
if dossie_heuristico and "dossie" in dossie_heuristico:
    print("Has dossie data:", bool(dossie_heuristico["dossie"]))
else:
    print("NO DOSSIE KEY IN DICT!")
