import requests

try:
    url = "http://127.0.0.1:8000/api/questor/contabilizacoes?ano=2024&mes=4&empresa_id=959&empreendimento_id=6400000000003"
    r = requests.get(url)
    print("Status:", r.status_code)
    print("Text:", r.text)
except Exception as e:
    print("Exception:", e)
