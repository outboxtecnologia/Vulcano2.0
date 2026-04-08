import sys
from main import get_conn
try:
    c = get_conn('questor')
    cur = c.cursor()
    cur.execute("SELECT FIRST 1 * FROM PLANOCONTAS")
    print("PLANOCONTAS COLUMNS:", [d[0] for d in cur.description])
except Exception as e:
    try:
        cur.execute("SELECT FIRST 1 * FROM CONTAB")
        print("CONTAB COLUMNS:", [d[0] for d in cur.description])
    except Exception as e2:
        print(e, e2)
