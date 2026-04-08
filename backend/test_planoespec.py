import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

try:
    conn = get_conn("questor", 959)
    cur = conn.cursor()

    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='PLANOESPEC'")
    cols = [r[0].strip() for r in cur.fetchall()]
    print("Cols:", cols)
    
    col_str = ", ".join(cols[:5]) # just print first 5 to see
    cur.execute(f"SELECT FIRST 5 * FROM PLANOESPEC")
    rows = cur.fetchall()
    print("\nRows:")
    for r in rows:
        print(r)
except Exception as e:
    print("ERRO:", e)
