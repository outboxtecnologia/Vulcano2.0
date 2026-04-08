import firebirdsql
conn = firebirdsql.connect(host='localhost', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB', port=3050, user='SYSDBA', password='masterkey', charset='WIN1252')
cur = conn.cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0")
tables = [row[0].strip() for row in cur.fetchall()]
with open("all_tables.txt", "w") as f:
    for t in tables:
        f.write(t + "\n")
conn.close()
