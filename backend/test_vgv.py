import urllib.request
import json
import collections

data = json.loads(urllib.request.urlopen("http://localhost:8001/api/receitas-caixa").read())

vgv_dict = collections.defaultdict(float)
for r in data["dashboard_data"]:
    emp = r["empreendimento"]
    if emp and "STU" in emp or "STT" in emp:
        key = (r["empreendimento"], r["unidade"], r["comprador"])
        # print("Matched Caixa:", key, "VGV:", r["vgv"])

print("VGV found in Caixa for STUTTGART:")
found = False
for r in data["dashboard_data"]:
    if "STU" in r["empreendimento"] or "STT" in r["empreendimento"]:
        found = True
        print(r["empreendimento"], r.get("vgv", 0))
if not found:
    print("NO ROWS IN EFDUNIDIMOBVENDIDA!")

print("RET Rows:")
for r in data["ret_consolidado"]:
    if "STU" in r["empreendimento"] or "STT" in r["empreendimento"]:
        print("RET:", r["empreendimento"], r["periodo"], "BaseCalc:", r["base_calculo"], "VLR_RET:", r["valor_ret"])
