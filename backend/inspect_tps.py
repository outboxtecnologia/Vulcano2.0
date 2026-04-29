import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='TERCEIROPGTO' ORDER BY RDB$FIELD_POSITION")
print("TERCEIROPGTO cols:", [r[0].strip() for r in cur.fetchall()])
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='TERCEIROPGTOSERVICO' ORDER BY RDB$FIELD_POSITION")
print("TERCEIROPGTOSERVICO cols:", [r[0].strip() for r in cur.fetchall()])
