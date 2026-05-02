import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.main import get_conn

conn = get_conn("questor")
try:
    cur = conn.cursor()
    cur.execute("""
        SELECT RDB$TRIGGER_SOURCE
        FROM RDB$TRIGGERS
        WHERE RDB$RELATION_NAME = 'LCTOGER'
    """)
    for row in cur.fetchall():
        source = row[0]
        if source and 'GEN_' in source.upper() or 'NEXT VALUE' in source.upper():
            print("Trigger Source:")
            print(source)
finally:
    conn.close()
