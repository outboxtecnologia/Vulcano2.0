from main import get_conn
try:
    conn = get_conn('vulcano')
    cur = conn.cursor()
    cur.execute('SELECT FIRST 1 * FROM RECEBER')
    with open('cols_receber.txt', 'w') as f:
        f.write(", ".join([d[0] for d in cur.description]))
    conn.close()
except Exception as e:
    with open('cols_receber.txt', 'w') as f:
        f.write(str(e))
