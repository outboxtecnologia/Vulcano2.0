import re

with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = open("out8.txt", "w", encoding="utf-8")

start_idx = -1
for i, line in enumerate(lines):
    if "/api/vulcano/empreendimentos" in line and "@app.get" in line:
        start_idx = i
        break

if start_idx != -1:
    out.write("--- EMPREENDIMENTOS GET ---\n")
    for j in range(start_idx, min(start_idx + 40, len(lines))):
        out.write(f"{j+1}: {lines[j]}")

start_idx = -1
for i, line in enumerate(lines):
    if "/api/vulcano/vendas" in line and "@app.get" in line and "condicoes" not in line:
        start_idx = i
        break

if start_idx != -1:
    out.write("\n--- VENDAS GET ---\n")
    for j in range(start_idx, min(start_idx + 40, len(lines))):
        out.write(f"{j+1}: {lines[j]}")

out.close()
