import json
from core.database.connection import get_firebird_connection

def test():
    conn = get_firebird_connection()
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 * FROM PLANOESPEC")
    desc = cur.description
    print([d[0] for d in desc])
    conn.close()

if __name__ == "__main__":
    test()
