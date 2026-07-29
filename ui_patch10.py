with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# 1. Expand button next to Orçamento Base
bad1_str = '''                          <span className="text-xs text-[var(--v-text-muted)] font-mono uppercase tracking-widest">{agentState.dossie_heuristico.dossie.empreendimento} | Orçamento Base: R$ {(agentState.dossie_heuristico.dossie.custo_orcado || 0).toLocaleString('pt-BR')}</span>'''
good1_str = '''                          <div className="flex items-center gap-4">
                             <span className="text-xs text-[var(--v-text-muted)] font-mono uppercase tracking-widest">{agentState.dossie_heuristico.dossie.empreendimento} | Orçamento Base: R$ {(agentState.dossie_heuristico.dossie.custo_orcado || 0).toLocaleString('pt-BR')}</span>
                             <button onClick={() => setDossierExpanded(!dossierExpanded)} className="bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/30 text-blue-400 font-bold px-3 py-1 text-[10px] uppercase tracking-widest rounded transition-colors">
                                {dossierExpanded ? 'âœ– Reduzir Colunas' : 'âž• Expandir Detalhes (Custo Inc./Fluxo/POC/CUB)'}
                             </button>
                          </div>'''
text = text.replace(bad1_str, good1_str)

# 2. Add Fraction to the header
bad2_str = '                                        <span className="text-[10px] text-[var(--v-accent-4)] font-mono">D.Venda: {u.data_venda} | Venda R$ {u.valor_unidade?.toLocaleString(\\'pt-BR\\')}</span>'
good2_str = '                                        <span className="text-[10px] text-[var(--v-accent-4)] font-mono">D.Venda: {u.data_venda} | Venda R$ {u.valor_unidade?.toLocaleString(\\'pt-BR\\')} | Fração: {u.fracao_area?.toFixed(2)}%</span>'
text = text.replace(bad2_str, good2_str)

# 3. Add global accumulated cost
bad3_str = '''                                  <td className="p-3 font-mono font-bold text-white border-r border-[#333]">
                                    R$ {custo_m.custo?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                                  </td>'''
good3_str = '''                                  <td className="p-3 font-mono border-r border-[#333]">
                                    <div className="flex justify-between items-center w-full">
                                      <span className="font-bold text-white whitespace-nowrap">R$ {custo_m.custo?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                                      <span className="font-black text-[#ffcc00] text-[10px] whitespace-nowrap ml-3">R$ {custo_m.custo_acumulado?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                                    </div>
                                  </td>'''
text = text.replace(bad3_str, good3_str)

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

