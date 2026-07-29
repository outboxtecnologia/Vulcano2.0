with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

table_jsx = '''
                    {/* [INICIO] Malha Analítica Heurística (Tabela Python) */}
                    {status === 'PAUSED' && agentState?.dossie_heuristico?.dossie && (
                      <div className="bg-[var(--v-bg)] border border-[var(--v-border)] rounded overflow-hidden flex flex-col mt-2 
animate-in slide-in-from-bottom-6 duration-500">
                        <div className="bg-[var(--v-deep)] px-4 py-3 border-b border-[var(--v-border)] flex justify-between items-center">
                          <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-[#10b981] flex items-center gap-2">
                             Dossiê Heurístico Temporal
                          </h3>
                          <span className="text-[9px] text-[var(--v-text-muted)] font-mono uppercase tracking-widest">{agentState.dossie_heuristico.dossie.empreendimento} | Orçamento Base: R$ {(agentState.dossie_heuristico.dossie.custo_orcado).toLocaleString('pt-BR')}</span>
                        </div>
                        
                        <div className="overflow-x-auto">
                          <table className="w-full text-left border-collapse text-[10px]">
                            <thead>
                              <tr>
                                <th className="p-3 border-b border-r border-[#333] font-black text-[var(--v-text-muted)] uppercase tracking-widest bg-[#111] sticky left-0 z-10 w-24">Período</th>
                                <th className="p-3 border-b border-r border-[#333] font-black text-white uppercase tracking-widest bg-[#111] min-w-[120px]">Obra (Questor LCTOGER)</th>
                                {agentState.dossie_heuristico.dossie.amostra_unidades.map((u, i) => (
                                  <th key={i} className="p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] min-w-[300px]">
                                     <div className="flex flex-col gap-1">
                                        <span className="text-[#10b981] uppercase font-black text-[11px]">{u.unidade}</span>
                                        <span className="text-[8px] text-[var(--v-accent-4)] font-mono">D.Venda: {u.data_venda} | Venda R$ {u.valor_unidade?.toLocaleString('pt-BR')}</span>
                                        <div className="grid grid-cols-5 gap-1 pt-2 mt-2 border-t border-[#333] text-[8px] uppercase tracking-widest text-[#888]">
                                          <div>V2 IFRS</div>
                                          <div>V1 LEGACY</div>
                                          <div>FLUXO</div>
                                          <div>POC%</div>
                                          <div>CUB%</div>
                                        </div>
                                     </div>
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {agentState.dossie_heuristico.dossie.custo_total_obra_mensal.map((custo_m, idx) => (
                                <tr key={idx} className="hover:bg-[#1a1a1a] transition-colors border-b border-[#222]">
                                  <td className="p-3 font-mono font-bold text-[var(--v-text-faint)] bg-[#111] sticky left-0 border-r border-[#333] whitespace-nowrap">
                                    {String(custo_m.mes).padStart(2, '0')} / {custo_m.ano}
                                  </td>
                                  <td className="p-3 font-mono font-bold text-white border-r border-[#333]">
                                    R$ {custo_m.custo?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                                  </td>
                                  {agentState.dossie_heuristico.dossie.amostra_unidades.map((u, i) => {
                                      const rowData = u.grid_temporal?.find(g => g.ano === custo_m.ano && g.mes === custo_m.mes) || {};
                                      return (
                                        <td key={i} className="p-3 font-mono text-[10px] border-r border-[#333]">
                                           <div className="grid grid-cols-5 gap-1">
                                              <div className="text-white">{(rowData.custo_v2_ifrs || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[var(--v-text-faint)]">{(rowData.custo_v1_legacy || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#10b981]">{(rowData.fluxo_recebido || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                                              <div className="text-[#a855f7]">{(rowData.poc_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                              <div className="text-[#facc15]">{(rowData.cub_mes || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}%</div>
                                           </div>
                                        </td>
                                      )
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    {/* [FIM] Malha Analítica */}
'''

search_str = "{(!agentState.sugestao_correcao || Object.keys(agentState.sugestao_correcao).length === 0) && status === 'PAUSED' && ("
rpl = search_str + "\n" + "                      " + "<>"

text = text.replace(search_str, table_jsx + "\n\n                    " + search_str)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Injected React TabelaDossie successfully into UI")
