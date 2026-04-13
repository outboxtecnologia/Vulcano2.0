import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import get_conn
import pprint

def test():
    conn = get_conn("vulcano")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM VENDAFORMAPAGTO WHERE IDVENDA = 15767")
    print("Pagamentos Venda 15767:")
    pprint.pprint(cur.fetchall())
    
if __name__ == "__main__":
    test()
