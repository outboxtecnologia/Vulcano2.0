with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''          all_chaves = set(f"{c['ano']}-{c['mes']}" for c in custos_questor)
          all_chaves.update(f"{c['ano']}-{c['mes']}" for c in creditos_questor_global)'''

good = '''          all_chaves = set(f"{c['ano']}-{c['mes']}" for c in custos_questor)
          all_chaves.update(f"{c['ano']}-{c['mes']}" for c in creditos_questor_detalhes)'''

text = text.replace(bad, good)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend Dossier Months Keys Inclusion Patched!")
