import sqlite3
import json

conn = sqlite3.connect('poc.db')
c = conn.cursor()

def get_columns(table):
    try:
        c.execute(f"PRAGMA table_info({table})")
        return [x[1] for x in c.fetchall()]
    except:
        return []

schema = {
    "VENDAFORMAPAGTO": get_columns("VENDAFORMAPAGTO"),
    "VENDAFORMAPAGTOPRAZO": get_columns("VENDAFORMAPAGTOPRAZO"),
    "VENDA": get_columns("VENDA")
}

with open("schema_venda.json", "w") as f:
    json.dump(schema, f, indent=2)

print("Schema gerado em schema_venda.json")
