import sys
from main import get_conn
import json
try:
    c = get_conn('questor')
    cur = c.cursor()
    cur.execute("SELECT FIRST 1 * FROM PLANOGRUPOEMPRESACONTAS")
    cols = [d[0].strip() for d in cur.description]
    with open('qplan_cols.json', 'w') as f:
        json.dump(cols, f)
except Exception as e:
    try:
        cur.execute("SELECT FIRST 1 * FROM PLANOPADRAO")
        cols = [d[0].strip() for d in cur.description]
        with open('qplan_cols.json', 'w') as f:
            json.dump(cols, f)
    except Exception as e2:
        with open('qplan_cols.json', 'w') as f:
            f.write(str(e2))
