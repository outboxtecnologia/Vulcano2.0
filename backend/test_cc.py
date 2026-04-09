import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()
cur.execute("SELECT ID, NOME, CODIGOCENTROCUSTO FROM EMPREENDIMENTO")
rows = cur.fetchall()
for r in rows:
    if "STUTTGART" in (r[1] or "").upper():
        print(r)
