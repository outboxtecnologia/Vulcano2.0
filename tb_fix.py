with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

old_logic = '''            if num_conta:
                cur_q.execute("""
                    SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOCTB)
                    FROM LCTOCTB
                    WHERE CODIGOEMPRESA = ? 
                      AND CONTACTBCRED = ?
                      AND CAST(COMPLHIST AS BLOB SUB_TYPE 0) LIKE ?
                    GROUP BY 1, 2 ORDER BY 1, 2
                """, (empresa_id, num_conta, f'%{apto_str}%'))
                mapa_creditos = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_q.fetchall()}
            else:
                mapa_creditos = {}
            
            # Racional Híbrido Temporal
            linhas_temporal = []
            u_dt_v_str = str(u_dt_venda).strip()
            u_ano_venda = int(u_dt_v_str[:4]) if len(u_dt_v_str) >= 4 and u_dt_v_str[:4].isdigit() else 9999
            u_mes_venda = int(u_dt_v_str[5:7]) if len(u_dt_v_str) >= 7 and u_dt_v_str[5:7].isdigit() else 12

            acumulado_v2 = 0
            acumulado_v1 = 0

            for c in custos_questor:
                k = f"{c['ano']}-{c['mes']}"
                custo_fis = c["custo"] * fracao'''

new_logic = '''            # Busca Ampla de Creditos do Apartamento (Receitas/CPV Grupo 3 ou 5)
            cur_q.execute("""
                SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOCTB)
                FROM LCTOCTB
                WHERE CODIGOEMPRESA = ? 
                  AND CAST(COMPLHIST AS BLOB SUB_TYPE 0) LIKE ?
                  AND CONTACTBCRED IS NOT NULL 
                  AND (CAST(CONTACTBCRED AS VARCHAR(10)) LIKE '3%' OR CAST(CONTACTBCRED AS VARCHAR(10)) LIKE '5%')
                GROUP BY 1, 2 ORDER BY 1, 2
            """, (empresa_id, f'%{apto_str}%'))
            mapa_creditos = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_q.fetchall()}
            
            # Racional Híbrido Temporal
            linhas_temporal = []
            u_dt_v_str = str(u_dt_venda).strip()
            u_ano_venda = int(u_dt_v_str[:4]) if len(u_dt_v_str) >= 4 and u_dt_v_str[:4].isdigit() else 9999
            u_mes_venda = int(u_dt_v_str[5:7]) if len(u_dt_v_str) >= 7 and u_dt_v_str[5:7].isdigit() else 12

            acumulado_v2 = 0
            acumulado_v1 = 0

            chaves_unicas = set()
            for c in custos_questor: chaves_unicas.add(f"{c['ano']}-{c['mes']}")
            for k in mapa_receb.keys(): chaves_unicas.add(k)
            for k in mapa_creditos.keys(): chaves_unicas.add(k)
            
            meses_ordenados = sorted([ {"ano": int(k.split('-')[0]), "mes": int(k.split('-')[1])} for k in chaves_unicas ], key=lambda x: (x["ano"], x["mes"]))

            for c in meses_ordenados:
                k = f"{c['ano']}-{c['mes']}"
                custo_orig = next((cq["custo"] for cq in custos_questor if cq["ano"] == c["ano"] and cq["mes"] == c["mes"]), 0)
                custo_fis = custo_orig * fracao'''

text = text.replace(old_logic, new_logic)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Temporal Matrix to prevent month dropping and broaden Credit catching!")
