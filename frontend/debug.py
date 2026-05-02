import sys

path = r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

lines = text.split("\n")
with open("debug.txt", "w", encoding="utf-8") as f:
    for i, line in enumerate(lines):
        if "FOOTER KPIs" in line:
            # write context
            f.write(f"--- MATCH {i} ---\n")
            for j in range(i-5, i+5):
                f.write(f"{j}: {lines[j]}\n")
            f.write("\n")
