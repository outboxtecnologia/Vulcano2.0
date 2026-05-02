import sys
out = open('c:/Users/dirfe/.gemini/antigravity/scratch/vulcano2.0/backend/search_out_2.txt', 'w', encoding='utf-8')
with open('c:/Users/dirfe/.gemini/antigravity/scratch/vulcano2.0/backend/main.py', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if '/estrutura' in line:
            out.write(f"{i}: {line.strip()}\n")
out.close()
