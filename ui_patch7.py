with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Fix syntax error inside onClick
# It looks like: onClick={() => setDetalheModal({ unidade: u.unidade, periodo:  / , dados: 
text = re.sub(
    r'periodo:\s*\\s*/\s*,',
    r'periodo: ${String(custo_m.mes).padStart(2, "0")} / ,',
    text
)

text = text.replace('{d.ano}-{str(d.mes).padStart(2,', '{d.ano}-{String(d.mes).padStart(2,')

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
