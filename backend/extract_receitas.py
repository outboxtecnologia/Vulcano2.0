import re

with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = open("r_out.txt", "w", encoding="utf-8")
start_idx = -1
for i, line in enumerate(lines):
    if "/api/receitas-caixa" in line:
        start_idx = i
        break

if start_idx != -1:
    out.write("--- get_receitas_caixa ---\n")
    for j in range(start_idx, min(start_idx + 150, len(lines))):
        if j > start_idx + 1 and lines[j].strip().startswith("@app."):
            break
        out.write(f"{j+1}: {lines[j]}")

out.close()
