import re
import os

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. State root
code = re.sub(
    r'(const \[dadosPorMes, setDadosPorMes\] = useState\(\{\}\);)',
    r'\1\n  const [dashboardMeta, setDashboardMeta] = useState({});',
    code
)

# 2. Fetch parse
code = re.sub(
    r'(const jsonV = await respV\.json\(\);)',
    r'\1\n        if (jsonV?.dashboard_meta) setDashboardMeta(jsonV.dashboard_meta);',
    code
)

# 3. Component props
code = code.replace(
    'function TabelaMapaComparativa({ questor, vulcano1, vulcano2 }) {',
    'function TabelaMapaComparativa({ questor, vulcano1, vulcano2, dashboardMeta }) {'
)
code = code.replace(
    '<TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} />',
    '<TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} dashboardMeta={dashboardMeta} />'
)
code = code.replace(
    '<TabelaMapaComparativa questor={questorManual} vulcano1={virtualListFull} vulcano2={legadoListFull} />',
    '<TabelaMapaComparativa questor={questorManual} vulcano1={virtualListFull} vulcano2={legadoListFull} dashboardMeta={dashboardMeta} />'
)
code = code.replace(
    '<TabelaMapaComparativa questor={resumoDados.questor} vulcano1={resumoDados.vulcano1} vulcano2={resumoDados.vulcano2} />',
    '<TabelaMapaComparativa questor={resumoDados.questor} vulcano1={resumoDados.vulcano1} vulcano2={resumoDados.vulcano2} dashboardMeta={dashboardMeta} />'
)

# 4. State detalheApto (add to top of TabelaMapaComparativa)
code = re.sub(
    r'(const \[dragOverApto, setDragOverApto\] = useState\(null\);)',
    r'\1\n  const [detalheApto, setDetalheApto] = useState(null);',
    code
)

# 5. Kanban buttons
code = code.replace(
    '<span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span>\n                          <div className="flex items-center gap-2">',
    '<span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span>\n                          <div className="flex items-center gap-2">\n                             <button onClick={() => setDetalheApto(k)} className="px-1.5 py-0.5 rounded bg-[#1f1a11] border border-[#ff6b1a] text-[#ff6b1a] hover:bg-[#ff6b1a] hover:text-white text-[9px] font-mono tracking-widest transition-colors font-bold z-10 cursor-pointer">INFO</button>'
)

# 6. Tabular buttons
code = code.replace(
    '<div className={`flex items-center justify-between px-3 py-2 bg-[#151515] border-b border-[var(--v-border)] ${isDragOver ? \'bg-[#ff6b1a]/10\' : \'\'}`}>\n                    <span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span>\n                    \n                    <div className="flex items-center gap-4">',
    '<div className={`flex items-center justify-between px-3 py-2 bg-[#151515] border-b border-[var(--v-border)] ${isDragOver ? \'bg-[#ff6b1a]/10\' : \'\'}`}>\n                    <div className="flex items-center gap-3"><span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span> <button onClick={() => setDetalheApto(k)} className="px-1.5 py-0.5 rounded bg-[#1f1a11] border border-[#ff6b1a] text-[#ff6b1a] hover:bg-[#ff6b1a] hover:text-white text-[9px] font-mono tracking-widest transition-colors font-bold cursor-pointer">INFO</button></div>\n                    \n                    <div className="flex items-center gap-4">'
)


# 7. Tabular Color Fixes
code = code.replace(
    '<div className="text-[9px] font-black uppercase tracking-widest text-[#34c759] mb-1.5 px-1 text-center">Questor ({d.questor.length})</div>',
    '<div className="text-[9px] font-black uppercase tracking-widest text-[#3b82f6] mb-1.5 px-1 text-center">Questor ({d.questor.length})</div>'
)

code = code.replace(
    '<div className="text-[9px] font-black uppercase tracking-widest text-[#34c759] mb-1.5 px-1 text-center">VU 2.0 ({d.vulcano2.length})</div>',
    '<div className="text-[9px] font-black uppercase tracking-widest text-[#ff4500] mb-1.5 px-1 text-center">VU 2.0 ({d.vulcano2.length})</div>'
)

code = code.replace(
    '<div className="p-2 bg-[#34c759]/5">',
    '<div className="p-2 bg-[#ff4500]/5">'
)

