with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Row swap logic
bad_row = '''                                              <div className={grid  border-l border-[#333] pl-2}>
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
                                                  )}'''

good_row = '''                                              <div className={grid  border-l border-[#333] pl-2}>
                                                  <div className="text-white font-bold bg-[#222] px-1 rounded-sm">{(rowData.credito_questor || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                  <div className="text-[#34c759] font-black">{(rowData.credito_questor_acumulado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                  <div className="text-gray-300">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                  <div className="text-[#a855f7] font-bold">{(rowData.custo_v2_ifrs_acumulado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                  {dossierExpanded && (
                                                    <>
                                                      <div className="text-blue-400 font-bold bg-[#112] px-1 rounded-sm">{(rowData.custo_questor_fracionado || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                      <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                      <div className="text-[#10b981] font-bold">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                                      <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                                      <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                                    </>
                                                  )}'''

text = text.replace(bad_row, good_row)

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("UI Re-Patched explicitly via Python!")
