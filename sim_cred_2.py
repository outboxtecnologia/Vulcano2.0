import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from core.db import get_conn

conn = get_conn('questor')
cur = conn.cursor()

# Query LCTOCTB directly for any entry matching APTO 201
cur.execute("""
    SELECT FIRST 20 
        C.DATALCTOCTB, C.VALORLCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0)
    FROM LCTOCTB C
    WHERE C.CODIGOEMPRESA = 959
      AND CAST(C.COMPLHIST AS BLOB SUB_TYPE 0) LIKE '%201%'
      AND EXTRACT(YEAR FROM C.DATALCTOCTB) IN (2023, 2024)
    ORDER BY C.DATALCTOCTB DESC
""")
rows = cur.fetchall()
for r in rows:
    print(r[0], "Val:", r[1], "Deb:", r[2], "Cred:", r[3], "Hist:", bytes(r[4]).decode('utf-8', errors='ignore')[:30] if r[4] else "")

conn.close()
