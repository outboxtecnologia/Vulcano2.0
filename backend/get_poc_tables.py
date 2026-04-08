import firebirdsql
import json

conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
cur = conn.cursor()

try:
    cols = []
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'POC'")
    for r in cur.fetchall():
        cols.append(r[0].strip())
    print("POC Columns:", cols)
    
    cur.execute("SELECT FIRST 5 " + ",".join(cols) + " FROM POC")
    print("POC Sample Data:")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print("Erro POC:", e)
    
try:
    cols = []
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'VPOC'")
    for r in cur.fetchall():
        cols.append(r[0].strip())
    print("\nVPOC Columns:", cols)
except Exception as e:
    pass

conn.close()
