from main import get_conn

conn = get_conn("questor")
cur = conn.cursor()
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'LCTOGER'")
rows = cur.fetchall()
print("QUESTOR LCTOGER COLUMNS:")
for r in rows:
    print(r[0].strip())
conn.close()
