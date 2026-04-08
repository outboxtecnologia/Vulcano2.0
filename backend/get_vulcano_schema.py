import firebirdsql
import json

DB_PATH_VULCANO = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"

def get_vulcano_tables():
    conn = firebirdsql.connect(
        host="localhost",
        database=DB_PATH_VULCANO,
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252"
    )
    cur = conn.cursor()
    
    # Get all tables
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 ORDER BY RDB$RELATION_NAME")
    tables = [row[0].strip() for row in cur.fetchall()]
    
    cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 AND RDB$RELATION_NAME LIKE '%REC%' ORDER BY RDB$RELATION_NAME")
    tables_rec = [row[0].strip() for row in cur.fetchall()]
    
    schema = {"recebimento_tables": tables_rec}
        
    with open("schema_out.json", "w") as f:
        json.dump(schema, f, indent=2)
    conn.close()

get_vulcano_tables()
