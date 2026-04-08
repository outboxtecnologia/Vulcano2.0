import sys
sys.path.append('.')
from main import get_conn

try:
    conn = get_conn('questor')
    cur = conn.cursor()
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%INDICE%'")
    tables = [r[0].strip() for r in cur.fetchall()]
    with open('q_indice_tables.txt', 'w') as f:
        for t in tables:
            f.write(t + '\n')
            
    if 'INDICE' in tables:
        cur.execute("SELECT FIRST 5 * FROM INDICE")
        cols = [d[0] for d in cur.description]
        with open('q_indice_data.txt', 'w') as f:
            f.write(str(cols) + '\n')
            for r in cur.fetchall():
                f.write(str(r) + '\n')
except Exception as e:
    with open('q_indice_err.txt', 'w') as f: f.write(str(e))
finally:
    if 'conn' in locals() and conn: conn.close()
