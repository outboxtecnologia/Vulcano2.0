import traceback
from fastapi.testclient import TestClient
import sys
sys.path.append('.')

try:
    from main import app
    client = TestClient(app)
    response = client.get("/api/receitas-caixa")
    print("Status:", response.status_code)
    try:
        data = response.json()
        if "detail" in data:
            print(data["detail"])
        else:
            print("OK, len:", len(str(data)))
    except:
        print(response.text[:1000])
except Exception as e:
    traceback.print_exc()
