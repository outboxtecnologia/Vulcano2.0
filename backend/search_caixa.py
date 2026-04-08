import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
cur = conn.cursor()

cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%MOV%' OR RDB$RELATION_NAME LIKE '%CAIXA%' OR RDB$RELATION_NAME LIKE '%LANC%' OR RDB$RELATION_NAME LIKE '%FINAN%'")
tables = [row[0].strip() for row in cur.fetchall() if not row[0].startswith('RDB$')]

with open("caixa_tables.txt", "w", encoding="utf-8") as f:
    for t in tables:
        f.write(t + "\\n")
        try:
            cur.execute(f"SELECT FIRST 1 * FROM {t}")
            f.write(f"  Row: {cur.fetchone()}\\n")
        except:
            pass

conn.close()
