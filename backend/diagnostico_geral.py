import os
import sys

# Força o sys.path para garantir que o fastapi modules locais resolvam
sys.path.insert(0, os.path.abspath("."))

from main import get_conn, get_receitas_caixa
import sqlite3

def run_diagnostico(empresa_id=959, ano=2024, mes=4, nome_busca="STUTTGART"):
    conn_v = get_conn("vulcano")
    cur_v = conn_v.cursor()
    
    print("=== DIAGNÓSTICO GERAL DE CONTABILIZAÇÕES VIRTUAIS ===")
    
    # Busca o empreendimento de teste
    cur_v.execute(f"SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTAADICLI, CONTACAIXA FROM EMPREENDIMENTO WHERE NOME LIKE '%{nome_busca}%'")
    emp_db = cur_v.fetchone()
    if not emp_db:
        print("Empreendimento não encontrado.")
        return
        
    emp_id = emp_db[0]
    nome_emp = emp_db[1]
    conta_custo = emp_db[3]
    conta_cli = emp_db[4]
    
    print(f"Empreendimento Alvo: {nome_emp} (ID: {emp_id})")
    print(f"Contas -> CUSTO: {conta_custo}, CLI: {conta_cli}")
    
    # 1. VERIFICANDO RECEITAS
    print(f"\n1. Buscando /api/receitas-caixa para {ano}-{mes:02d}...")
    try:
        resp = get_receitas_caixa(empresa_id=empresa_id, data_ini=f"{ano}-{mes:02d}", data_fim=f"{ano}-{mes:02d}")
        receitas_meta = resp.get("dashboard_meta", {})
        meta_emp = receitas_meta.get(nome_emp, {})
        print(f"-> Chaves retornadas do Pandas para {nome_emp}:", list(meta_emp.keys()) if meta_emp else "VAZIO!")
        if meta_emp:
            print("-> Dados Receitas/Tributos:", meta_emp)
    except Exception as e:
        print("Erro ao buscar receitas:", e)

    # 2. VERIFICANDO POC FÍSICO (SQLITE)
    print(f"\n2. Buscando POC Físico (sqlite) para {ano}-{mes:02d}...")
    poc_mensal = 0.0
    try:
        conn_lite = sqlite3.connect("poc_database.sqlite")
        cur_lite = conn_lite.cursor()
        
        cur_lite.execute("SELECT periodo, percentual FROM evolucao_obras WHERE empreendimento = ?", (nome_emp,))
        todas_datas = cur_lite.fetchall()
        print("-> Datas POC existentes para este Empreendimento:", todas_datas)
        
        cur_lite.execute("SELECT percentual FROM evolucao_obras WHERE empreendimento = ? AND (periodo = ? OR periodo LIKE ?)", 
                         (nome_emp, f"{ano}-{mes:02d}", f"%{mes:02d}/{ano}"))
        row = cur_lite.fetchone()
        if row: 
            poc_mensal = float(row[0] or 0)
        print(f"-> POC Encontrado para o mês: {poc_mensal}%")
    except Exception as e:
        print("Erro ao buscar POC:", e)
        
    # 3. VERIFICANDO CUSTO ACUMULADO REAL NO VULCANO
    print(f"\n3. Buscando Custo Acumulado Real no Vulcano para {ano}-{mes:02d}...")
    custo_real_gasto = 0.0
    try:
        cur_v.execute("SELECT SUM(CUSTO_TOTAL) FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES <= ?))", 
                      (emp_id, ano, ano, mes))
        crg = cur_v.fetchone()
        if crg and crg[0]: 
            custo_real_gasto = float(crg[0])
        print(f"-> Custo Acumulado Total: {custo_real_gasto}")
    except Exception as e:
        print("Erro ao buscar Custo Real:", e)

    # 4. AVALIAÇÃO DE INJEÇÃO
    print("\n--- RESUMO DE INJEÇÃO VIRTUAL ---")
    valor_poc = custo_real_gasto * (poc_mensal / 100.0)
    print(f"Valor POC a Injetar: R$ {valor_poc:.2f} (Custo {custo_real_gasto} * {poc_mensal}%)")
    if valor_poc > 0 and conta_custo:
        print(">> VERIFICADO: Lançamento POC DEVE OCORRER na conta", conta_custo)
    else:
        print(">> BLOQUEADO: Lançamento POC NÃO ocorrerá.")
        
    if meta_emp:
        caixa = meta_emp.get("RECEITA_CAIXA", 0.0)
        if caixa > 0:
            print(f">> VERIFICADO: Lançamento de Recebimento de R$ {caixa:.2f}")
        else:
            print(">> BLOQUEADO: Sem Receita Caixa.")
            
        ret = meta_emp.get("RET", 0)
        if ret > 0:
            print(f">> VERIFICADO: Lançamento de Tributos (ex RET) de R$ {ret:.2f}")
    else:
         print(">> BLOQUEADO: Sem Recebimentos/Tributos.")
         
if __name__ == "__main__":
    with open("diagnostico_geral_saida.log", "w", encoding='utf-8') as f:
        sys.stdout = f
        sys.stderr = f
        run_diagnostico()
