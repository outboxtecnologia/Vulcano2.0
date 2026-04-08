import sys
from main import get_conn
import json
try:
    c = get_conn('questor')
    cur = c.cursor()
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%PLAN%'")
    tables = [r[0].strip() for r in cur.fetchall()]
    with open('qplan.json', 'w') as f:
        json.dump(tables, f)
except Exception as e:
    with open('qplan.json', 'w') as f:
        f.write(str(e))
