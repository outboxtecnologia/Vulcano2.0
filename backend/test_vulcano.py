import sys
sys.path.insert(0, r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute("""
    SELECT p.ID, p.DATA, p.VALOR, p.VALOR_PAGO
    FROM VENDAFORMAPAGTOPRAZO p
    JOIN VENDAFORMAPAGTO vfp ON vfp.ID = p.IDVENDAFORMAPAGTO
    WHERE vfp.IDVENDA = 16278
""")
print("Prazos:")
for r in cur.fetchall():
    print(r)
