import sys
sys.path.append('backend')
from main import get_conn
import json
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute('SELECT FIRST 1 * FROM EMPREENDIMENTO')
cols = [d[0] for d in cur.description]
res = {
    'DATA': [c for c in cols if 'DAT' in c],
    'METRAGEM': [c for c in cols if 'MET' in c or 'ARE' in c],
    'CNO': [c for c in cols if 'CNO' in c],
    'PRAZO': [c for c in cols if 'PRAZ' in c or 'FIM' in c]
}
with open('../cols.json', 'w') as f:
    json.dump(res, f)
