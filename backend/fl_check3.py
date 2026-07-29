from main import get_conn

conn = get_conn("questor")
cur = conn.cursor()
cur.execute("SELECT SUM(VALORLCTOGER) FROM LCTOGER WHERE CODIGOCENTROCUSTO = 35 AND CODIGOEMPRESA = 959 AND NATURLCTOCTB = 1")
row = cur.fetchone()
print(f"Total: {row[0]}")
conn.close()
