with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''  const [dossierExpanded, setDossierExpanded] = useState(false);'''

good = '''  const [dossierExpanded, setDossierExpanded] = useState(false);
  const [detalheModal, setDetalheModal] = useState(null);'''

text = text.replace(bad, good)

# Also make the cell clickable!
bad2 = '''                                                <div className="text-white font-bold bg-[#222] px-1 rounded-sm">{(rowData.credito_questor || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>'''

good2 = '''                                                <div className="text-white font-bold bg-[#222] px-1 rounded-sm cursor-pointer hover:bg-blue-900 border border-transparent hover:border-blue-400 transition-colors" onClick={() => setDetalheModal({ unidade: u.unidade, periodo: ${custo_m.mes.toString().padStart(2, '0')} / , dados: rowData.questor_creditos_raw || [] })} title="Clique para ver extrato detalhado do Razão">{(rowData.credito_questor || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>'''

text = text.replace(bad2, good2)

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

