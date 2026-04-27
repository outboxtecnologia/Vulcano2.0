import firebirdsql
import time
import os

DB_PATH = r"C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB"
HOST = "127.0.0.1"

print(f"Testing connection to {DB_PATH} at {HOST}...")
start = time.time()
try:
    conn = firebirdsql.connect(
        host=HOST,
        database=DB_PATH,
        port=3050,
        user="SYSDBA",
        password="masterkey",
        charset="WIN1252"
    )
    print(f"Success! Connected in {time.time() - start:.2f} seconds.")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM EMPRESA")
    count = cur.fetchone()[0]
    print(f"Found {count} empresas.")
    conn.close()
except Exception as e:
    print(f"FAILED in {time.time() - start:.2f} seconds.")
    print(f"Error: {e}")
