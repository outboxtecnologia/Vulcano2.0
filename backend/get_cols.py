import httpx
import sys

try:
    with httpx.Client(base_url="http://127.0.0.1:8000") as client:
        r = client.get("/api/table/RECEBER/schema")
        print(r.json())
except Exception as e:
    print(e)
