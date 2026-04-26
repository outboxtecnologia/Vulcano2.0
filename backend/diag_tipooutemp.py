"""Checa TIPOOUTEMP valores reais para empresa 959."""
import firebirdsql, os
from dotenv import load_dotenv
load_dotenv()

conn = firebirdsql.connect(
    host=os.environ.get('FIREBIRD_HOST', 'localhost'),
    database=os.environ.get('DB_PATH_QUESTOR', ''),
    user=os.environ.get('FIREBIRD_USER', 'SYSDBA'),
    password=os.environ.get('FIREBIRD_PASSWORD', 'masterkey'),
    charset='WIN1252'
)

def dec(v):
    if v is None: return ""
    if isinstance(v, bytes): return v.decode('win1252', 'ignore').strip()
    return str(v).strip()

cur = conn.cursor()

# Valores distintos de TIPOOUTEMP
cur.execute("""
    SELECT OEE.TIPOOUTEMP, COUNT(*)
    FROM OUTRAEMPEMP OEE
    WHERE OEE.CODIGOEMPRESA = 959
    GROUP BY OEE.TIPOOUTEMP
    ORDER BY 2 DESC
""")
print("TIPOOUTEMP | COUNT")
for r in cur.fetchall():
    print(f"  '{dec(r[0])}' -> {r[1]}")

# Todos os registros com tipo e inscricao
cur.execute("""
    SELECT OE.CODIGOOUTEMP, OE.NOMEOUTEMP, OE.INSCRFEDERAL, OEE.TIPOOUTEMP, OEE.INSCRFEDPROPRIET
    FROM OUTRAEMPEMP OEE
    JOIN OUTRAEMPRESA OE ON OE.CODIGOOUTEMP = OEE.CODIGOOUTEMP
    WHERE OEE.CODIGOEMPRESA = 959
    ORDER BY OEE.TIPOOUTEMP, OE.NOMEOUTEMP
""")
print("\nTIPO | OUTEMP | NOME | INSCRFEDERAL | INSCRFEDPROPRIET")
print("-" * 100)
for r in cur.fetchall():
    print(f"  {dec(r[3]):4} | {r[0]:6} | {dec(r[1])[:35]:35} | {dec(r[2])[:25]:25} | {dec(r[4])}")

conn.close()
