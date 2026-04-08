import sys
import json
from main import get_conn

try:
    c = get_conn('questor')
    cur = c.cursor()
    cur.execute("SELECT FIRST 1 * FROM LCTOCTB")
    l1 = [d[0] for d in cur.description]
    cur.execute("SELECT FIRST 1 * FROM LCTOGER")
    l2 = [d[0] for d in cur.description]
    with open('cols_lcto.json', 'w') as f:
        json.dump({"LCTOCTB": l1, "LCTOGER": l2}, f)
except Exception as e:
    with open('cols_lcto.json', 'w') as f:
        f.write(str(e))
