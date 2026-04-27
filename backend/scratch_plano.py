import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from main import get_conn

def run():
    conn = get_conn("questor")
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 * FROM PLANOESPEC")
    desc = cur.description
    print([d[0] for d in desc])
    conn.close()

if __name__ == "__main__":
    run()
