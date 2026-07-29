with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"fluxo_recebido": mapa_receb.get(k, 0.0)\n                })', '"fluxo_recebido": mapa_receb.get(k, 0.0),\n                    "credito_questor": mapa_creditos.get(k, 0.0)\n                })')

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Added missing credito_questor property back into grid object!")
