import os
import codecs

filename = "DEV_TERMS_LOG.md"

new_terms = """
- Shell Scripting para Deploy (Bash)
- Processos em Background (nohup e &)
- Git Update-Index (Permissão Executável)
"""

content = ""
if os.path.exists(filename):
    with codecs.open(filename, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

if "nohup" not in content:
    with codecs.open(filename, "w", encoding="utf-8") as f:
        f.write(content + "\n" + new_terms)
    print("Terms added.")
else:
    print("Terms already exist.")
