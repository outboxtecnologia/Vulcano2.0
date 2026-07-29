from main_BKP_VERTEX import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_NAME LIKE '%POC%'")
rows = cur.fetchall()
print("FIREBIRD POC TABLES:")
for r in rows:
    print(r[0].strip())
conn.close()
