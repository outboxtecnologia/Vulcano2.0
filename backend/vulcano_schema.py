import firebirdsql
import json

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

    def get_cols(table):
        cur.execute("SELECT rf.RDB$FIELD_NAME FROM RDB$RELATION_FIELDS rf WHERE rf.RDB$RELATION_NAME = ? ORDER BY rf.RDB$FIELD_POSITION", (table.upper(),))
        return [r[0].strip() for r in cur.fetchall()]

    schema = {
        "RECEBER": get_cols("RECEBER"),
        "VENDA": get_cols("VENDA"),
        "CLIENTE": get_cols("CLIENTE"),
        "UNIDADE": get_cols("UNIDADE"),
        "EMPREENDIMENTO": get_cols("EMPREENDIMENTO")
    }

    with open("vulcano_schema_out.json", "w") as f:
        json.dump(schema, f, indent=2)

    conn.close()
    print("Schema dumped!")
except Exception as e:
    print("Schema ERR:", e)
