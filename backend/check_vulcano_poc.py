import sys
from main import get_conn
try:
    conn_v = get_conn('vulcano')
    cur = conn_v.cursor()
    cur.execute('SELECT FIRST 1 * FROM POC_CUSTO_MENSAL_REAL')
    print("MENSAL:", [d[0] for d in cur.description])
    cur.execute('SELECT FIRST 1 * FROM POC_CUSTOS')
    print("POC_CUSTOS:", [d[0] for d in cur.description])
except Exception as e:
    print(e)
