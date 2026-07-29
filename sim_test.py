import urllib.request, json
req = urllib.request.Request("http://localhost:8000/api/agentes/iniciar_auditoria", data=b'{"conta_alvo":"Conta 5639", "thread_id":"123", "feedback_usuario":"", "aprovado":false}', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
st = data.get("state", {})
d = st.get("dossie_heuristico", {})
print("d.keys()=", d.keys())
print("d['status']=", d.get("status"))
if "dossie" in d:
    print("d['dossie'].keys()=", d["dossie"].keys() if isinstance(d["dossie"], dict) else "Not a dict")
    if "amostra_unidades" in d["dossie"]:
        print("Length of amostra_unidades:", len(d["dossie"]["amostra_unidades"]))
    else:
        print("Missing amostra_unidades")
else:
    print("Missing dossie")
