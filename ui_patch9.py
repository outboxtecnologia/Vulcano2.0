with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = text.replace('onClick={(e) => { e.stopPropagation(); setDetalheModal({ unidade: u.unidade, periodo: ${String(custo_m.mes).padStart(2, \\'0\\')} / , dados: rowData.questor_creditos_raw || [] })}', 'onClick={(e) => { e.stopPropagation(); setDetalheModal({ unidade: u.unidade, periodo: ${String(custo_m.mes).padStart(2, \\'0\\')} / , dados: rowData.questor_creditos_raw || [] }); }}')

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
