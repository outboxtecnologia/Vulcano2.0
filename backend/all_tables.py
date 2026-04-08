import firebirdsql
try:
    conn = firebirdsql.connect(
        host='localhost',
        database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
        user='SYSDBA',
        password='masterkey',
        charset='WIN1252'
    )
    c = conn.cursor()
    c.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
    tables = [r[0].strip() for r in c.fetchall() if r[0] and not r[0].startswith('RDB$')]
    
    with open("vulcano_all_tables.txt", "w") as f:
        f.write("\\n".join(tables))
    
except Exception as e:
    print(e)
