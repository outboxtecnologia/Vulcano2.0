from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.post("/api/parser/preview-baixas", json={"empresa_id": 1, "extracted_data": []})
print("STATUS CODE:", response.status_code)
print("RESPONSE TEXT:", response.text)
if response.status_code == 405:
    print("WARNING: Method Not Allowed. Let's see what is allowed...")
    # Get all routes matching exactly the path
    routes = [r for r in app.routes if r.path == "/api/parser/preview-baixas"]
    for r in routes:
        print(f"ROUTE MATCHED: {r.name} - Methods: {getattr(r, 'methods', None)}")
