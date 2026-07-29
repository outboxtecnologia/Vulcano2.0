import urllib.request, json
req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639", "thread_id":"123", "feedback_usuario":"", "aprovado":false}', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
st = data.get("state", {})
print("Calibracao Prompt contains:\n")
print(st.get("prompt_calibracao")[-500:])
