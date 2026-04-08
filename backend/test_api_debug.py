import urllib.request
from urllib.error import HTTPError

try:
    url = 'http://127.0.0.1:8000/api/custos/dashboard/5?mes=12&ano=2024'
    res = urllib.request.urlopen(url)
    print("SUCCESS:")
    print(res.read().decode())
except HTTPError as e:
    print(f"HTTP ERROR: {e.code}")
    print(e.read().decode())
