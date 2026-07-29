import sqlite3
import os

db_path = os.path.join('backend', 'data', 'poc_database.sqlite')
if not os.path.exists(db_path):
    print("No db found at", db_path)
    # Check root
    db_path = 'poc_database.sqlite'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables in sqlite:", cur.fetchall())
    conn.close()
