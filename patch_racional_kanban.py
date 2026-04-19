"""
Patch: Adiciona botão RACIONAL no Kanban e enriquece o modal de detalhe do APTO
com: fração da unidade, evolução mensal de gastos, custos realizados acumulados.
Também move o modal para createPortal para funcionar no modo fullscreen.
"""
import re

path = 'frontend/src/AuditoriaERPView.jsx'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# 1) Adicionar botão RACIONAL no Column Head do Kanban (linha ~673)
#    Antes: só tem o badge DIVERGENTE/BATEU
#    Depois: badge + botão RACIONAL
# ─────────────────────────────────────────────────────────────────────────────
old_col_head = '''                        {/* Column Head */}
                        <div className={`px-3 py-2 flex items-center justify-between border-t-2 ${hasDiff ? 'border-t-[#d32f2f] bg-[#171111]' : 'border-t-[#22c55e] bg-[#111713]'}`}>
                           <div className="flex items-baseline gap-2">
                              <span className="text-[#555] text-[10px] font-mono tracking-widest">APTO</span>
                              <span className="text-white text-lg font-black leading-none">{k.replace(/\\D/g, '') || k}</span>
                           </div>
                           <div className={`px-1.5 py-0.5 rounded text-[9px] font-black tracking-widest leading-none ${hasDiff ? 'bg-[#d32f2f]/20 text-[#d32f2f]' : 'bg-[#22c55e]/20 text-[#22c55e]'}`}>
                              {hasDiff ? 'DIVERGENTE' : 'BATEU'}
                           </div>
                        </div>'''

new_col_head = '''                        {/* Column Head */}
                        <div className={`px-3 py-2 flex items-center justify-between border-t-2 ${hasDiff ? 'border-t-[#d32f2f] bg-[#171111]' : 'border-t-[#22c55e] bg-[#111713]'}`}>
                           <div className="flex items-baseline gap-2">
                              <span className="text-[#555] text-[10px] font-mono tracking-widest">APTO</span>
                              <span className="text-white text-lg font-black leading-none">{k.replace(/\\D/g, '') || k}</span>
                           </div>
                           <div className="flex items-center gap-1.5">
                              <button
                                onClick={(e) => { e.stopPropagation(); setDetalheApto(k); }}
                                className="px-2 py-0.5 bg-[#1a1412] border border-[#ff6b1a]/50 hover:border-[#ff6b1a] hover:bg-[#ff6b1a]/10 text-[#ff6b1a] text-[8px] font-black tracking-widest uppercase rounded transition-colors leading-none"
                                title="Ver racional da unidade"
                              >
                                RACIONAL
                              </button>
                              <div className={`px-1.5 py-0.5 rounded text-[9px] font-black tracking-widest leading-none ${hasDiff ? 'bg-[#d32f2f]/20 text-[#d32f2f]' : 'bg-[#22c55e]/20 text-[#22c55e]'}`}>
                                {hasDiff ? 'DIVERGENTE' : 'BATEU'}
                              </div>
                           </div>
                        </div>'''

if old_col_head in code:
    code = code.replace(old_col_head, new_col_head, 1)
    print('OK: botao RACIONAL adicionado no Column Head')
else:
    print('WARN: Column Head nao encontrado')

# ─────────────────────────────────────────────────────────────────────────────
# 2) Substituir o bloco completo do modal detalheApto por versão enriquecida
#    via createPortal (funciona em fullscreen e normal)
# ─────────────────────────────────────────────────────────────────────────────
old_modal_block = '''  if (isFullScreen) {
     return createPortal(<div style={{ zIndex: 99999, position: 'relative' }}>{contentToRender}</div>, document.body);
  }
  return (
    <>
      {contentToRender}

      {detalheApto && (() => {
          const rawAptoNum = detalheApto.replace(/\\D/g, '');
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
                             <h3 className="text-[10px] font-bold tracking-widest text-[#3b82f6] mb-2 uppercase border-b border-[#333] pb-1">Evolução de Custos \\u2014 QUESTOR ({d.questor.length})</h3>
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
                             <h3 className="text-[10px] font-bold tracking-widest text-[#ff4500] mb-2 uppercase border-b border-[#333] pb-1">Evolução de Custos \\u2014 VU 2.0 ({d.vulcano2.length})</h3>
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

    </>
  );
}
// FIN CARD COMPARATIVO //'''

