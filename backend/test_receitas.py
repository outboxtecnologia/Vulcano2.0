from main import get_receitas_caixa
res = get_receitas_caixa(empresa_id=959, data_ini="2024-04-01", data_fim="2024-04-30")
keys = res.get("dashboard_meta", {}).keys()
print("KEYS IN DASHBOARD META:", keys)
if 'RESIDENCIAL STUTTGART' in res.get("dashboard_meta", {}):
    print("STUTTGART DATA:", res["dashboard_meta"]["RESIDENCIAL STUTTGART"])
else:
    print("STUTTGART IS MISSING FROM META!")
