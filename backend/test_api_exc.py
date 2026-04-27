import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

conn_q = get_conn("questor")
cur_q = conn_q.cursor()

def test_api():
    try:
        cur_q.execute("""
            SELECT SUM(CASE WHEN CONTACTBDEB = ? THEN VALORLCTOCTB ELSE -VALORLCTOCTB END)
            FROM LCTOCTB
            WHERE CODIGOEMPRESA = ?
              AND (CONTACTBDEB = ? OR CONTACTBCRED = ?)
              AND DATALCTOCTB < CAST(? AS DATE)
              AND (CODIGOORIGLCTOCTB IS NULL OR CODIGOORIGLCTOCTB <> 'ZZ')
        """, (5665, 959, 5665, 5665, "2025-01-01"))
        print("Success:", cur_q.fetchone())
    except Exception as e:
        import traceback
        traceback.print_exc()

test_api()
