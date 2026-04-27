import requests
import json

resp = requests.post("http://127.0.0.1:8000/api/auditoria/diagnostico", json={
    "empresa_id": 959,
    "linhas": [{
        "conta": "123",
        "nome": "TEST",
        "classif": "01",
        "saldo_questor": 10,
        "saldo_vulcano": 20,
        "detalhes": []
    }]
})
print("STATUS CODE:", resp.status_code)
print(resp.text)
