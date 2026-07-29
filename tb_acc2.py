with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''            acumulado_linha_questor = 0
            acumulado_linha_v2 = 0
            for c in meses_ordenados:'''

good = '''            acumulado_linha_questor = 0
            acumulado_linha_questor_credito = 0
            acumulado_linha_v2 = 0
            for c in meses_ordenados:'''

text = text.replace(bad, good)

bad2 = '''                custo_questor_fracionado = custo_orig * (fracao * 100) / 100
                acumulado_linha_questor += custo_questor_fracionado
                acumulado_linha_v2 += custo_v2'''

good2 = '''                custo_questor_fracionado = custo_orig * (fracao * 100) / 100
                acumulado_linha_questor += custo_questor_fracionado
                acumulado_linha_questor_credito += mapa_creditos.get(k, 0.0)
                acumulado_linha_v2 += custo_v2'''

text = text.replace(bad2, good2)

bad3 = '''                    "fluxo_recebido": mapa_receb.get(k, 0.0),
                    "credito_questor": mapa_creditos.get(k, 0.0)
                })'''

good3 = '''                    "fluxo_recebido": mapa_receb.get(k, 0.0),
                    "credito_questor": mapa_creditos.get(k, 0.0),
                    "credito_questor_acumulado": acumulado_linha_questor_credito
                })'''

text = text.replace(bad3, good3)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend Credits Accumulated Patched!")
