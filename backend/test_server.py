import urllib.request
import traceback

try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/receitas-caixa?empresa_id=959", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        print("Status:", response.status)
        data = response.read().decode('utf-8')
        print(data[:500])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode('utf-8')[:500])
except Exception as e:
    print("Exception:", e)
    traceback.print_exc()
