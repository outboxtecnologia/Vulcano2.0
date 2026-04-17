import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import main
conn = main.get_conn('questor')
cur = conn.cursor()

# Find any credits in LCTOGER for CC 35!
cur.execute("SELECT NATURLCTOCTB, COUNT(*), SUM(VALORLCTOGER) FROM LCTOGER WHERE CODIGOCENTROCUSTO = 35 GROUP BY NATURLCTOCTB")
rows = cur.fetchall()
print("LCTOGER CC 35 Profile:")
for r in rows:
    print(f"NATUR: {r[0]}, COUNT: {r[1]}, SUM: {r[2]}")

conn.close()
