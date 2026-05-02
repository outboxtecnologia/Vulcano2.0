import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.main import get_conn

conn = get_conn("questor")
try:
    cur = conn.cursor()
    cur.execute("""
        SELECT RDB$GENERATOR_NAME
        FROM RDB$GENERATORS
        WHERE RDB$SYSTEM_FLAG = 0
    """)
    generators = [row[0].strip() for row in cur.fetchall()]
    lcto_gens = [g for g in generators if 'LCTO' in g.upper() or 'GER' in g.upper()]
    print("Found LCTO generators:", lcto_gens)
    if not lcto_gens:
        print("All generators:", generators[:20])
finally:
    conn.close()
