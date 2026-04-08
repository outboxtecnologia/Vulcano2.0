import sys
out = open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/search_out.txt', 'w', encoding='utf-8')
with open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/main.py', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if '/api/vulcano/unidades' in line or '/api/vulcano/blocos' in line or 'estrutura' in line:
            out.write(f"{i}: {line.strip()}\n")
out.close()
