import sys

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. State for fontesFaltantes and detalheApto
if 'const [detalheApto, setDetalheApto] = useState(null);' not in code:
    code = code.replace(
        "const [dragOverApto, setDragOverApto] = useState(null);",
        "const [dragOverApto, setDragOverApto] = useState(null);\n  const [detalheApto, setDetalheApto] = useState(null);\n  const [fontesFaltantes, setFontesFaltantes] = useState(false);"
    )

# 2. Filter logic for fontesFaltantes
if 'if (fontesFaltantes' not in code:
    code = code.replace(
        "if (soDivergentes && !hasDiff) return false;",
        "if (soDivergentes && !hasDiff) return false;\n      if (fontesFaltantes && d.questor.length > 0 && d.vulcano2.length > 0) return false;"
    )

# 3. Checkbox in Kanban
if 'SÓ DIVERGENTES' in code and 'FONTES FALTANTES' not in code:
    code = code.replace(
        '''                       SÓ DIVERGENTES\n                    </label>''',
        '''                       SÓ DIVERGENTES\n                    </label>\n                    <label className="flex items-center gap-2 cursor-pointer text-[#888] text-[10px] font-mono uppercase tracking-widest hover:text-white transition-colors">\n                       <input type="checkbox" checked={fontesFaltantes} onChange={e => setFontesFaltantes(e.target.checked)} className="accent-[#ff6b1a] w-3 h-3" />\n                       FONTES FALTANTES\n                    </label>'''
    )

# 4. INFO button in Kanban
kanban_span = '<span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span>'
kanban_replacement = '<div className="flex items-center gap-3"><span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span> <button onClick={() => setDetalheApto(k)} className="px-1.5 py-0.5 rounded bg-[#1f1a11] border border-[#ff6b1a] text-[#ff6b1a] hover:bg-[#ff6b1a] hover:text-white text-[9px] font-mono tracking-widest transition-colors font-bold z-10 cursor-pointer">INFO</button></div>'

code = code.replace(kanban_span, kanban_replacement)

# 5. Modal Block
modal_block = """
      {detalheApto && (() => {
          const rawAptoNum = detalheApto.replace(/\D/g, '');
          const todasVendas = [];
          Object.values(dashboardMeta || {}).forEach(emp => {
              (emp.unidades || []).forEach(u => {
                  if(u.unidade && rawAptoNum && u.unidade.includes(`APTO ${rawAptoNum}`)) {
                     todasVendas.push(u);
                  }
              });
          });
          const d = mapAptos[detalheApto] || { questor: [], vulcano2: [] };

          return (
             <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={() => setDetalheApto(null)}>
                <div className="bg-[#0a0a0a] border border-[#333] shadow-2xl rounded-lg p-6 max-w-4xl w-full max-h-[90vh] flex flex-col font-mono" onClick={e => e.stopPropagation()}>
                    <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#222]">
                        <h2 className="text-xl font-black text-white tracking-widest uppercase">DETALHES DA UNIDADE <span className="text-[#ff6b1a]">{detalheApto}</span></h2>
                        <button onClick={() => setDetalheApto(null)} className="text-[#888] hover:text-white font-bold text-xl leading-none">&times;</button>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-8 overflow-y-auto custom-scrollbar flex-1 pr-2">
                       {/* Left Column: Vendas */}
                       <div>
                          <h3 className="text-[10px] font-bold tracking-widest text-[#888] mb-4 uppercase border-b border-[#333] pb-1">Vendas Vinculadas (Comprador & Data)</h3>
                          {todasVendas.length === 0 ? <p className="text-[#555] italic text-xs">Nenhuma venda listada com este número na DIMOB.</p> :
                             <div className="flex flex-col gap-2">
                                {todasVendas.map((v, i) => (
                                   <div key={i} className="flex flex-col gap-1 p-3 bg-[#111] border border-[#222] rounded shadow-inner">
                                      <span className="text-xs font-bold text-[#ffae42] uppercase tracking-widest">{v.comprador || "DESCONHECIDO"}</span>
                                      <span className="text-[10px] text-[var(--v-text-muted)] group-hover:text-white transition-colors">Venda: {v.data_venda || "-"}</span>
                                      <span className="text-[10px] text-[var(--v-accent-2)]">VGV: {(v.vgv || 0).toLocaleString('pt-BR', {style: 'currency', currency:'BRL'})}</span>
                                   </div>
                                ))}
                             </div>
                          }
                       </div>
                       
                       {/* Right Column: Custos */}
                       <div className="flex flex-col gap-6">
                           <div>
                             <h3 className="text-[10px] font-bold tracking-widest text-[#3b82f6] mb-2 uppercase border-b border-[#333] pb-1">Evolução de Custos — QUESTOR ({d.questor.length})</h3>
                             {d.questor.length === 0 ? <p className="text-[#555] italic text-xs">Sem lançamentos.</p> :
                                <div className="flex flex-col gap-1.5 max-h-[30vh] overflow-y-auto custom-scrollbar pr-1">
                                   {d.questor.map((q, i) => (
                                      <div key={i} className="flex justify-between items-center text-[10px] bg-[#121c2d] border border-[#1a3a66] p-1.5 rounded">
                                         <span className="text-white">{Number(q.valor).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})} {q.natureza}</span>
                                         <span className="text-[#888]">{q.data}</span>
                                      </div>
                                   ))}
                                </div>
                             }
                           </div>
                           
                           <div>
                             <h3 className="text-[10px] font-bold tracking-widest text-[#ff4500] mb-2 uppercase border-b border-[#333] pb-1">Evolução de Custos — VU 2.0 ({d.vulcano2.length})</h3>
                             {d.vulcano2.length === 0 ? <p className="text-[#555] italic text-xs">Sem lançamentos.</p> :
                                <div className="flex flex-col gap-1.5 max-h-[30vh] overflow-y-auto custom-scrollbar pr-1">
                                   {d.vulcano2.map((q, i) => (
                                      <div key={i} className="flex justify-between items-center text-[10px] bg-[#26120e] border border-[#662211] p-1.5 rounded">
                                         <span className="text-white">{Number(q.valor).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})} {q.natureza}</span>
                                         <span className="text-[#888]">{q.data}</span>
                                      </div>
                                   ))}
                                </div>
                             }
                           </div>
                       </div>
                    </div>
                </div>
             </div>
          )
      })()}
"""

if "Vendas Vinculadas" not in code:
    code = code.replace(
        "  return (\n    <>\n      {contentToRender}\n    </>\n  );\n}",
        "  return (\n    <>\n      {contentToRender}\n" + modal_block + "\n    </>\n  );\n}"
    )

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied.")
