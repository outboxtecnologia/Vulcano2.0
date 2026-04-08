from main import get_conn
try:
    conn = get_conn("questor")
    cur = conn.cursor()
    cur.execute("SELECT FIRST 50 RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 AND (RDB$RELATION_NAME LIKE '%CLI%' OR RDB$RELATION_NAME LIKE '%PESSOA%' OR RDB$RELATION_NAME LIKE '%ENTIDADE%' OR RDB$RELATION_NAME LIKE '%FORNEC%')")
    tables = [r[0].strip() for r in cur.fetchall()]
    with open('tables_questor.txt', 'w') as f:
        f.write("\n".join(tables))
    conn.close()
except Exception as e:
    with open('tables_questor.txt', 'w') as f:
        f.write(str(e))
