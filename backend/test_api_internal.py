from main import api_custos_dashboard_by_id
import sys, io

old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    ret = api_custos_dashboard_by_id(id_emp=335, mes=12, ano=2024)
except Exception as e:
    ret = f"ERROR: {e}"

out = sys.stdout.getvalue()
sys.stdout = old_stdout

import json
with open('out_api.txt', 'w', encoding='utf-8') as f:
    f.write(f"CAP:\n{out}\nAPI:\n{json.dumps(ret, indent=2, default=str)}\n")
