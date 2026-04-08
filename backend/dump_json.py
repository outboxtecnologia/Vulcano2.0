import urllib.request
import json
url = "http://127.0.0.1:8000/api/custos/dashboard/5?mes=12&ano=2024"
try:
    with urllib.request.urlopen(url) as response:
        ret = json.loads(response.read().decode())
        with open('ret.json', 'w') as f:
            json.dump(ret, f, indent=2)
except Exception as e:
    with open('ret.json', 'w') as f:
        f.write(str(e))
