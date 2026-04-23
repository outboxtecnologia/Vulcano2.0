import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend")
import main

conn = main.get_conn('vulcano')
c = conn.cursor()
c.execute("""
SELECT R.PARCELA, R.DATA, R.VALORPARCELA, R.TOTALPAGO 
FROM RECEBER R 
LEFT JOIN VENDA V ON V.ID = R.IDVENDA 
LEFT JOIN CLIENTE C ON C.ID = V.ID_CLIENTE 
WHERE C.NOME LIKE '%JOSIANE DE MELO CISZ%'
""")
rows = c.fetchall()
for r in rows:
    if '2025-12-30' in str(r[1]):
        print("MATCHED DATE:", r)
    if r[2] == 23097.15 or r[3] == 23097.15:
        print("MATCHED VALUE:", r)
conn.close()
