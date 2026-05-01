import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn

conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_NAME LIKE '%RECEB%'")
rows = cur_v.fetchall()
print("RECEB TABLES:")
for r in rows:
    print(r[0].strip())
conn_v.close()
