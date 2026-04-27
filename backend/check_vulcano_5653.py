import traceback
import sys
import os

from core.services.database import get_vulcano_db

def main():
    try:
        conn = get_vulcano_db()
        cur = conn.cursor()
        
        query = """
            SELECT FIRST 10 DATA, VALOR, ID_EMPREENDIMENTO, ID_CONTA_DEBITO, ID_CONTA_CREDITO
            FROM LANCAMENTO_CONTABIL
            WHERE (ID_CONTA_DEBITO = 5653 OR ID_CONTA_CREDITO = 5653)
              AND DATA >= CAST('2025-11-01' AS DATE) AND DATA < CAST('2025-12-01' AS DATE)
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
