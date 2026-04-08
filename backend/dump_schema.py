import sqlite3

try:
    conn = sqlite3.connect('poc.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        print(f"--- Table: {row[0]} ---")
        print(row[1])
        print("\n")
    conn.close()
except Exception as e:
    print("Error:", e)
