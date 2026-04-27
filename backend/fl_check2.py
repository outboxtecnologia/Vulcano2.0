from main import get_conn

conn = get_conn("questor")
cur = conn.cursor()
cur.execute("SELECT FIRST 1 VALORLCTOGER, NATURLCTOCTB FROM LCTOGER")
r = cur.fetchone()
print(r)
conn.close()
