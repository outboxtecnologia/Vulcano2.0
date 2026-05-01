import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn

conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'VENDA'")
rows = cur_v.fetchall()
print("VENDA COLUMNS:")
for r in rows:
    if "DATA" in r[0]:
        print(r[0].strip())
conn_v.close()
