import sys, os, math
import traceback
import pandas as pd
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

def run():
    cq = get_conn('questor')
    cv = get_conn('vulcano')
    
    print("Buscando amostras...")
    cur_v = cv.cursor()
    cur_v.execute("""
        SELECT r.DATA, r.VALORPARCELA, r.VALORVARIACAO, r.TOTALPAGO, v.DESCUNIDIMOB, v.DTOPER AS DATAVENDA, r.OBS
        FROM RECEBER r
        JOIN VENDA v ON v.ID = r.IDVENDA
        WHERE r.TOTALPAGO > 0 AND EXTRACT(YEAR FROM r.DATA) >= 2024 AND r.VALORVARIACAO > 0
        ORDER BY r.DATA DESC
    """)
    rows_v = cur_v.fetchall()[:200]
    
    cur_q = cq.cursor()
    cur_q.execute("""
        SELECT DATALCTOCTB, VALORLCTOCTB
        FROM LCTOCTB
        WHERE EXTRACT(YEAR FROM DATALCTOCTB) >= 2024 AND CODIGOORIGLCTOCTB <> 'ZZ'
    """)
    rows_q = cur_q.fetchall()
    
    df_q = pd.DataFrame(rows_q, columns=["data", "valor"])
    df_q['data'] = pd.to_datetime(df_q['data'])
    df_q['valor'] = df_q['valor'].astype(float)
    
    matches_total = 0
    matches_principal = 0
    desvios = []

    for r in rows_v:
        d_v = pd.to_datetime(r[0])
        v_princ = float(r[1] or 0)
        v_cub = float(r[2] or 0)
        v_tot = float(r[3] or 0)
        uni = r[4]
        
        q_perto = df_q[abs((df_q['data'] - d_v).dt.days) <= 35]
        
        mt = q_perto[abs(q_perto['valor'] - v_tot) <= 0.05]
        if not mt.empty:
            matches_total += 1
            continue
            
        mp = q_perto[abs(q_perto['valor'] - v_princ) <= 0.05]
        if not mp.empty:
            matches_principal += 1
            cub_cand = q_perto[abs(q_perto['valor'] - v_cub) <= 0.05]
            if not cub_cand.empty:
                print(f"Questor separou CUB! Unid {uni}. Princ {v_princ} Variacao {v_cub}")
            continue
            
        q_closest = q_perto.iloc[(q_perto['valor'] - v_tot).abs().argsort()[:1]]
        if not q_closest.empty:
            q_val = float(q_closest['valor'].iloc[0])
            diff = q_val - v_tot
            if abs(diff) < v_tot * 0.15: 
                desvios.append((uni, v_tot, q_val, diff, v_cub, r[6], d_v))

    print(f"Matches exatos com Total Pago: {matches_total}")
    print(f"Matches exatos com Principal: {matches_principal}")
    
    print("\nAmostra de Desvios (Questor vs Vulcano Total):")
    for d in desvios[:15]:
        print(f"Data {d[6].date()} | Unid {d[0]} | Tot Vulcano: R${d[1]:.2f} (CUB no Vulcano: R${d[4]:.2f}) | Lanc Questor prox: R${d[2]:.2f} | Dif: R${d[3]:.2f} | OBS/Multa: {d[5]}")

try:
    run()
except Exception as e:
    traceback.print_exc()
