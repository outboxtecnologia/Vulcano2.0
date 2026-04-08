import firebirdsql

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
cur = conn.cursor()

with open('venda_cols.txt', 'w') as f:
    try:
        cols = []
        cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'VENDA'")
        for r in cur.fetchall():
            cols.append(r[0].strip())
        f.write("VENDA Columns:\n" + str(cols) + "\n\n")
        cur.execute("SELECT FIRST 5 " + ",".join(cols[:5]) + " FROM VENDA")
        for r in cur.fetchall():
            f.write(str(r) + "\n")
    except Exception as e:
        f.write("Erro: " + str(e))
    finally:
        conn.close()
