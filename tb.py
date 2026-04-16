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
    
    cur.execute("SELECT COUNT(*) FROM RECEBER WHERE DATA >= '2025-03-01' AND DATA < '2025-04-01' AND TOTALPAGO > 0")
    print("Vencimento em Março (TOTALPAGO > 0):", cur.fetchone()[0])
    
    cur.execute("SELECT COUNT(*) FROM RECEBER WHERE DATA_PAGAMENTO >= '2025-03-01' AND DATA_PAGAMENTO < '2025-04-01' AND TOTALPAGO > 0")
    print("Pagamento Certo em Março (TOTALPAGO > 0):", cur.fetchone()[0])
    
except Exception as e:
    print('Erro', e)
