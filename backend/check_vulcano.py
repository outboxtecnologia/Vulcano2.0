import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import main

conn = main.get_conn("vulcano")
cur = conn.cursor()
try:
    cur.execute("SELECT FIRST 5 * FROM LANCAMENTO_CONTABIL")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("Cols:", cols)
    for r in rows:
        print(r)
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
