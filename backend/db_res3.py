import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute(f"SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'INDICE_REAJUSTE_TABELA'")
print("INDICE_REAJUSTE_TABELA COLUMNS:")
print([r[0].strip() for r in cur_v.fetchall()])
conn_v.close()
