import urllib.request, json
data = json.loads(urllib.request.urlopen("http://localhost:8001/api/receitas-caixa").read())
with open("test_out.txt", "w") as f:
    found = False
    for r in data["dashboard_data"]:
        if "STUTTGART" in r["empreendimento"].upper():
            f.write(f"CAIXA: {r['empreendimento']} VGV:{r.get('vgv',0)}\n")
            found = True
    if not found:
        f.write("NO MATCH IN CAIXA\n")
