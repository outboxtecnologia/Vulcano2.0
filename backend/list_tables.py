import main
conn = main.get_conn('vulcano')
cur = conn.cursor()
cur.execute('SELECT FIRST 1 * FROM VENDAUNIDADE')
desc = cur.description
for col in desc: print(col[0])
conn.close()
