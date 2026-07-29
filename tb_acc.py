with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''            for c in meses_ordenados:
                k = f"{c['ano']}-{c['mes']}"
                custo_orig = next((cq["custo"] for cq in custos_questor if cq["ano"] == c["ano"] and cq["mes"] == c["mes"]), 0)
                custo_fis = custo_orig * fracao
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

                linhas_temporal.append({
                    "ano": c["ano"], 
                    "mes": c["mes"], 
                    "custo_questor": custo_orig,
                    "custo_v2_ifrs": round(custo_v2, 2),
                    "custo_v1_legacy": round(custo_v1, 2),
                    "poc_mes": mapa_poc.get(k, 0.0),
                    "cub_mes": mapa_cub.get(k, 0.0),
                    "fluxo_recebido": mapa_receb.get(k, 0.0),
                    "credito_questor": mapa_creditos.get(k, 0.0)
                })'''

new_logic = '''            acumulado_linha_questor = 0
            acumulado_linha_v2 = 0
            for c in meses_ordenados:
                k = f"{c['ano']}-{c['mes']}"
                custo_orig = next((cq["custo"] for cq in custos_questor if cq["ano"] == c["ano"] and cq["mes"] == c["mes"]), 0)
                custo_fis = custo_orig * fracao
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

                custo_questor_fracionado = custo_orig * (fracao * 100) / 100
                acumulado_linha_questor += custo_questor_fracionado
                acumulado_linha_v2 += custo_v2

                linhas_temporal.append({
                    "ano": c["ano"], 
                    "mes": c["mes"], 
                    "custo_questor": custo_orig,
                    "custo_questor_fracionado": custo_questor_fracionado,
                    "custo_questor_acumulado": acumulado_linha_questor,
                    "custo_v2_ifrs": round(custo_v2, 2),
                    "custo_v2_ifrs_acumulado": round(acumulado_linha_v2, 2),
                    "custo_v1_legacy": round(custo_v1, 2),
                    "poc_mes": mapa_poc.get(k, 0.0),
                    "cub_mes": mapa_cub.get(k, 0.0),
                    "fluxo_recebido": mapa_receb.get(k, 0.0),
                    "credito_questor": mapa_creditos.get(k, 0.0)
                })'''

text = text.replace(old_logic, new_logic)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Temporal Matrix Backend to include Accumulated columns!")
