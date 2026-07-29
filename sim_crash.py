import re

with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Find any unsafe toLocaleString
# Look for .toLocaleString without optional chaining or || 0

# Just to be safe, I will patch the specific Dossiê header
text = text.replace('{(agentState.dossie_heuristico.dossie.custo_orcado).toLocaleString(\'pt-BR\')}', '{(agentState.dossie_heuristico.dossie.custo_orcado || 0).toLocaleString(\'pt-BR\')}')

# What about custo_total_obra_mensal?
text = text.replace('{custo_m.custo.toLocaleString', '{(custo_m.custo || 0).toLocaleString')

# Let's search if any of my rows lack the || 0
rows = re.findall(r'\{([^}]+?\.toLocaleString\([^)]+\))\}', text)
for r in rows:
    if '|| 0' not in r and '?' not in r and 'fmt' not in r:
        print("Potentially unsafe:", r)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

