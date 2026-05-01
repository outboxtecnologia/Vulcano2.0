import sqlite3
import re

conn = sqlite3.connect('poc_database.sqlite')
res = conn.execute("SELECT CONTA_ID, NOME FROM PLANO WHERE NOME LIKE '%LOCA%' OR NOME LIKE '%ALUGU%' LIMIT 20").fetchall()
for r in res:
    print(r)
