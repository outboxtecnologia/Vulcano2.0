import os
import sys
import traceback

# Força o sys.path para garantir que o fastapi modules locais resolvam (simulando a raiz)
sys.path.insert(0, os.path.abspath(".."))

from main import get_conn

def test_queries():
    empresa_id = 959
    empreendimento_id = "6400000000003"
    ano = 2024
    mes = 4
    
    print("--- TESTE DE ENGENHARIA CONSOLIDADO (Regra 3 do SETUP) ---")
    
    try:
        print("1. Conectando Vulcano...")
        conn_v = get_conn("vulcano")
        cur_v = conn_v.cursor()
        
        
        print(f"3. Query EMPREENDIMENTO DUMP...")
        cur_v.execute(f"SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTACLI, CONTACAIXA FROM EMPREENDIMENTO WHERE CODIGOEMPRESA = {empresa_id} AND ATIVO = 'S'")
        res = cur_v.fetchall()
        print("Empreendimentos Ativos:")
        for r in res:
            print(f"- ID: {r[0]}, NOME: {r[1]}, CC: {r[2]}, Conta Custo: {r[3]}, CLI: {r[4]}, CAIXA: {r[5]}")
        
        print("4. Conectando Questor...")
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        
        date_str = f"{ano}-{str(mes).zfill(2)}-01"
        print(f"5. Query LCTOGER...")
        cur_q.execute("""
            SELECT SUM(G.VALORLCTOGER) as TOTAL
            FROM LCTOGER G
            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
            WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ? AND C.DATALCTOCTB < CAST(? AS DATE)
        """, (empresa_id, cc, date_str))
        res2 = cur_q.fetchall()
        print("LCTOGER Questor OK:", res2)
        
        print("6. Query POC CUSTO MENSAL REAL com int {emp_id_int}...")
        cur_v.execute("SELECT SUM(CUSTO_TOTAL) FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES <= ?))", (empresa_id, ano, ano, mes))
        crg = cur_v.fetchone()
        print("Custo Mensal Real OK:", crg)

        print("\n[SUCESSO] Todas as queries blindadas passaram com sucesso.")

    except Exception as e:
        print("\n[ERRO CRITICO ENCONTRADO]:", str(e))
        traceback.print_exc(file=sys.stdout)
        
if __name__ == "__main__":
    with open("test_out.log", "w") as f:
        sys.stdout = f
        sys.stderr = f
        test_queries()
