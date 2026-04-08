import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import get_conn

def test_query():
    conn_v = get_conn("vulcano")
    cur_v = conn_v.cursor()
    cur_v.execute("SELECT ID, NOME, CODIGOCENTROCUSTO FROM EMPREENDIMENTO WHERE NOME LIKE '%STUTT%' OR NOME LIKE '%Stutt%'")
    stutt = cur_v.fetchone()
    print("Stuttgart Vol:", stutt)
    cc = int(stutt[2])
    conn_v.close()
    
    conn_q = get_conn("questor")
    cur_q = conn_q.cursor()
    
    query = """
        SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0)
        FROM LCTOGER G
        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
        WHERE G.CODIGOEMPRESA = 959 AND G.CODIGOCENTROCUSTO = ? 
        AND C.DATALCTOCTB >= '2025-06-01' AND C.DATALCTOCTB < '2025-07-01'
    """
    cur_q.execute(query, (cc,))
    logs = cur_q.fetchall()
    
    print(f"Buscado {len(logs)} registros via BLOB.")
    err_count = 0
    for r in logs:
        # r[2] usually comes back as bytes or string depending on firebirdsql blob read
        val = r[2]
        if isinstance(val, (bytes, bytearray)):
            s = val.decode('win1252', 'ignore')
        else:
            s = str(val)
            
    print("Success reading all rows without crashing inside fetchall().")
    conn_q.close()

if __name__ == "__main__":
    test_query()
