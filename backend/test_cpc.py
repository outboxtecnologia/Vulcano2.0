import sqlite3
from main import get_conn, POC_DATABASE_FILE

def test_dynamic_cpc47(id_emp, mes, ano):
    conn_v = get_conn("vulcano")
    cur = conn_v.cursor()
    cur.execute("SELECT NOME FROM EMPREENDIMENTO WHERE ID = ?", (id_emp,))
    nome_emp = cur.fetchone()[0]
    
    fracao_vendida = 0.9087 # mocked from screenshot 90.87%
    
    cur.execute("""
        SELECT ANO, MES, SUM(CUSTO_TOTAL) 
        FROM POC_CUSTO_MENSAL_REAL 
        WHERE ID_EMPREENDIMENTO = ? 
        GROUP BY ANO, MES 
    """, (id_emp,))
    spends = cur.fetchall()
    
    conn_lite = sqlite3.connect(POC_DATABASE_FILE)
    cur_lite = conn_lite.cursor()
    cur_lite.execute("SELECT periodo, percentual FROM evolucao_obras WHERE empreendimento = ?", (nome_emp,))
    pocs_raw = cur_lite.fetchall()
    
    # Get all distinct periods before (ano, mes)
    periods = set()
    spend_dict = {}
    for (a, m, val) in spends:
        if a < ano or (a == ano and m < mes):
            per = f"{str(a).zfill(4)}-{str(m).zfill(2)}"
            periods.add(per)
            spend_dict[per] = float(val)
            
    poc_dict = {}
    for (per, pct) in pocs_raw:
        a = int(per.split('-')[0])
        m = int(per.split('-')[1])
        if a < ano or (a == ano and m < mes):
            periods.add(per)
            poc_dict[per] = float(pct)
            
    sorted_periods = sorted(list(periods))
    
    def get_poc_for_period(target):
        best_poc = 0.0
        for per, pct in sorted(poc_dict.items()):
            if per <= target:
                best_poc = pct
            else:
                break
        return best_poc

    historico_calc = []
    running_gasto = 0.0
    prev_custo_acumulado = 0.0
    
    for per in sorted_periods:
        gasto_mes = spend_dict.get(per, 0.0)
        running_gasto += gasto_mes
        
        poc_m = get_poc_for_period(per)
        
        custo_acumulado_req = running_gasto * fracao_vendida * (poc_m / 100.0)
        valor_mensal = custo_acumulado_req - prev_custo_acumulado
        
        if abs(valor_mensal) >= 0.01:
            historico_calc.append({
                "periodo": per,
                "valor": valor_mensal,
                "poc": poc_m,
                "gasto_acumulado": running_gasto
            })
            
        prev_custo_acumulado = custo_acumulado_req
        
    return historico_calc

if __name__ == "__main__":
    res = test_dynamic_cpc47(204, 12, 2025) # ID for stuttgart maybe? Let's check.
    for r in res:
        print(r)
