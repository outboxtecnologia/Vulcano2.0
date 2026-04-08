import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
cur = conn.cursor()

with open('poc_result.txt', 'w') as f:
    try:
        cols = []
        cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'POC'")
        for r in cur.fetchall():
            cols.append(r[0].strip())
        f.write("POC Columns:\n" + str(cols) + "\n\n")
        
        cur.execute("SELECT FIRST 10 " + ",".join(cols) + " FROM POC ORDER BY 2 DESC")
        for r in cur.fetchall():
            f.write(str(r) + "\n")
    except Exception as e:
        f.write("Erro POC: " + str(e) + "\n")

conn.close()
