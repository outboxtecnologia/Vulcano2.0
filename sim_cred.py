import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.core.db import get_conn

conn = get_conn('questor')
cur = conn.cursor()

cur.execute("""
    SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), SUM(G.VALORLCTOGER)
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
    WHERE G.CODIGOCENTROCUSTO = 35
      AND G.CODIGOEMPRESA = 959
      AND G.NATURLCTOCTB = 2
      AND CAST(C.COMPLHIST AS BLOB SUB_TYPE 0) LIKE '%201%'
    GROUP BY 1, 2
    ORDER BY 1, 2
""")
rows = cur.fetchall()
print("Creditos CC 35 Apto 201:", rows)

conn.close()
