import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend")
import main

conn = main.get_conn('vulcano')
c = conn.cursor()
c.execute("""
SELECT RDB$RELATION_NAME 
FROM RDB$RELATIONS 
WHERE RDB$RELATION_NAME LIKE '%BAIXA%' OR RDB$RELATION_NAME LIKE '%QUIT%'
""")
tables = [r[0].strip() for r in c.fetchall()]
print("Tables:", tables)
conn.close()
