with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Swap headers
head_pattern = r'<div>V1 LEGACY</div>\s*<div>Q\. CR[^<]+</div>'
new_head = "<div>Q. INCORRIDO</div>\n                                                  <div>V1 LEGACY</div>"
text = re.sub(head_pattern, new_head, text)

# Swap rows
# Q. Mensal (was custo_questor_fracionado) -> credito_questor
text = text.replace('{(rowData.custo_questor_fracionado || 0).toLocaleString(\'pt-BR\'', '{(rowData.credito_questor || 0).toLocaleString(\'pt-BR\'')

# Q. Acumulado (was custo_questor_acumulado) -> credito_questor_acumulado
text = text.replace('{(rowData.custo_questor_acumulado || 0).toLocaleString(\'pt-BR\'', '{(rowData.credito_questor_acumulado || 0).toLocaleString(\'pt-BR\'')

# Hidden block replacing credito_questor -> custo_questor_fracionado
# Wait, because I already replaced custo_questor_fracionado, doing it this way would collision!
