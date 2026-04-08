import fdb

try:
    conn = fdb.connect(dsn='localhost:C:/Vulcano/dados/VULCANO.FDB', user='SYSDBA', password='masterkey', charset='WIN1252')
    cur = conn.cursor()
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'RECEBER'")
    fields = [row[0].strip() for row in cur.fetchall()]
    print(fields)
except Exception as e:
    print(e)
