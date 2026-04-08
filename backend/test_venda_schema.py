import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import get_conn

def test():
    conn = get_conn("vulcano")
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 * FROM VENDA")
    cols = [d[0] for d in cur.description]
    print("COLUMNS IN VENDA:", cols)
    conn.close()

if __name__ == "__main__":
    test()
