import re

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "r", encoding="utf-8") as f:
    code = f.read()

replacement = """                for causa in resp_ia.get("causas", []) or resp_ia.get("Causas", []):
                    try:
                        c_id = int(causa.get("conta_id", 0))
                    except:
                        c_id = 0
                    match = next((r for r in resultado if r["conta_id"] == c_id), None)
                    if match:
                        match["causa_raiz"] = str(causa.get("causa_raiz", causa.get("Causa_Raiz", "")))
                        match["recomendacao"] = str(causa.get("recomendacao", causa.get("Recomendacao", ""))) """

code = code.replace("""                for causa in resp_ia.get("causas", []):
                    c_id = causa.get("conta_id")
                    match = next((r for r in resultado if r["conta_id"] == c_id), None)
                    if match:
                        match["causa_raiz"] = str(causa.get("causa_raiz", ""))
                        match["recomendacao"] = str(causa.get("recomendacao", ""))""", replacement)

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Patch applied for relaxed json parsing.")
