import urllib.request
import json
import urllib.error

data = json.dumps({'empresa_id': 1, 'extracted_data': []}).encode('utf-8')
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/parser/preview-baixas', 
    method='POST', 
    data=data, 
    headers={'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"FAILED: {e.code} {e.reason}")
    print(e.read().decode())
