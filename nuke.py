import re

with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Completely nuke ALL occurrences of TabelaMapaComparativa
# It starts at 'function TabelaMapaComparativa'
# It ends right before 'function TabelaMapaAgrupada'

text = re.sub(r'// CARD COMPARATIVO //.*?// FIN CARD COMPARATIVO //\n*', '', text, flags=re.DOTALL)
text = re.sub(r'(?:\n*)function TabelaMapaComparativa.*?\}\n*(?=function TabelaMapaAgrupada)', '\n\n', text, flags=re.DOTALL)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
