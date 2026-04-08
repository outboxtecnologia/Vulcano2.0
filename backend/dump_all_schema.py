import sqlite3

for db in ['poc_database.sqlite', 'db.sqlite3', 'poc.db']:
    print(f'=== DB: {db} ===')
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        for row in cursor.fetchall():
            print(f"Table: {row[0]}\n{row[1]}\n")
        conn.close()
    except Exception as e:
        print('Error:', e)
