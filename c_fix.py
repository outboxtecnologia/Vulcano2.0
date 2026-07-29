with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

old_logic = '''            # Racional Híbrido Temporal
            linhas_temporal = []
            for c in custos_questor:
                k = f"{c['ano']}-{c['mes']}"
                custo_v2 = c["custo"] * fracao
                custo_v1 = custo_v2 * (mapa_poc.get(k, 0) / 100) if mapa_poc.get(k, 0) > 0 else 0
                
                linhas_temporal.append({'''

new_logic = '''            # Racional Híbrido Temporal
            linhas_temporal = []
            u_dt_v_str = str(u_dt_venda).strip()
            u_ano_venda = int(u_dt_v_str[:4]) if len(u_dt_v_str) >= 4 and u_dt_v_str[:4].isdigit() else 9999
            u_mes_venda = int(u_dt_v_str[5:7]) if len(u_dt_v_str) >= 7 and u_dt_v_str[5:7].isdigit() else 12

            acumulado_v2 = 0
            acumulado_v1 = 0

            for c in custos_questor:
                k = f"{c['ano']}-{c['mes']}"
                custo_fis = c["custo"] * fracao
                custo_fis_v1 = custo_fis * (mapa_poc.get(k, 0) / 100) if mapa_poc.get(k, 0) > 0 else 0
                
                is_before_sale = (c['ano'] < u_ano_venda) or (c['ano'] == u_ano_venda and c['mes'] < u_mes_venda)
                is_sale_month = (c['ano'] == u_ano_venda and c['mes'] == u_mes_venda)

                if is_before_sale:
                    acumulado_v2 += custo_fis
                    acumulado_v1 += custo_fis_v1
                    custo_v2 = 0
                    custo_v1 = 0
                elif is_sale_month:
                    custo_v2 = custo_fis + acumulado_v2
                    custo_v1 = custo_fis_v1 + acumulado_v1
                    acumulado_v2 = 0
                    acumulado_v1 = 0
                else:
                    custo_v2 = custo_fis
                    custo_v1 = custo_fis_v1

                linhas_temporal.append({'''

text = text.replace(old_logic, new_logic)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated CPV calculation to clamp before Venda!")
