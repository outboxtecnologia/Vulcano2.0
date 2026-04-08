import os
with open('main.py', encoding='utf-8') as f:
    lines = f.readlines()
with open('receb_endpoints.txt', 'w') as out:
    for i, l in enumerate(lines):
        if '/api/vulcano/recebimentos' in l or '/api/vulcano/receber' in l:
            out.write(f"Line {i}: {l.strip()}\n")
