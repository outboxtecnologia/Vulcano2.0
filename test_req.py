import requests
r = requests.post("http://127.0.0.1:8000/api/parser/preview-baixas", json={"empresa_id": 1, "extracted_data": []})
print(r.status_code)
print(r.headers)
print(r.text)
print(r.history)
