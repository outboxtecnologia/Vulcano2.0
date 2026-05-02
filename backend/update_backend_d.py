import re

with open(r'D:\vulcano2.0\backend\main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. TIMELINE FIX WITH FILTER + HISTORICO ARRAY
timeline_target = r'cur\.execute\("SELECT MES, ANO, TOTAL_PERIODO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = \? ORDER BY ANO DESC, MES DESC", \(id_emp,\)\)'
timeline_replacement = '''
        cur.execute("SELECT MES, ANO, TOTAL_PERIODO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES <= ?)) ORDER BY ANO ASC, MES ASC", (id_emp, ano, ano, mes))
        
        timeline_list = []
        acumulado = emp_detail["custo_reconhecido_anterior"]
        
        # We need historical pocs before this month for the dropdown
        cur.execute("SELECT MES, ANO, TOTAL_PERIODO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES < ?)) ORDER BY ANO DESC, MES DESC", (id_emp, ano, ano, mes))
        emp_detail["historico_anterior"] = [
            {
                "periodo": f"{str(h[1]).zfill(4)}-{str(h[0]).zfill(2)}",
                "valor": float(h[2] or 0)
            } for h in cur.fetchall()
        ]
        
        cur.execute("SELECT MES, ANO, TOTAL_PERIODO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ? AND (ANO < ? OR (ANO = ? AND MES <= ?)) ORDER BY ANO DESC, MES DESC", (id_emp, ano, ano, mes))
'''

code = code.replace(timeline_target, timeline_replacement)

# 2. CONTA NAMES INJECTION
conta_target = r'"conta_custo": r\[3\], "conta_estoque": r\[4\], "conta_estconc": r\[5\], "codigo_cc": cc_emp\n        \}'
conta_replacement = '''"conta_custo": r[3], "conta_estoque": r[4], "conta_estconc": r[5], "codigo_cc": cc_emp
        }
        
        # --- BUSCA NOME DAS CONTAS QUESTOR ---
        emp_detail["conta_custo_nome"] = ""
        emp_detail["conta_estoque_nome"] = ""
        emp_detail["conta_estconc_nome"] = ""
        
        try:
            conn_q = get_conn("questor")
            cur_q = conn_q.cursor()
            contas_query = [int(n) for n in [r[3], r[4], r[5]] if n]
            if contas_query:
                placeholders = ",".join(["?"] * len(contas_query))
                cur_q.execute(f"SELECT CODIGOCONTAGRUPOEMP, DESCRCONTA FROM PLANOGRUPOEMPRESACONTAS WHERE CODIGOCONTAGRUPOEMP IN ({placeholders})", contas_query)
                map_contas = {row[0]: row[1] for row in cur_q.fetchall()}
                emp_detail["conta_custo_nome"] = map_contas.get(int(r[3]), "") if r[3] else ""
                emp_detail["conta_estoque_nome"] = map_contas.get(int(r[4]), "") if r[4] else ""
                emp_detail["conta_estconc_nome"] = map_contas.get(int(r[5]), "") if r[5] else ""
        except Exception as e:
            print("Erro Nomes Contas:", e)
'''
code = code.replace(conta_target, conta_replacement)

with open(r'D:\vulcano2.0\backend\main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("UPDATED main.py OK")
