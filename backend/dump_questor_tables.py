import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

try:
    conn = get_conn("questor", 959)
    cur = conn.cursor()

    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME")
    tables = [r[0].strip() for r in cur.fetchall()]

    with open("questor_tables_dump.txt", "w", encoding="utf-8") as f:
        for t in tables:
            f.write(t + "\n")
    print("Tables list saved.")
    
except Exception as e:
    print("ERRO:", e)
