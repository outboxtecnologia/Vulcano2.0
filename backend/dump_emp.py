import sys
import json
sys.path.append('backend')
from main import get_conn

conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute('SELECT FIRST 1 * FROM EMPREENDIMENTO')
cols = [d[0].strip() for d in cur.description]

with open('backend/emp_cols.json', 'w', encoding='utf-8') as f:
    json.dump(cols, f, indent=2)
