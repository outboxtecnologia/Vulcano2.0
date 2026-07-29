with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

hdr_old = '''<div className="grid grid-cols-6 gap-2 pt-2 mt-2 border-t border-dashed border-[#555] text-[10.5px] uppercase tracking-wider text-gray-400">
                                          <div className="text-white font-bold">Q. INCORRIDO</div>
                                          <div>V2 IFRS</div>
                                          <div>V1 LEGACY</div>
                                          <div>FLUXO</div>
                                          <div>POC%</div>
                                          <div>CUB%</div>
                                        </div>'''
                                        
hdr_new = '''<div className="grid grid-cols-7 gap-2 pt-2 mt-2 border-t border-dashed border-[#555] text-[10.5px] uppercase tracking-wider text-gray-400">
                                          <div className="text-white font-bold">Q. INCORRIDO</div>
                                          <div>V2 IFRS</div>
                                          <div>V1 LEGACY</div>
                                          <div>Q. CRÉDITO</div>
                                          <div>FLUXO</div>
                                          <div>POC%</div>
                                          <div>CUB%</div>
                                        </div>'''

row_old = '''<div className="grid grid-cols-6 gap-2 border-l border-[#333] pl-2">
                                              <div className="text-white font-bold bg-[#222] px-1 rounded rounded-sm">{(rowData.custo_questor * u.fracao_obra / 100 || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-gray-300">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#10b981] font-bold">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                              <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                           </div>'''

row_new = '''<div className="grid grid-cols-7 gap-2 border-l border-[#333] pl-2">
                                              <div className="text-white font-bold bg-[#222] px-1 rounded rounded-sm">{(rowData.custo_questor * u.fracao_obra / 100 || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-gray-300">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-blue-400 font-bold bg-[#112] px-1 rounded-sm">{(rowData.credito_questor || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#10b981] font-bold">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                              <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                           </div>'''

text = text.replace(hdr_old, hdr_new)
text = text.replace(row_old, row_new)

# width adjustment to fit extra col
text = text.replace('min-w-[450px]', 'min-w-[530px]')

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Interface with Q. CREDITO")
