import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB',
    port=3050, user='SYSDBA', password='masterkey', charset='WIN1252'
)
cur = conn.cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 AND (RDB$RELATION_NAME LIKE '%IMOB%' OR RDB$RELATION_NAME LIKE '%RET%')")
tables = [r[0].strip() for r in cur.fetchall()]
print('IMOB/RET Tables:', tables)

# check STUTTGART in all possible tables if they have DESCUNIDIMOB or INCIMOB or IDENTEMP
for t in tables:
    try:
        cur.execute(f"SELECT FIRST 1 * FROM {t}")
        cols = [d[0] for d in cur.description]
        search_cols = []
        for c in ["IDENTEMP", "INCIMOB", "DESCUNIDIMOB", "NOMECOMPRADOR"]:
            if c in cols: search_cols.append(c)
        if search_cols:
            where_clause = " OR ".join([f"{c} LIKE '%STU%'" for c in search_cols])
            cur.execute(f"SELECT COUNT(*) FROM {t} WHERE {where_clause}")
            count = cur.fetchone()[0]
            if count > 0:
                print(f"FOUND STUTTGART {count} times IN TABLE {t} !!")
                cur.execute(f"SELECT FIRST 5 * FROM {t} WHERE {where_clause}")
                for r in cur.fetchall():
                    print("-->", [x.decode('win1252', 'ignore').strip() if isinstance(x, bytes) else x for x in r])
    except Exception as e:
        print("Error on", t, e)
