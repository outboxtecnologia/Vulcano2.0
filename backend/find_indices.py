import sys
sys.path.append('.')
from main import get_conn

try:
    conn = get_conn('vulcano')
    cur = conn.cursor()
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$VIEW_BLR IS NULL AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)")
    tables = [r[0].strip() for r in cur.fetchall()]
    
    with open('indices.txt', 'w', encoding='utf-8') as f:
        for t in tables:
            if 'INDICE' in t.upper() or 'CUB' in t.upper():
                f.write(t + '\n')
    conn.close()
    
    connq = get_conn('questor')
    curq = connq.cursor()
    curq.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$VIEW_BLR IS NULL AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)")
    tablesq = [r[0].strip() for r in curq.fetchall()]
    
    with open('indices_q.txt', 'w', encoding='utf-8') as f:
        for t in tablesq:
            if 'INDICE' in t.upper() or 'CUB' in t.upper():
                f.write(t + '\n')
    connq.close()
except Exception as e:
    with open('indices_err.txt', 'w') as f:
        f.write(str(e))
