import sys
sys.path.append(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

data = {
    "empresa_id": 959,
    "linhas": [
        {"conta_id": 5668, "competencia": "2024-01", "saldo_q": 9000, "saldo_v": 1500, "n_lanc_q": 1, "n_lanc_v": 1},
        {"conta_id": 5668, "competencia": "2024-02", "saldo_q": 8000, "saldo_v": 1500, "n_lanc_q": 1, "n_lanc_v": 1},
        {"conta_id": 5669, "competencia": "2024-01", "saldo_q": 1000, "saldo_v": 1500, "n_lanc_q": 1, "n_lanc_v": 1},
        {"conta_id": 5669, "competencia": "2024-02", "saldo_q": 1000, "saldo_v": 1500, "n_lanc_q": 1, "n_lanc_v": 1},
        {"conta_id": 5670, "competencia": "2024-01", "saldo_q": 1000, "saldo_v": 1500, "n_lanc_q": 1, "n_lanc_v": 1},
        {"conta_id": 5670, "competencia": "2024-02", "saldo_q": 1000, "saldo_v": 1500, "n_lanc_q": 1, "n_lanc_v": 1}
    ],
    "top_n": 20
}

response = client.post("/api/auditoria/diagnostico", json=data)
print(response.json())
