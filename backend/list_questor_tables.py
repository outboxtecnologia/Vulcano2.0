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
cursor.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0;")
tables = [row[0].strip() for row in cursor.fetchall()]
print("Total Tables:", len(tables))
print("Sample:", tables[:20])
from fnmatch import filter
print("LOTE tables:", filter(tables, '*LOTE*'))
print("LANC tables:", filter(tables, '*LANC*'))
conn.close()
