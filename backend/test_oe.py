import sys, json
sys.path.append('backend')
from main import get_conn
conn = get_conn('questor')
cur = conn.cursor()
cur.execute('SELECT FIRST 1 * FROM OUTRAEMPRESA')
cols = [d[0] for d in cur.description]
with open('outraempresa_cols.txt', 'w') as f:
    json.dump(cols, f)
