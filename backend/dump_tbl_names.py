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
    tables = [r[0].strip() for r in c.fetchall() if r[0]]
    
    receb = [t for t in tables if ('RECEB' in t or 'BAIXA' in t or 'PAG' in t) and not t.startswith('RDB$')]
    
    with open("vulcano_receb_tables.txt", "w") as f:
        f.write("\\n".join(receb))
    
except Exception as e:
    print(e)
