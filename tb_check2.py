import sqlite3

def check_sqlite():
    db_path = "backend/poc_database.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rows = cur.fetchall()
    print("TABLES:")
    for r in rows:
        print(r)
check_sqlite()
