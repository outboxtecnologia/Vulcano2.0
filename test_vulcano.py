import sys
import os
sys.path.append('backend')
from core.database import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT v.ID, c.NOME, v.DESCUNIDIMOB FROM VENDA v JOIN CLIENTE c ON v.ID_CLIENTE = c.ID WHERE c.NOME LIKE '%GILBERTO PACHECO%' OR c.NOME LIKE '%EDSON LUIS HOSANG%'")
r = cur.fetchall()
print(r)
for row in r:
    print(row)
    cur.execute("SELECT ID, DATA, VALORPARCELA, TOTALPAGO FROM RECEBER WHERE IDVENDA = ?", (row[0],))
    recs = cur.fetchall()
    print("Recs:", len(recs), "Sample:", recs[:3] if recs else [])
