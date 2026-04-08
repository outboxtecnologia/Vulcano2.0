import sys
import json
sys.path.append('backend')
from main import get_conn

def run():
    conn = get_conn('vulcano')
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT e.CODIGOEMPRESA, e.NOMEEMPRESA FROM EMPRESA e INNER JOIN EMPREENDIMENTO emp ON emp.CODIGOEMPRESA = e.CODIGOEMPRESA")
    rows = cur.fetchall()
    
    with open('test_empresas.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f)
        
if __name__ == '__main__':
    run()
