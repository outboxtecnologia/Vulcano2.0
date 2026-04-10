import re

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "r", encoding="utf-8") as f:
    code = f.read()

# I will just replace the except block to print the stack trace into a file instead of stdout!
patched_code = code.replace(
    'logging.error(f"Erro na inferência qualitativa do Gemini: {ml_err}")',
    'import traceback; open("gemini_error.txt", "w").write(traceback.format_exc())'
)

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "w", encoding="utf-8") as f:
    f.write(patched_code)
