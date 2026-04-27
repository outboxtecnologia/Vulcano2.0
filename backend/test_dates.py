import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

conn = get_conn("questor")
cur = conn.cursor()
query = "SELECT DATALCTOCTB, VALORLCTOCTB FROM LCTOCTB C WHERE CODIGOEMPRESA = 959 AND (CONTACTBDEB = 4910 OR CONTACTBCRED = 4910) AND EXISTS (SELECT 1 FROM LCTOGER G WHERE G.CODIGOEMPRESA = C.CODIGOEMPRESA AND G.CHAVELCTOCTB = C.CHAVELCTOCTB AND G.CODIGOCENTROCUSTO = 19) ORDER BY DATALCTOCTB DESC"

cur.execute(query)
rows = cur.fetchall()
print(f"Total rows for CC=19: {len(rows)}")
for r in rows[:10]:
    print(r)
