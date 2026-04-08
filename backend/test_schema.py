import sys
import os
import fdb

def get_conn():
    return fdb.connect(
        host='127.0.0.1',
        database='C:/Questor/Dados/000010.FDB', # Adjust if needed
        user='SYSDBA',
        password='masterkey',
        charset='WIN1252'
    )

def test_schema():
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT FIRST 1 * FROM SALDOCTB")
        print("--- SALDOCTB COLUMNS ---")
        for desc in cur.description:
            print(desc[0])
            
        cur.execute("SELECT FIRST 1 * FROM LCTOGER")
        print("\n--- LCTOGER COLUMNS ---")
        for desc in cur.description:
            print(desc[0])
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    # If the standard connection fails, maybe it's in the actual app connection pool.
    # Let's try importing get_conn from backend.main if available.
    try:
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        from main import get_conn as get_app_conn
        conn = get_app_conn("questor")
        cur = conn.cursor()
        
        cur.execute("SELECT FIRST 1 * FROM SALDOCTB")
        print("--- SALDOCTB COLUMNS (via main) ---")
        for desc in cur.description:
            print(desc[0])
            
        cur.execute("SELECT FIRST 1 * FROM LCTOGER")
        print("\n--- LCTOGER COLUMNS (via main) ---")
        for desc in cur.description:
            print(desc[0])
    except Exception as e:
        print("Failed through main.py:", e)