code = code.replace(
    'className="flex flex-col border border-[#34c759]/30 bg-[#111] p-1.5 rounded hover:bg-[#1a1a1a]">',
    'className="flex flex-col border border-[#ff4500]/30 bg-[#111] p-1.5 rounded hover:bg-[#1a1a1a]">'
)

# 8. Modal root return replacement
modal_part = r'''
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
                <div className="bg-[#111] border border-[#333] w-[800px] max-w-[90vw] max-h-[85vh] flex flex-col rounded shadow-2xl overflow-hidden text-white font-mono text-xs" onClick={e => e.stopPropagation()}>
                    <div className="px-4 py-3 border-b border-[#333] flex justify-between items-center bg-[#1a1a1a]">
                       <h2 className="text-lg font-black tracking-widest uppercase text-[#ff6b1a]">DETALHES: {detalheApto.replace('_', ' ')}</h2>
                       <button onClick={() => setDetalheApto(null)} className="text-[#888] hover:text-white text-lg leading-none cursor-pointer">&times;</button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar flex flex-col gap-6">
                       
                       <div>
                          <h3 className="text-[10px] font-bold tracking-widest text-[#888] mb-2 uppercase border-b border-[#333] pb-1">Vendas Vinculadas (Comprador & Data)</h3>
                          {todasVendas.length === 0 ? <p className="text-[#555] italic">Nenhuma venda listada com este número na DIMOB.</p> :
                             <div className="flex flex-col gap-2">
                                {todasVendas.map((v, i) => (
                                   <div key={i} className="flex justify-between items-center p-2 bg-[#1a1a1a] rounded border border-[#222]">
                                      <div className="flex flex-col">
                                         <span className="font-bold text-[#ffb020] uppercase">{v.comprador}</span>
                                         <span className="text-[10px] text-[#888]">{v.unidade}</span>
                                      </div>
                                      <div className="flex flex-col text-right">
                                         <span className="text-white font-bold">{v.data_venda}</span>
                                         <span className="text-[10px] text-[var(--v-accent-2)]">VGV: {(v.vgv || 0).toLocaleString('pt-BR', {style: 'currency', currency:'BRL'})}</span>
                                      </div>
                                   </div>
                                ))}
                             </div>
                          }
                       </div>

                       <div className="grid grid-cols-2 gap-4">
                          <div>
                             <h3 className="text-[10px] font-bold tracking-widest text-[#3b82f6] mb-2 uppercase border-b border-[#333] pb-1">Evolução de Custos \u2014 QUESTOR ({d.questor.length})</h3>
                             {d.questor.length === 0 ? <p className="text-[#555] italic">Sem lançamentos.</p> : 
                               <div className="flex flex-col gap-1">
                                  {d.questor.map((q, i) => (
                                     <div key={i} className="flex flex-col p-1.5 bg-[#151a24] rounded border border-[#1a3a66]/50">
                                        <div className="flex justify-between items-center text-[10px]">
                                           <span className="text-white">{Number(q.valor).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})} {q.natureza}</span>
                                           <span className="text-[#888]">{q.data}</span>
                                        </div>
                                        <span className="text-[9px] text-[#3b82f6] truncate" title={q.historico}>{q.historico}</span>
                                     </div>
                                  ))}
                               </div>
                             }
                          </div>

                          <div>
                             <h3 className="text-[10px] font-bold tracking-widest text-[#ff4500] mb-2 uppercase border-b border-[#333] pb-1">Evolução de Custos \u2014 VU 2.0 ({d.vulcano2.length})</h3>
                             {d.vulcano2.length === 0 ? <p className="text-[#555] italic">Sem lançamentos.</p> : 
                               <div className="flex flex-col gap-1">
                                  {d.vulcano2.map((q, i) => (
                                     <div key={i} className="flex flex-col p-1.5 bg-[#26120e] rounded border border-[#662211]/50">
                                        <div className="flex justify-between items-center text-[10px]">
                                           <span className="text-white">{Number(q.valor).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})} {q.natureza}</span>
                                           <span className="text-[#888]">{q.data}</span>
                                        </div>
                                        <span className="text-[9px] text-[#ff4500] truncate" title={q.historico}>{q.historico}</span>
                                     </div>
                                  ))}
                               </div>
                             }
                          </div>
                       </div>
                    </div>
                </div>
             </div>
          );
      })()}
'''

code = code.replace(
    '  return contentToRender;\n}',
    '  return (\n    <>\n      {contentToRender}\n' + modal_part + '\n    </>\n  );\n}'
)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch executado com sucesso.")
