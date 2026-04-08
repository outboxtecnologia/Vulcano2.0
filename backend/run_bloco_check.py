import sys
sys.path.append('.')
from main import get_conn

try:
    conn = get_conn('vulcano')
    cur = conn.cursor()
    cur.execute('SELECT FIRST 10 ID, NOME, IDEMPREENDIMENTO FROM BLOCO')
    with open('bloco_test.txt', 'w') as f:
        for r in cur.fetchall(): f.write(str(r)+'\n')
except Exception as e:
    with open('bloco_err.txt', 'w') as f: f.write(str(e))
finally:    
    if 'conn' in locals() and conn: conn.close()
