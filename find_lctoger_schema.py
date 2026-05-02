import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.main import get_conn

conn = get_conn("questor")
try:
    cur = conn.cursor()
    cur.execute("""
        SELECT RDB$FIELD_NAME 
        FROM RDB$RELATION_FIELDS 
        WHERE RDB$RELATION_NAME = 'LCTOGER'
    """)
    fields = [row[0].strip() for row in cur.fetchall()]
    print("Fields in LCTOGER:", fields[:20])
    
    # Let's check for any generators in the entire DB containing LCTOGER
    cur.execute("SELECT RDB$GENERATOR_NAME FROM RDB$GENERATORS WHERE RDB$GENERATOR_NAME LIKE '%LCTO%'")
    gens = [row[0].strip() for row in cur.fetchall()]
    print("Generators LIKE LCTO:", gens[:20])
finally:
    conn.close()
