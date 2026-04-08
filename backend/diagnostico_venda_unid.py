import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import get_conn

def run():
    conn = get_conn("vulcano")
    cur = conn.cursor()
    cur.execute("SELECT FIRST 10 UNIDIMOB, DESCUNIDIMOB FROM VENDA WHERE IDEMPREENDIMENTO = '22' AND TOTALVENDA > 0")
    for r in cur.fetchall():
        print(f"UNIDIMOB: {r[0]} | DESCUNIDIMOB: {r[1]}")
    conn.close()

if __name__ == "__main__":
    run()
