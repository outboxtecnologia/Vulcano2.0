import traceback
import sys
import os

# Append backend path so we can import modules
sys.path.append(os.path.abspath("backend"))

from backend.core.services.database import get_vulcano_db

def main():
    try:
        conn = get_vulcano_db()
        cur = conn.cursor()
        print("Connected to Vulcano Firebird.")
        
        query = """
            SELECT FIRST 10 DATA, VALOR, ID_EMPREENDIMENTO, ID_CONTA_DEBITO, ID_CONTA_CREDITO
            FROM LANCAMENTO_CONTABIL
            WHERE (ID_CONTA_DEBITO = 5653 OR ID_CONTA_CREDITO = 5653)
              AND DATA >= '2025-11-01' AND DATA < '2025-12-01'
        """
        cur.execute(query)
        rows = cur.fetchall()
        print(f"Found {len(rows)} rows for 5653 in Nov 2025:")
        for r in rows:
            print(r)
            
        conn.close()
    except Exception as e:
        print("Error:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
