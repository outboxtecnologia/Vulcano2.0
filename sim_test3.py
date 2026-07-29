import urllib.request, json
req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639", "thread_id":"123", "feedback_usuario":"", "aprovado":false}', headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    st = data.get("state", {})
    dossie = st.get("dossie_heuristico", {})
    prmp = st.get("prompt_calibracao", "")
    print("Dossie dict status:", dossie.get("status"))
    print("Dossie amostra exist?:", bool(dossie.get("dossie", {}).get("amostra_unidades")))
    print("Prompt tail:\n", prmp[-400:])
except Exception as e:
    print("HTTP Error:", e)
