import sys
sys.path.append('.')
from main import get_conn

conn = get_conn('vulcano')
cur = conn.cursor()
try:
    cur.execute('SELECT FIRST 5 * FROM INDICE_REAJUSTE_TABELA')
    cols = [d[0] for d in cur.description]
    with open('indice_schema.txt', 'w', encoding='utf-8') as f:
        f.write(str(cols) + '\n')
        for r in cur.fetchall():
            f.write(str(r) + '\n')
            
    cur.execute('SELECT FIRST 5 * FROM INDICE_REAJUSTE')
    cols2 = [d[0] for d in cur.description]
    with open('indice_2_schema.txt', 'w', encoding='utf-8') as f:
        f.write(str(cols2) + '\n')
        for r in cur.fetchall():
            f.write(str(r) + '\n')
            
except Exception as e:
    with open('error_db2.txt', 'w') as f: f.write(str(e))
conn.close()
