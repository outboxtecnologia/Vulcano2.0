import sqlite3
import sys
import os
sqlite_path = os.path.join(os.getcwd(), 'backend', 'poc_database.sqlite')
if os.path.exists(sqlite_path):
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    for r in cur.fetchall():
        print(f"[{r[0]}]")
        print(r[1][:200])
    conn.close()
