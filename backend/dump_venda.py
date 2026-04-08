import sys
sys.path.append('backend')
from main import get_conn
import json
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$VIEW_BLR IS NULL AND RDB$SYSTEM_FLAG = 0 AND (RDB$RELATION_NAME LIKE '%VEND%' OR RDB$RELATION_NAME LIKE '%CONTRATO%')")
tables = [r[0].strip() for r in cur.fetchall()]

res = {"tables": tables, "schemas": {}}
for t in tables[:15]:
    try:
        cur.execute(f"SELECT FIRST 1 * FROM {t}")
        cols = [d[0] for d in cur.description]
        res["schemas"][t] = cols
    except:
        pass

with open('backend/venda_schema.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=2)
