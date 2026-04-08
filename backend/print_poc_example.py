import requests
import json

r = requests.get('http://127.0.0.1:8000/api/receitas-caixa?empresa_id=959&competencia=2024-12')
data = r.json()

dashboard = data.get("dashboard_data", [])
meta = data.get("dashboard_meta", {})

print("META:", json.dumps(meta, indent=2))
for d in dashboard:
    if d.get("poc", 0) > 0:
        print("EMP:", d)
        break
