from main import get_conn
try:
    conn_v = get_conn('vulcano')
    cur = conn_v.cursor()
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%POC%'")
    tables = [r[0].strip() for r in cur.fetchall()]
    print("TABLES:", tables)
    for t in tables:
        cur.execute(f"SELECT FIRST 1 * FROM {t}")
        print(f"COLUMNS FOR {t}:", [d[0] for d in cur.description])
        cur.execute(f"SELECT * FROM {t}")
        rows = cur.fetchall()
        print(f"ROWS FOR {t}:", rows)
except Exception as e:
    print(e)
