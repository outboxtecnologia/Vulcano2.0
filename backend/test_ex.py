import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

def test_api():
    conn_q = get_conn("questor")
    cur_q = conn_q.cursor()
    conta_id = 5665
    empresa_id = 959
    data_ini = "2025-01-01"
    cur_q.execute("""
        SELECT SUM(CASE WHEN CONTACTBDEB = ? THEN VALORLCTOCTB ELSE -VALORLCTOCTB END)
        FROM LCTOCTB
        WHERE CODIGOEMPRESA = ?
          AND (CONTACTBDEB = ? OR CONTACTBCRED = ?)
          AND DATALCTOCTB < CAST(? AS DATE)
          AND (CODIGOORIGLCTOCTB IS NULL OR CODIGOORIGLCTOCTB <> 'ZZ')
    """, (conta_id, empresa_id, conta_id, conta_id, data_ini))
    print(cur_q.fetchone())

test_api()
