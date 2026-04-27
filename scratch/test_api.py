import requests

try:
    # Venda ID do Eduardo Nunes: 11151
    resp = requests.get("http://127.0.0.1:8000/api/vulcano/vendas/11151/condicoes")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total Parcelas: {len(data['parcelas'])}")
        abertas = [p for p in data['parcelas'] if p['total_pago'] == 0.0]
        print(f"Abertas Dinâmicas (Projetadas): {len(abertas)}")
    else:
        print("Erro HTTP:", resp.status_code, resp.text)
except Exception as e:
    print("Erro Request:", e)
