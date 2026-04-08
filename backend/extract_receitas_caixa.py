import re

with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = open("main_receitas_caixa_ext.txt", "w", encoding="utf-8")
start_idx = -1
for i, line in enumerate(lines):
    if "def get_receitas_caixa(" in line:
        start_idx = i
        break

if start_idx != -1:
    out.write("--- get_receitas_caixa ---\n")
    # Read until next @app.get or similar decorator
    for j in range(start_idx, len(lines)):
        if j > start_idx and lines[j].strip().startswith("@app."):
            break
        out.write(f"{j+1}: {lines[j]}")

out.close()
