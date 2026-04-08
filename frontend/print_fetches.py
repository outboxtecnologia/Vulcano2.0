import sys
with open(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\CustosView.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "fetch(" in line:
        print(f"{i}: {line.strip()}")
