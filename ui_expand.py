with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inject State
state_inject = "const [ocultarSemMovimento, setOcultarSemMovimento] = useState(true);\n  const [dossierExpanded, setDossierExpanded] = useState(false);"
text = text.replace("const [ocultarSemMovimento, setOcultarSemMovimento] = useState(true);", state_inject)

# 2. Inject Button next to title (Let's find the Dossiê header)
import re
# Look for <h3 className="...">DOSSI...</h3>
header_match = re.search(r'(<h3[^>]*>DOSSI[^<]*<\/h3>)', text, re.IGNORECASE)
if header_match:
    h3_str = header_match.group(1)
    new_h3 = h3_str + '''\n<button onClick={() => setDossierExpanded(!dossierExpanded)} className="text-xs font-bold uppercase tracking-widest bg-[#222] border border-[#555] rounded px-3 py-1 cursor-pointer text-gray-300 hover:text-[#10b981] transition-colors">{dossierExpanded ? "Ocultar Extras" : "Expandir Colunas"}</button>'''
    text = text.replace(h3_str, new_h3)

# 3. Inject dynamic min-w
text = re.sub(r'min-w-\[660px\]', r'{dossierExpanded ? "min-w-[800px]" : "min-w-[400px]"}', text)

# 4. Modifying the Headers of Dossier
old_heads = '''<div className="grid grid-cols-7 gap-4 pt-2 mt-2 border-t border-dashed 
border-[#555] text-[10.5px] uppercase tracking-wider text-gray-400">
                                            <div className="text-white font-bold">Q. INCORRIDO</div>
                                            <div>V2 IFRS</div>
                                            <div>V1 LEGACY</div>
                                            <div>Q. CR%DITO</div>
                                            <div>FLUXO</div>
                                            <div>POC%</div>
                                            <div>CUB%</div>
                                          </div>'''

# Regex might fail because of newlines, so let's do a substring replace
import re
pattern = r'<div className="grid grid-cols-7[^>]+>.*?(?=</div\s*>\s*</div\s*>\s*</th)'
match = re.search(pattern, text, re.DOTALL)
if match:
    new_heads = '''<div className={grid  pt-2 mt-2 border-t border-dashed border-[#555] text-[10.5px] uppercase tracking-wider text-gray-400}>
                                            <div className="text-white font-bold">Q. MENSAL</div>
                                            <div className="text-white font-bold">Q. ACUMUL.</div>
                                            <div>V2 MENSAL</div>
                                            <div>V2 ACUMUL.</div>
                                            {dossierExpanded && (
                                              <>
                                                <div>V1 LEGACY</div>
                                                <div>Q. CRÉDITO</div>
                                                <div>FLUXO</div>
                                                <div>POC%</div>
                                                <div>CUB%</div>
                                              </>
                                            )}
                                          </div>'''
    text = text.replace(match.group(0), new_heads)


# 5. Modifying the Rows Data
pattern_row = r'<div className="grid grid-cols-7[^>]+>.*?</div>\s*</div>'
match_row = re.search(pattern_row, text, re.DOTALL)
if match_row:
    new_rows = '''<div className={grid  border-l border-[#333] pl-2}>
                                                <div className="text-white font-bold bg-[#222] px-1 rounded-sm">{(rowData.custo_questor_fracionado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                <div className="text-[#34c759] font-black">{(rowData.custo_questor_acumulado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                <div className="text-gray-300">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                <div className="text-[#a855f7] font-bold">{(rowData.custo_v2_ifrs_acumulado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                {dossierExpanded && (
                                                  <>
                                                    <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                    <div className="text-blue-400 font-bold bg-[#112] px-1 rounded-sm">{(rowData.credito_questor || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                    <div className="text-[#10b981] font-bold">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                    <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                                    <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                                  </>
                                                )}
                                             </div>'''
    text = text.replace(match_row.group(0), new_rows)


# Wait, need to fix the th/key min-w regex replace
text = text.replace('className="p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] min-w-[660px]"', 'className={p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] }')

# I also replaced the inner h3 div wrapper to justify-between, maybe I need to check it
# If the original h3 didn't have justify-between flex, the button will be under it. 
# It's inside a flex wrapper usually. Let's see.

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Complete Visual Expandable Metrics!")
