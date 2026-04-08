import sys
sys.path.append('backend')
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute('SELECT FIRST 1 * FROM EMPREENDIMENTO')
cols = [d[0] for d in cur.description]
with open('../all_cols.txt', 'w') as f:
    f.write(", ".join(cols))
