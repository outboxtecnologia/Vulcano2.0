import main
conn = main.get_conn('questor')
cur = conn.cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS")
tables = [r[0].strip() for r in cur.fetchall()]
for t in tables:
    if 'CONT' in t: print("Table:", t)

cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'PLANOCONTA' OR RDB$RELATION_NAME = 'PLANOESPEC' OR RDB$RELATION_NAME = 'CTB_CONTA'")
for r in cur.fetchall():
    print("Field:", r[0].strip())
