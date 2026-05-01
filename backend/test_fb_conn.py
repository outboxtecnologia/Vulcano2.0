import firebirdsql
import sys

try:
    print("Connecting to Firebird...")
    conn = firebirdsql.connect(
        host='localhost',
        database=r'D:\Questor_Restore\Questor.fdb',
        port=3050,
        user='SYSDBA',
        password='masterkey',
        charset='UTF8'
    )
    print("SUCCESS: Connected to Firebird successfully.")
    cur = conn.cursor()
    cur.execute("SELECT FIRST 1 NOMEEMPRESA FROM EMPRESA")
    row = cur.fetchone()
    print("Company Name from restored DB:", row[0] if row else "None")
    conn.close()
    sys.exit(0)
except Exception as e:
    print("FAILED:", str(e))
    sys.exit(1)
