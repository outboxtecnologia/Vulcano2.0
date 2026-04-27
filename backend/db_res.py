import sys
import os
import sqlite3
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn

print("--- ORCAMENTO EMPREENDIMENTO ---")
conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'EMPREENDIMENTO'")
cols = [r[0].strip() for r in cur_v.fetchall()]
print([c for c in cols if 'ORCA' in c or 'CUSTO' in c])

print("\n--- POC / INDICE TABLES ---")
cur_v.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 AND (RDB$RELATION_NAME LIKE '%POC%' OR RDB$RELATION_NAME LIKE '%CUB%' OR RDB$RELATION_NAME LIKE '%INDICE%')")
print([r[0].strip() for r in cur_v.fetchall()])
conn_v.close()
