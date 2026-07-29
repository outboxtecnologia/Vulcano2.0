with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# 1. Update text sizing in table and add QUESTOR FRAC column
# Look for the map iterations inside the TH and TD strings
text = text.replace('text-[10px]', 'text-xs')
text = text.replace('text-[8px]', 'text-[10px]')
text = text.replace('text-[11px]', 'text-sm')
text = text.replace('text-[9px]', 'text-xs')

# In the Headers:
old_header_grid = '''<div className="grid grid-cols-5 gap-1 pt-2 mt-2 border-t border-[#333] text-[10px] uppercase tracking-widest text-[#888]">
                                          <div>V2 IFRS</div>
                                          <div>V1 LEGACY</div>
                                          <div>FLUXO</div>
                                          <div>POC%</div>
                                          <div>CUB%</div>
                                        </div>'''
new_header_grid = '''<div className="grid grid-cols-6 gap-2 pt-2 mt-2 border-t border-dashed border-[#555] text-[10.5px] uppercase tracking-wider text-gray-400">
                                          <div className="text-white font-bold">Q. INCORRIDO</div>
                                          <div>V2 IFRS</div>
                                          <div>V1 LEGACY</div>
                                          <div>FLUXO</div>
                                          <div>POC%</div>
                                          <div>CUB%</div>
                                        </div>'''
text = text.replace(old_header_grid.replace('text-[10px]', 'text-[8px]'), new_header_grid) # fallback if earlier replacement missed
text = text.replace(old_header_grid, new_header_grid)

# In the Rows
old_row_grid = '''<div className="grid grid-cols-5 gap-1">
                                              <div className="text-white">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#10b981]">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                              <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                           </div>'''
                                           
new_row_grid = '''<div className="grid grid-cols-6 gap-2 border-l border-[#333] pl-2">
                                              <div className="text-white font-bold bg-[#222] px-1 rounded rounded-sm">{(rowData.custo_questor * u.fracao_obra / 100 || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-gray-300">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#10b981] font-bold">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                              <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                           </div>'''

text = text.replace(old_row_grid, new_row_grid)

# Also fix the TH base text classes "font-black text-xs"
# Make the table more robust visually
text = text.replace('min-w-[300px]', 'min-w-[450px]') # Give more width for 6 cols

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Table sizes and added Questor Incorrido column inside.")
