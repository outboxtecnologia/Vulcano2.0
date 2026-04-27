import sys; sys.path.insert(0, 'backend')
from main import get_conn
cur = get_conn('vulcano').cursor()
cur.execute("SELECT DESCUNIDIMOB, DATADISTRATO, DISTRATO FROM VENDA WHERE ID IN (16829, 16831)")
for r in cur.fetchall():
    print(r[0].decode('cp1252'), r[1], r[2])
