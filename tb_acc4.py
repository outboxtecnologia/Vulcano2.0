with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''          dossie = {
              "cc_empreendimento": cc_empreendimento,
              "empreendimento": nome_emp,
              "metragem_total": metragem_total,
              "custo_orcado": orcado,
              "custo_total_obra_mensal": custos_questor,
              "amostra_unidades": []
          }'''

good = '''          # Ensure custo_total_obra_mensal has ALL months (including CPV only months)
          all_chaves = set(f"{c['ano']}-{c['mes']}" for c in custos_questor)
          all_chaves.update(f"{c['ano']}-{c['mes']}" for c in creditos_questor_global)
          meses_glob = sorted([ {"ano": int(k.split('-')[0]), "mes": int(k.split('-')[1])} for k in all_chaves ], key=lambda x: (x["ano"], x["mes"]))
          custos_glob_expandido = []
          for mg in meses_glob:
              c_orig = next((cq["custo"] for cq in custos_questor if cq["ano"] == mg["ano"] and cq["mes"] == mg["mes"]), 0)
              custos_glob_expandido.append({"ano": mg["ano"], "mes": mg["mes"], "custo": c_orig})

          dossie = {
              "cc_empreendimento": cc_empreendimento,
              "empreendimento": nome_emp,
              "metragem_total": metragem_total,
              "custo_orcado": orcado,
              "custo_total_obra_mensal": custos_glob_expandido,
              "amostra_unidades": []
          }'''

text = text.replace(bad, good)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend Dossier Array Missing Months Patched!")
