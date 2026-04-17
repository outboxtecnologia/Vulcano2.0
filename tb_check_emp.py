import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()
cur_v.execute('SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = ''EMPREENDIMENTO''')
cols = [r[0].strip() for r in cur_v.fetchall()]
print("EMPREENDIMENTO COLUMNS containing ORC, INDICE, POC:")
print([c for c in cols if 'ORC' in c or 'INDICE' in c or 'POC' in c])
conn_v.close()
