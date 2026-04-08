import json
from main import get_conn
cols = [d[0] for d in get_conn('vulcano').cursor().execute('SELECT FIRST 1 * FROM EMPREENDIMENTO').description]
with open('emp_cols.json', 'w') as f:
    json.dump(cols, f)
