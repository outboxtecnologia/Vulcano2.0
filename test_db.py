import requests
import json

try:
    res = requests.get('http://127.0.0.1:8000/api/receitas-caixa?empresa_id=959')
    data = res.json()
    if "dashboard_data" in data and len(data["dashboard_data"]) > 0:
        print(json.dumps(data["dashboard_data"][0], indent=2))
        
    print("\n--- Testing second endpoint ---")
    res2 = requests.get('http://127.0.0.1:8000/api/compare/receitas?empresa_id=959')
    try:
        data2 = res2.json()
        print(len(data2.get("timeline", [])))
    except:
        pass
except Exception as e:
    print(e)
