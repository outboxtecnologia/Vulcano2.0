from main_BKP_VERTEX import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'POC'")
rows = cur.fetchall()
print("FIREBIRD POC COLUMNS:")
for r in rows:
    print(r[0].strip())
conn.close()
