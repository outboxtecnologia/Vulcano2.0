import os
import sys
import time

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

def test_query():
    print("Testing query speed...")
    conn = get_conn("vulcano")
    
    query1 = """
        SELECT count(*)
        FROM VENDA v
        JOIN RECEBER r ON r.IDVENDA = v.ID
        WHERE v.CODIGOEMPRESA = 95
        AND v.IDEMPREENDIMENTO = 2
    """
    
    query2 = """
        SELECT count(*)
        FROM VENDA v
        JOIN RECEBER r ON r.IDVENDA = v.ID
        WHERE v.CODIGOEMPRESA = 95
        AND v.IDEMPREENDIMENTO = 2
        AND r.DATA >= CAST('2020-01-01' AS DATE)
    """
    
    query2 = """
        SELECT count(*)
        FROM RECEBER r
        JOIN VENDA v ON r.IDVENDA = v.ID
        LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
        LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
        WHERE v.CODIGOEMPRESA = 95
        AND v.IDEMPREENDIMENTO = 2
        AND r.DATA >= '2020-01-01'
    """
    
    start = time.time()
    cur = conn.cursor()
    cur.execute(query1)
    res1 = cur.fetchone()
    t1 = time.time() - start
    print(f"Query 1 (No filters): {res1[0]} rows. Time: {t1:.2f}s")
    
    # Try fetching all rows instead of count since pandas reads all data
    query3 = """
        SELECT r.DATA, r.TOTALPAGO, r.VALORPARCELA, r.VALORVARIACAO, v.DESCUNIDIMOB, c.CNPJ, r.PARCELA, c.NOME AS CLIENTE_NOME, e.NOME AS EMPREENDIMENTO, r.OBS, r.ID, v.TOTALVENDA, r.DESCONTO
        FROM RECEBER r
        JOIN VENDA v ON r.IDVENDA = v.ID
        LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID
        LEFT JOIN EMPREENDIMENTO e ON v.IDEMPREENDIMENTO = e.ID
        WHERE v.CODIGOEMPRESA = 95
    """
    start = time.time()
    try:
        cur.execute(query3)
        rows = cur.fetchall()
        t3 = time.time() - start
        print(f"Query 3: Feched {len(rows)} records. Time: {t3:.2f}s")
    except Exception as e:
        print(f"Query 3 failed: {e}")
    
    conn.close()

if __name__ == "__main__":
    test_query()
