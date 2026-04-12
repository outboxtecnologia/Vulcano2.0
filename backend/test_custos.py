import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.db.db_firebird import get_questor_connection, get_vulcano_connection

def test():
    conn_q = get_questor_connection(959)
    conn_v = get_vulcano_connection()
    cur_q = conn_q.cursor()
    cur_v = conn_v.cursor()

    cur_v.execute("SELECT ID, NOME, CENTRO_CUSTO FROM EMPREENDIMENTO")
    emps = cur_v.fetchall()

    for emp_id, nome, cc in emps:
        if not cc: continue
        cur_q.execute("""
            SELECT SUM(G.VALORLCTOGER * G.NATURLCTOCTB)
            FROM LCTOGER G
            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
            WHERE G.CODIGOEMPRESA = 959 AND G.CODIGOCENTROCUSTO = ?
            AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
            AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
        """, (cc,))
        row = cur_q.fetchone()
        custo = float(row[0] or 0.0)
        print(f"Emp: {nome} (CC {cc}) -> Custo Gasto: {custo}")

test()
