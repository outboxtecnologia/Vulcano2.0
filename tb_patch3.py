with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad1 = '''        custos_questor = [{"ano": int(r[0]), "mes": int(r[1]), "custo": float(r[2] or 0)} for r in cur_q.fetchall()]'''
good1 = '''        custos_questor_raw = cur_q.fetchall()
        custos_questor = []
        acum_global = 0.0
        for r in custos_questor_raw:
            custo_m = float(r[2] or 0)
            acum_global += custo_m
            custos_questor.append({"ano": int(r[0]), "mes": int(r[1]), "custo": custo_m, "custo_acumulado": acum_global})'''

bad2 = '''            dossie["amostra_unidades"].append({
                "unidade": u_desc,
                "data_venda": f"{u_dt_v_str[8:10]}/{u_mes_venda:02d}/{u_ano_venda}" if u_ano_venda != 9999 else "Não Vendida",
                "valor_unidade": u_tvenda,
                "grid_temporal": linhas_temporal
            })'''
good2 = '''            dossie["amostra_unidades"].append({
                "unidade": u_desc,
                "data_venda": f"{u_dt_v_str[8:10]}/{u_mes_venda:02d}/{u_ano_venda}" if u_ano_venda != 9999 else "Não Vendida",
                "valor_unidade": u_tvenda,
                "fracao_area": round(fracao * 100, 4),
                "grid_temporal": linhas_temporal
            })'''

text = text.replace(bad1, good1).replace(bad2, good2)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

