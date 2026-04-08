import firebirdsql
import sys

def check_schema():
    try:
        conn = firebirdsql.connect(
            host="localhost",
            database="C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB",
            port=3050,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252"
        )
        cur = conn.cursor()
        
        cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLIENTE' ORDER BY RDB$FIELD_POSITION")
        print("CLIENTE Columns:", [r[0].strip() for r in cur.fetchall()])

        cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'EMPRESA' ORDER BY RDB$FIELD_POSITION")
        print("EMPRESA Columns:", [r[0].strip() for r in cur.fetchall()])
        
        conn.close()
    except Exception as e:
        print("Err:", e)

if __name__ == "__main__":
    check_schema()
