import sqlite3

def check_sqlite():
    db_path = "backend/poc_database.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(empreendimento)")
    rows = cur.fetchall()
    print("Empreendimento COLUMNS:")
    for r in rows:
        print(r)
check_sqlite()
