from main import get_conn
try:
    conn = get_conn("questor")
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 * FROM PESSOA")
    cols = [desc[0] for desc in cur.description]
    with open('cols_pessoa_questor.txt', 'w') as f:
        f.write(", ".join(cols))
    conn.close()
except Exception as e:
    with open('cols_pessoa_questor.txt', 'w') as f:
        f.write(str(e))
