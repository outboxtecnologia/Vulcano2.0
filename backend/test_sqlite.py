import sqlite3, os
db = os.path.join(os.path.dirname(__file__), '..', 'poc_database.sqlite')
conn = sqlite3.connect(db)
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)
conn.close()
