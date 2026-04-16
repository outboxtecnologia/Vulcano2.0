import sys
sys.path.append(r'backend')
import sqlite3
from core.database.connection import get_conn
import asyncio

conn = get_conn('questor')
cur = conn.cursor()
cur.execute('''
    SELECT 
        SUM(CASE WHEN G.NATURLCTOCTB=1 THEN G.VALORLCTOGER ELSE 0 END) AS DEB,
        SUM(CASE WHEN G.NATURLCTOCTB=-1 THEN G.VALORLCTOGER ELSE 0 END) AS CRED,
        SUM(G.VALORLCTOGER * G.NATURLCTOCTB) AS NET
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = 959 AND G.CODIGOCENTROCUSTO = 35
      AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
      AND G.DATALCTOCTB >= '2025-03-01' AND G.DATALCTOCTB < '2025-04-01'
''')
d, c, n = cur.fetchone()
print(f"Stuttgart Mar/2025 -> Deb: {d}, Cred: {c}, Net: {n}")
