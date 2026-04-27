import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

from core.database import get_conn

def test():
    try:
        conn = get_conn('vulcano')
        cur = conn.cursor()
        cur.execute('SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTAESTOQUE, CONTAESTAND FROM EMPREENDIMENTO')
        for row in cur.fetchall():
            print(row)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test()
