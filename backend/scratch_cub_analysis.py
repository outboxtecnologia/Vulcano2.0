import sys
import os
import pandas as pd
import duckdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

def analyze():
    print("Conectando aos bancos localmente para rastrear o CUB...")
    try:
        cq = get_conn("questor")
        cv = get_conn("vulcano")
    except Exception as e:
        print(f"Erro BD: {e}")
        return
        
    cur_v = cv.cursor()
    # Pega amostra de recebimentos no Vulcano com variação
    cur_v.execute("""
        SELECT r.DATA, r.VALORPARCELA as principal_vulcano, r.VALORVARIACAO as cub_vulcano, r.TOTALPAGO as total_vulcano, v.DESCUNIDIMOB, v.DTOPER AS DATAVENDA
        FROM RECEBER r
        JOIN VENDA v ON v.ID = r.IDVENDA
        JOIN VENDAUNIDADE vu ON vu.IDVENDA = v.ID
        JOIN UNIDADE u ON u.ID = vu.IDUNIDADE
        JOIN BLOCO b ON b.ID = u.IDBLOCO
        WHERE r.TOTALPAGO > 0 AND EXTRACT(YEAR FROM r.DATA) >= 2024
        ORDER BY r.DATA DESC
    """)
    v_rows = cur_v.fetchall()
    print(f"Buscados {len(v_rows)} recebimentos do Vulcano.")
    
    cur_q = cq.cursor()
    
    cur_q.execute("""
        SELECT DATALCTOCTB, VALORLCTOCTB
        FROM LCTOCTB
        WHERE EXTRACT(YEAR FROM DATALCTOCTB) >= 2024
          AND CODIGOORIGLCTOCTB <> 'ZZ'
    """)
    q_rows = cur_q.fetchall()
    print(f"Buscados {len(q_rows)} lançamentos do Questor.")

    df_v = pd.DataFrame(v_rows, columns=["data_rec", "principal", "cub", "total", "unidade", "data_venda"])
    df_q = pd.DataFrame(q_rows, columns=["data", "valor"])
    
    df_v['data_rec'] = pd.to_datetime(df_v['data_rec'])
    df_q['data'] = pd.to_datetime(df_q['data'])
    
    # Preencher NaN
    df_v['cub'] = df_v['cub'].fillna(0)
    df_v['principal'] = df_v['principal'].fillna(0)
    df_v['total'] = df_v['total'].fillna(0)
    
    match_por_principal = 0
    match_por_total = 0
    
    # Amostra de recebimentos do Vulcano que TINHAM CUB > 0
    df_v_com_cub = df_v[df_v['cub'] > 0.01].head(50)
    print(f"Cruamento com {len(df_v_com_cub)} recebimentos que tiveram CUB > 0...")
    
    for _, rv in df_v_com_cub.iterrows():
        # Busca no Questor no mesmo dia e até 2 dias de diferença
        q_perto = df_q[abs((df_q['data'] - rv['data_rec']).dt.days) <= 2]
        
        # Procura match exato do Total
        mt = q_perto[abs(q_perto['valor'] - float(rv['total'])) < 0.02]
        if not mt.empty:
            match_por_total += 1
            print(f"Unidade {rv['unidade']} (Venda: {rv['data_venda']}, Pagto: {rv['data_rec'].date()}): Questor lançou o TOTAL c/ CUB! (R$ {rv['total']})")
            continue
            
        # Procura match do Principal
        mp = q_perto[abs(q_perto['valor'] - float(rv['principal'])) < 0.02]
        if not mp.empty:
            match_por_principal += 1
            print(f"Unidade {rv['unidade']} (Venda: {rv['data_venda']}, Pagto: {rv['data_rec'].date()}): Questor lançou SÓ O PRINCIPAL! {rv['principal']} (Questor separou o CUB de {rv['cub']})")
        else:
            print(f"Unidade {rv['unidade']}: Sem match. Princ: {rv['principal']}, CUB: {rv['cub']}, Tot: {rv['total']}")

    print(f"\nResumo da Amostra (n={len(df_v_com_cub)}):\nQuestor aglutinou Total: {match_por_total}\nQuestor isolou o Principal: {match_por_principal}")

if __name__ == '__main__':
    analyze()
