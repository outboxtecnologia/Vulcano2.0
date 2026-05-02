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
    rows = cur.fetchall()
    print(f"Triggers for LCTOGER: {len(rows)}")
    for row in rows:
        source = row[0]
        if source:
            source_upper = source.upper()
            if 'GEN_' in source_upper or 'GEN_ID' in source_upper or 'GENERATOR' in source_upper:
                print("--- TRIGGER SOURCE FRAGMENT ---")
                # Print the lines that mention GEN
                lines = source.split('\n')
                for line in lines:
                    if 'GEN' in line.upper():
                        print(line.strip())
finally:
    conn.close()
