import firebirdsql, os
from dotenv import load_dotenv
load_dotenv('.env', override=True)

conn = firebirdsql.connect(
    host=os.environ.get('FIREBIRD_HOST','localhost'),
    port=int(os.environ.get('FIREBIRD_PORT','3050')),
    database=os.environ.get('DB_PATH_VULCANO', r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb'),
    user=os.environ.get('FIREBIRD_USER','SYSDBA'),
    password=os.environ.get('FIREBIRD_PASSWORD','masterkey'),
    charset='WIN1252'
)
cur = conn.cursor()
cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='EMPREENDIMENTO' ORDER BY RDB$FIELD_POSITION")
cols = [r[0].strip() for r in cur.fetchall()]
print("Todas as colunas de EMPREENDIMENTO:")
for c in cols:
    print(" >", c)
print("\nColunas com CONTA/CUSTO/ESTAN:")
for c in cols:
    if any(x in c for x in ['CONTA','CUSTO','ESTAN','ESTCON']):
        print(" >>", c)
conn.close()
