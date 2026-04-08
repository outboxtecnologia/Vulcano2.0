import firebirdsql

conn = firebirdsql.connect(
    host="localhost",
    port=3050,
    database=r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB",
    user="SYSDBA",
    password="masterkey",
    charset="UTF8"
)
cursor = conn.cursor()

def dump_cols(table):
    cursor.execute(f"SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = '{table}'")
    cols = [r[0].strip() for r in cursor.fetchall()]
    print(f"--- {table} ---")
    print(", ".join(cols))

dump_cols('LOTECTB')
dump_cols('LCTOCTB')
print('DONE')
conn.close()
