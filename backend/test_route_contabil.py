import sys
import urllib.request
import json

def test():
    try:
        url = "http://127.0.0.1:8000/api/questor/contabilizacoes?empresa_id=959&ano=2024&mes=4&empreendimento_id=6400000000003"
        print(f"Buscando {url} ...")
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
            print("Status Code: 200")
            print("Response JSON/Text:", data.decode('utf-8')[:1500])
    except urllib.error.HTTPError as e:
        print("Erro 500! Response:", e.read().decode('utf-8'))

if __name__ == "__main__":
    test()
