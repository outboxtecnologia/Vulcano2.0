import sys
sys.path.append('backend')
from main import get_conn
try:
    conn = get_conn('questor')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 * FROM PLANOESPEC")
    print([d[0].strip() for d in cur.description])
    conn.close()
except Exception as e:
    print(e)
