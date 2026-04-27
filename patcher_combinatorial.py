import os
import re

with open('backend/core/services/heuristic_optimizer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace 1.1 loop
# From: qs_restantes = sorted(qs_livres, key=lambda x: x["valor"], reverse=True)
# Until the end of 1.2 loop just before "# 2. Rescaldo Fuzzy"

start_idx = text.find('            # 1.1 Combinatória Isolada 1:N (Dentro do Repositório)')
end_idx = text.find('        # 2. Rescaldo Fuzzy Clássico')

replacement = '''            # 1.1 Combinatória Isolada 1:N (Dentro do Repositório)
            CombinatorialAnalyzer.run_1_to_n(c_id, qs_livres, cv["v"], _adicionar_match, _verificar_anomalia_cub)

            # 1.2 Combinatória Isolada N:1 (Dentro do Repositório)
            CombinatorialAnalyzer.run_n_to_1(c_id, vs_livres, cv["q"], _adicionar_match, _verificar_anomalia_cub)

'''
new_text = text[:start_idx] + replacement + text[end_idx:]

with open('backend/core/services/heuristic_optimizer.py', 'w', encoding='utf-8') as f:
    f.write(new_text)

