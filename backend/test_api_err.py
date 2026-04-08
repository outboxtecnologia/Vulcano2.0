import requests

try:
    res = requests.get("http://localhost:8000/api/auditoria/saldos?empresa_id=2&data_fim=2025-04-30")
    print("STATUS:", res.status_code)
    if res.status_code != 200:
        print("ERROR:", res.text)
    else:
        print("OK")
except Exception as e:
    print(e)
