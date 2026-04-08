import firebirdsql
import json

DB_PATH_VULCANO = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"
conn = firebirdsql.connect(
    host="localhost",
    database=DB_PATH_VULCANO,
    port=3050,
    user="SYSDBA",
    password="masterkey",
    charset="WIN1252"
)
cur = conn.cursor()

def get_fdb_columns(table_name):
    cur.execute(f"SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = '{table_name}' ORDER BY RDB$FIELD_POSITION")
    return [r[0].strip() for r in cur.fetchall()]

try:
    schema = {
        "VENDA": get_fdb_columns("VENDA"),
        "VENDAFORMAPAGTO": get_fdb_columns("VENDAFORMAPAGTO"),
        "VENDAFORMAPAGTOPRAZO": get_fdb_columns("VENDAFORMAPAGTOPRAZO"),
        "RECEBER": get_fdb_columns("RECEBER")
    }
    with open("schema_firebird_formapagto.json", "w") as f:
        json.dump(schema, f, indent=2)
    print("Schema guardado em schema_firebird_formapagto.json")
except Exception as e:
    print("Erro:", str(e))
finally:
    conn.close()
