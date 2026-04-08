import firebirdsql
import os
from dotenv import load_dotenv

load_dotenv()

conn = firebirdsql.connect(
    host="localhost",
    port=3050,
    database=r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB",
    user="SYSDBA",
    password="masterkey",
    charset="UTF8"
)
cursor = conn.cursor()

# Check EMPREENDIMENTO fields
cursor.execute("SELECT RDB$RELATION_NAME, RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'EMPREENDIMENTO'")
emp_fields = [row[1].strip() for row in cursor.fetchall()]
print("EMPREENDIMENTO fields holding 'CONT' or 'CTB':")
for f in emp_fields:
    if 'CONT' in f or 'CT' in f:
        print(f)

# Also check for table named CONTA_CONTABIL or similar
cursor.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME STARTING WITH 'CONTA'")
print("\nTables starting with CONTA:")
for row in cursor.fetchall():
    print(row[0].strip())

conn.close()
