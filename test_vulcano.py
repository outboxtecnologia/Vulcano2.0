import sys, os
sys.path.insert(0, os.path.abspath('backend'))
import firebirdsql
import dotenv
dotenv.load_dotenv('backend/.env')
try:
    conn = firebirdsql.connect(
        host='localhost',
        database=r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb",
        port=3050,
        user='SYSDBA',
        password='masterkey',
        charset='WIN1252'
    )
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 v.DESCUNIDIMOB, r.DATA, r.TOTALPAGO FROM VENDA v JOIN RECEBER r ON r.IDVENDA = v.ID WHERE r.TOTALPAGO > 0")
    print("Massa Vulcano viva:", cur.fetchone())
except Exception as e:
    pass
