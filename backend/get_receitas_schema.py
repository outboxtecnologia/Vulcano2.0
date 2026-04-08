import firebirdsql
import sys

DB_PATH_VULCANO = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"

try:
    conn = firebirdsql.connect(
        host="localhost",
        database=DB_PATH_VULCANO,
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252"
    )
    cur = conn.cursor()

    def dump_table(table_name):
        query = """
        SELECT rf.RDB$FIELD_NAME
        FROM RDB$RELATION_FIELDS rf
        WHERE rf.RDB$RELATION_NAME = ?
        ORDER BY rf.RDB$FIELD_POSITION
        """
        cur.execute(query, (table_name.upper(),))
        cols = [row[0].strip() for row in cur.fetchall()]
        import json
        with open('receber_schema.json', 'w') as f:
            json.dump(cols, f)

    dump_table("RECEBER")
    
    cur.execute("SELECT FIRST 1 * FROM RECEBER")
    with open('receber_row.txt', 'w') as f:
        f.write(str(cur.fetchone()))

    
    conn.close()
except Exception as e:
    print("ERROR:", e)
