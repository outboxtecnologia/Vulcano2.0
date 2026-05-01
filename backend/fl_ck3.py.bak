import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn

conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'RECEBER'")
rows = cur_v.fetchall()
print("RECEBER COLUMNS:")
for r in rows:
    res = r[0].strip()
    if "DATA" in res or "VALOR" in res or "ID" in res:
        print(res)
conn_v.close()
