with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''                                                    <div className="text-blue-400 font-bold bg-[#112] px-1 rounded-sm">{(rowData.custo_questor_fracionado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                    <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                    <div className="text-blue-400 font-bold bg-[#112] px-1 rounded-sm">{(rowData.custo_questor_fracionado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>'''

good = '''                                                    <div className="text-blue-400 font-bold bg-[#112] px-1 rounded-sm">{(rowData.custo_questor_fracionado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                    <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>'''

text = text.replace(bad, good)

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

