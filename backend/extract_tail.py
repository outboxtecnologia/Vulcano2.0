import sys
path=r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\uvicorn_err.txt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()[-3000:]
with open(r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\uvicorn_tail.txt', 'w', encoding='utf-8') as fw:
    fw.write(text)