new_modal_block = '''  // ── Modal RACIONAL do APTO ────────────────────────────────────────────────
  const racionalModal = detalheApto ? (() => {
    const rawAptoNum = detalheApto.replace(/\\D/g, '');
    const todasVendas = [];
    Object.values(dashboardMeta || {}).forEach(emp => {
      (emp.unidades || []).forEach(u => {
        if (u.unidade && rawAptoNum && u.unidade.includes(`APTO ${rawAptoNum}`)) {
          todasVendas.push(u);
        }
      });
    });
    const d = mapAptos[detalheApto] || { questor: [], vulcano1: [], vulcano2: [] };

    // Agrupa lançamentos Questor por mês (YYYY-MM) e acumula custo
    const porMesQ = {};
    d.questor.forEach(q => {
      const mes = (q.data || '').substring(0, 7); // YYYY-MM
      if (!porMesQ[mes]) porMesQ[mes] = { mes, debitos: 0, creditos: 0, lancamentos: [] };
      if (q.natureza === 'D') porMesQ[mes].debitos += (q.valor || 0);
      else porMesQ[mes].creditos += (q.valor || 0);
      porMesQ[mes].lancamentos.push(q);
    });
    const mesesQ = Object.values(porMesQ).sort((a, b) => a.mes.localeCompare(b.mes));
    let acumQ = 0;
    mesesQ.forEach(m => { m.liquido = m.debitos - m.creditos; acumQ += m.liquido; m.acumulado = acumQ; });

    // Fração média das vendas
    const fracaoTotal = todasVendas.reduce((s, v) => s + (v.fracao || 0), 0);
    const vgvTotal = todasVendas.reduce((s, v) => s + (v.vgv || 0), 0);
    const custoRealizado = d.totalQuestor !== undefined ? d.totalQuestor : (acumQ);

    return createPortal(
      <div
        className="fixed inset-0 flex items-center justify-center bg-black/85 backdrop-blur-sm"
        style={{ zIndex: 999999 }}
        onClick={() => setDetalheApto(null)}
      >
        <div
          className="bg-[#0e0e0e] border border-[#2a2a2a] w-[960px] max-w-[95vw] max-h-[90vh] flex flex-col rounded-lg shadow-2xl overflow-hidden text-white font-mono"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-5 py-3.5 border-b border-[#1e1e1e] flex items-center justify-between bg-[#141414] shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-1 h-8 bg-[#ff6b1a] rounded-full"/>
              <div>
                <div className="text-[10px] text-[#555] tracking-widest uppercase">Racional da Unidade</div>
                <h2 className="text-xl font-black tracking-widest uppercase text-white leading-none">
                  {detalheApto.replace('_', ' ')}
                </h2>
              </div>
            </div>
            <button onClick={() => setDetalheApto(null)} className="w-8 h-8 flex items-center justify-center bg-[#1a1a1a] hover:bg-white text-[#888] hover:text-black border border-[#333] rounded transition-colors text-lg leading-none">×</button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">

            {/* ── Seção 1: Dados da Venda ───────────────────────── */}
            <div className="px-5 py-4 border-b border-[#1a1a1a]">
              <div className="text-[9px] font-black uppercase tracking-widest text-[#ff6b1a] mb-3 flex items-center gap-2">
                <span className="text-[#ff6b1a]">◈</span> DADOS DA VENDA
              </div>
              {todasVendas.length === 0 ? (
                <p className="text-[#444] italic text-xs">Nenhuma venda vinculada a esta unidade na DIMOB.</p>
              ) : (
                <div className="flex flex-col gap-2">
                  {todasVendas.map((v, i) => (
                    <div key={i} className="grid grid-cols-4 gap-3 p-3 bg-[#161616] rounded-lg border border-[#222]">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-[#555] uppercase tracking-widest">Comprador</span>
                        <span className="text-[11px] font-bold text-[#ffb020] uppercase leading-tight">{v.comprador || '—'}</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-[#555] uppercase tracking-widest">Unidade</span>
                        <span className="text-[11px] font-bold text-white">{v.unidade || '—'}</span>
                        {v.fracao > 0 && (
                          <span className="text-[9px] text-[#888]">Fração: <span className="text-[#22c55e] font-bold">{(v.fracao * 100).toFixed(4)}%</span></span>
                        )}
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-[#555] uppercase tracking-widest">Data da Venda</span>
                        <span className="text-[13px] font-black text-white">{v.data_venda || '—'}</span>
                      </div>
                      <div className="flex flex-col gap-0.5 text-right">
                        <span className="text-[8px] text-[#555] uppercase tracking-widest">VGV</span>
                        <span className="text-[13px] font-black text-[#22c55e]">
                          {(v.vgv || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                        </span>
                        {v.percentual_pago > 0 && (
                          <span className="text-[9px] text-[#888]">{(v.percentual_pago * 100).toFixed(1)}% pago</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ── Seção 2: KPIs Resumo ──────────────────────────── */}
            <div className="px-5 py-4 border-b border-[#1a1a1a] grid grid-cols-4 gap-3">
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Custo Questor</span>
                <span className="text-base font-black text-[#3b82f6]">
                  {(d.totalQuestor || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
                <span className="text-[9px] text-[#555]">{d.questor.length} lançamentos</span>
              </div>
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Custo VU 2.0</span>
                <span className="text-base font-black text-[#ff4500]">
                  {(d.totalVulcano2 || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
                <span className="text-[9px] text-[#555]">{d.vulcano2.length} lançamentos</span>
              </div>
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Divergência</span>
                <span className={`text-base font-black ${Math.abs((d.totalQuestor||0) - (d.totalVulcano2||0)) < 0.5 ? 'text-[#22c55e]' : 'text-[#d32f2f]'}`}>
                  {((d.totalQuestor||0) - (d.totalVulcano2||0)).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
                <span className="text-[9px] text-[#555]">Q vs VU 2.0</span>
              </div>
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Fração Total</span>
                <span className="text-base font-black text-[#ffb020]">
                  {fracaoTotal > 0 ? `${(fracaoTotal * 100).toFixed(4)}%` : '—'}
                </span>
                <span className="text-[9px] text-[#555]">{todasVendas.length} unidade(s)</span>
              </div>
            </div>

            {/* ── Seção 3: Evolução Mensal de Gastos (Questor) ─── */}
            <div className="px-5 py-4 border-b border-[#1a1a1a]">
              <div className="text-[9px] font-black uppercase tracking-widest text-[#3b82f6] mb-3 flex items-center gap-2">
                <span>◈</span> EVOLUÇÃO MENSAL DE GASTOS — QUESTOR ({d.questor.length} lançamentos)
              </div>
              {mesesQ.length === 0 ? (
                <p className="text-[#444] italic text-xs">Sem lançamentos Questor para esta unidade.</p>
              ) : (
                <div className="overflow-x-auto custom-scrollbar">
                  <table className="w-full text-[10px] border-collapse">
                    <thead>
                      <tr className="border-b border-[#222]">
                        <th className="text-left px-3 py-2 text-[#555] font-black uppercase tracking-widest w-24">Mês</th>
                        <th className="text-right px-3 py-2 text-[#3b82f6] font-black uppercase tracking-widest">Débitos</th>
                        <th className="text-right px-3 py-2 text-[#ff4500] font-black uppercase tracking-widest">Créditos</th>
                        <th className="text-right px-3 py-2 text-white font-black uppercase tracking-widest">Líquido</th>
                        <th className="text-right px-3 py-2 text-[#ffb020] font-black uppercase tracking-widest">Acumulado</th>
                        <th className="text-right px-3 py-2 text-[#555] font-black uppercase tracking-widest">Lançtos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mesesQ.map((m, i) => {
                        const pct = mesesQ.length > 0 ? Math.abs(m.acumulado) / Math.max(...mesesQ.map(x => Math.abs(x.acumulado)), 1) * 100 : 0;
                        return (
                          <tr key={m.mes} className={`border-b border-[#111] ${i % 2 === 0 ? 'bg-[#131313]' : 'bg-[#0e0e0e]'} hover:bg-[#1e1e1e] transition-colors`}>
                            <td className="px-3 py-2 font-bold text-white font-mono">{m.mes}</td>
                            <td className="px-3 py-2 text-right text-[#3b82f6] font-bold font-mono">
                              {m.debitos.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                            </td>
                            <td className="px-3 py-2 text-right text-[#ff4500] font-bold font-mono">
                              {m.creditos > 0 ? m.creditos.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'}) : '—'}
                            </td>
                            <td className={`px-3 py-2 text-right font-black font-mono ${m.liquido >= 0 ? 'text-[#22c55e]' : 'text-[#d32f2f]'}`}>
                              {m.liquido.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                            </td>
                            <td className="px-3 py-2 text-right font-black font-mono">
                              <div className="flex flex-col items-end gap-1">
                                <span className="text-[#ffb020]">
                                  {m.acumulado.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                                </span>
                                <div className="w-full bg-[#1a1a1a] rounded-full h-1 max-w-[80px]">
                                  <div className="bg-[#ffb020] h-1 rounded-full transition-all" style={{ width: `${Math.min(pct, 100).toFixed(1)}%` }}/>
                                </div>
                              </div>
                            </td>
                            <td className="px-3 py-2 text-right text-[#555]">{m.lancamentos.length}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 border-[#333] bg-[#141414]">
                        <td className="px-3 py-2 font-black text-[#888] uppercase text-[9px] tracking-widest">TOTAL</td>
                        <td className="px-3 py-2 text-right font-black text-[#3b82f6] font-mono">
                          {mesesQ.reduce((s,m) => s+m.debitos,0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})}
                        </td>
                        <td className="px-3 py-2 text-right font-black text-[#ff4500] font-mono">
                          {mesesQ.reduce((s,m) => s+m.creditos,0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})}
                        </td>
                        <td colSpan={2} className="px-3 py-2 text-right font-black text-[#ffb020] font-mono text-sm">
                          {mesesQ.length > 0 ? mesesQ[mesesQ.length-1].acumulado.toLocaleString('pt-BR', {style:'currency', currency:'BRL'}) : '—'}
                        </td>
                        <td className="px-3 py-2 text-right text-[#555] font-bold">{d.questor.length}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>

            {/* ── Seção 4: Custos Realizados — VU 2.0 ─────────── */}
            <div className="px-5 py-4">
              <div className="text-[9px] font-black uppercase tracking-widest text-[#ff4500] mb-3 flex items-center gap-2">
                <span>◈</span> CUSTOS REALIZADOS — VU 2.0 ({d.vulcano2.length} lançamentos)
              </div>
              {d.vulcano2.length === 0 ? (
                <p className="text-[#444] italic text-xs">Sem lançamentos VU 2.0 para esta unidade.</p>
              ) : (
                <div className="flex flex-col gap-1.5 max-h-[240px] overflow-y-auto custom-scrollbar pr-1">
                  {d.vulcano2.map((q, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-[#160e0a] rounded border border-[#2a1208] hover:border-[#ff4500]/30 transition-colors">
                      <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                        <span className="text-[9px] text-[#ff4500]/70 truncate uppercase pr-2" title={q.historico || q.logica || ''}>
                          {q.historico || q.logica || '—'}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-[9px] text-[#555] font-mono">{q.data || '—'}</span>
                        <span className={`text-[11px] font-black font-mono ${q.natureza === 'D' ? 'text-[#22c55e]' : 'text-[#d32f2f]'}`}>
                          {q.natureza} {(q.valor || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </div>
      </div>,
      document.body
    );
  })() : null;

  if (isFullScreen) {
     return (
       <>
         {createPortal(<div style={{ zIndex: 99999, position: 'relative' }}>{contentToRender}</div>, document.body)}
         {racionalModal}
       </>
     );
  }
  return (
    <>
      {contentToRender}
      {racionalModal}
    </>
  );
}
// FIN CARD COMPARATIVO //'''

if old_modal_block in code:
    code = code.replace(old_modal_block, new_modal_block, 1)
    print('OK: modal RACIONAL substituido')
else:
    print('WARN: bloco do modal nao encontrado, verificar manualmente')

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print('Arquivo salvo.')
