import sys
sys.path.append('backend')
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$VIEW_BLR IS NULL AND RDB$SYSTEM_FLAG = 0")
tables = [r[0].strip() for r in cur.fetchall()]
venda_tables = [t for t in tables if 'VEND' in t or 'CONTRATO' in t]
print('Tabels:', venda_tables)
for t in venda_tables[:10]:
    try:
        cur.execute(f'SELECT FIRST 1 * FROM {t}')
        cols = [d[0] for d in cur.description]
        print(t, cols)
    except:
        pass
