import React, { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';

const mesExtract = (dtStr) => {
  if (!dtStr) return '';
  const str = dtStr.substring(0, 10);
  if (str.includes('/')) {
    const p = str.split('/'); 
    if (p.length === 3) return `${p[2]}-${p[1]}`;
  }
  return str.substring(0, 7);
};

export default function RacionalModalAsync({
  detalheApto,
  setDetalheApto,
  mapAptos,
  dashboardMeta,
  filtroEmpNome,
  selectedEmpresa,
  API_BASE
}) {
  const [questorHistory, setQuestorHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const rawAptoNum = detalheApto ? detalheApto.replace(/\D/g, '') : '';

  // Bug #3 fix: memoizar derivações de dashboardMeta para deps estáveis no useEffect
  const { todasVendas, ccId, custoGlobalObra, contasCsv, fracaoTotal, custoRealizadoIdeal } = useMemo(() => {
    const vendas = [];
    let cc = null;
    let custoGlobal = 0;
    const qCsv = new Set();

    Object.entries(dashboardMeta || {}).forEach(([empNomeKey, emp]) => {
      if (filtroEmpNome && !empNomeKey.toLowerCase().includes(filtroEmpNome.toLowerCase()) &&
          !filtroEmpNome.toLowerCase().includes(empNomeKey.toLowerCase())) return;

      (emp.unidades || []).forEach(u => {
        if (u.unidade && rawAptoNum && u.unidade.includes(`APTO ${rawAptoNum}`)) {
          vendas.push(u);
        }
      });

      if (emp.custo_gasto_vigente > 0) custoGlobal = emp.custo_gasto_vigente;
      if (emp.contas_contabeis && emp.contas_contabeis.estoque_obras) {
        qCsv.add(emp.contas_contabeis.estoque_obras);
      }
      if (emp.cc) cc = emp.cc;
    });

    const fracao = vendas.reduce((s, v) => s + (v.fracao || 0), 0);
    return {
      todasVendas: vendas,
      ccId: cc,
      custoGlobalObra: custoGlobal,
      contasCsv: Array.from(qCsv).join(','),
      fracaoTotal: fracao,
      custoRealizadoIdeal: custoGlobal * fracao,
    };
  }, [dashboardMeta, filtroEmpNome, rawAptoNum]);

  useEffect(() => {
    async function loadHistory() {
      setIsLoading(true);

      // Extrai o número do apto e monta o texto de busca
      // detalheApto pode ser 'APTO_202' ou 'APTO 202' — normalize para 'APTO 202'
      const aptoText = `APTO ${rawAptoNum}`;
      // conta estoque: primeiro item do contasCsv
      const contaNum = contasCsv ? parseInt(contasCsv.split(',')[0], 10) : null;

      if (!contaNum || !rawAptoNum) {
        setQuestorHistory([]);
        setIsLoading(false);
        return;
      }

      try {
        // Novo endpoint: busca LCTOCTB com COMPLHIST LIKE '%APTO 202%'
        // Retorna apenas os lançamentos de realização de custo da unidade
        const url = `${API_BASE}/api/questor/historico-unidade?empresa_id=${selectedEmpresa}&conta=${contaNum}&apto_text=${encodeURIComponent(aptoText)}`;
        const res = await fetch(url);
        const json = await res.json();
        setQuestorHistory(json.data || []);
      } catch (e) {
        console.error('Failed to load historico-unidade', e);
        setQuestorHistory([]);
      }
      setIsLoading(false);
    }
    if (detalheApto) loadHistory();
  }, [detalheApto, selectedEmpresa, contasCsv, rawAptoNum, API_BASE]);

  if (!detalheApto) return null;

  const d = mapAptos[detalheApto] || { questor: [], vulcano1: [], vulcano2: [] };

  // Usa o questorHistory retornado pela API para montar o acumulado Fisico progressivo
  const porMesQ = {};
  questorHistory.forEach(q => {
    const mes = mesExtract(q.data);
    if (!porMesQ[mes]) porMesQ[mes] = { mes, debitos: 0, creditos: 0, lancamentos: [] };
    if (q.natureza === 'D') porMesQ[mes].debitos += (q.valor || 0);
    else porMesQ[mes].creditos += (q.valor || 0);
    porMesQ[mes].lancamentos.push(q);
  });
  const mesesQ = Object.values(porMesQ).sort((a, b) => a.mes.localeCompare(b.mes));
  let acumQ = 0;
  mesesQ.forEach(m => { m.liquido = m.debitos - m.creditos; acumQ += m.liquido; m.acumulado = acumQ; });

  // A Evolucao do Sistêmico VU 2.0. Injetamos um "Saldo Histórico" caso o array local mude!
  // No caso, deixaremos o array d.vulcano2 rodar do zero, MAS somaremos o custoTarget na cabeça dele se for necessário?
  // O usuário disse: "O acumulado dos apto está trazendo apenas o lançamento do mes"
  // Na verdade, VU 2.0 são virtuais e reconstruídos todo mês no Dashboard, o Racional Modal deles não passará de um "Espelho Sintético".
  const porMesV = {};
  (d.vulcano2 || []).forEach(q => {
    const mes = mesExtract(q.data);
    if (!porMesV[mes]) porMesV[mes] = { mes, debitos: 0, creditos: 0, lancamentos: [] };
    if (q.natureza === 'D') porMesV[mes].debitos += (q.valor || 0);
    else porMesV[mes].creditos += (q.valor || 0);
    porMesV[mes].lancamentos.push(q);
  });
  const mesesV2 = Object.values(porMesV).sort((a, b) => a.mes.localeCompare(b.mes));
  
  // A compensação! O Saldo inicial é todo o Custo Ideal subtraído do que aconteceu neste mês:
  const custoAtualMes = mesesV2.reduce((acc, m) => acc + m.debitos - m.creditos, 0);
  let acumV = custoRealizadoIdeal - custoAtualMes; 

  mesesV2.forEach(m => { m.liquido = m.debitos - m.creditos; acumV += m.liquido; m.acumulado = acumV; });

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

        <div className="flex-1 overflow-y-auto custom-scrollbar">

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

          <div className="px-5 py-4 border-b border-[#1a1a1a] flex flex-col gap-3">
            {/* Bug #2 fix: grid de 5 KPIs — adicionado Acumulado Questor Histórico */}
            <div className="grid grid-cols-5 gap-2">
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Custo Físico (Mês Kanban)</span>
                <span className="text-base font-black text-[#3b82f6]">
                  {(d.totalQuestor || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
                <span className="text-[9px] text-[#555]">{d.questor.len              <div className="bg-[#0a1628] rounded-lg border border-[#1a3a66] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#3b82f6]/70 uppercase tracking-widest">Acumulado Questor (Histórico)</span>
                {isLoading ? (
                  <span className="text-sm font-black text-[#3b82f6]/40 animate-pulse">...</span>
                ) : (
                  <span className="text-base font-black text-[#3b82f6]">
                    {mesesQ.length > 0
                      ? mesesQ[mesesQ.length - 1].acumulado.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})
                      : '—'}
                  </span>
                )}
                <span className="text-[9px] text-[#3b82f6]/40">{questorHistory.length} lnç históricos</span>
              </div>�ricos`}
                </span>
              </div>
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Custo Sistêmico (VU 2.0)</span>
                <span className="text-base font-black text-[#ff4500]">
                  {(d.totalVulcano2 || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
                <span className="text-[9px] text-[#555]">{d.vulcano2.length} lançamentos virtuais</span>
              </div>
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Divergência do Período</span>
                <span className={`text-base font-black ${Math.abs((d.totalQuestor||0) - (d.totalVulcano2||0)) < 0.5 ? 'text-[#22c55e]' : 'text-[#d32f2f]'}`}>
                  {((d.totalQuestor||0) - (d.totalVulcano2||0)).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
                <span className="text-[9px] text-[#555]">Q vs VU 2.0</span>
              </div>
              <div className="bg-[#161616] rounded-lg border border-[#222] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#555] uppercase tracking-widest">Representatividade</span>
                <span className="text-base font-black text-[#ffb020]">
                  {fracaoTotal > 0 ? `${(fracaoTotal * 100).toFixed(4)}%` : '-'}
                </span>
                <span className="text-[9px] text-[#555]">Fração DIMOB VGV</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-[#0e1208] rounded-lg border border-[#2ab212]/30 p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#2ab212] uppercase tracking-widest flex items-center gap-1">◈ Total Gasto da Obra (Até Período Pesquisado)</span>
                <span className="text-base font-black text-[#2ab212]">
                  {(custoGlobalObra || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                </span>
              </div>
              <div className="bg-[#12081a] rounded-lg border border-[#a22ab2]/30 p-3 flex flex-col gap-1 relative overflow-hidden">
                <span className="text-[8px] text-[#a22ab2] uppercase tracking-widest flex items-center gap-1">◈ Ponto de Equilíbrio / Custo Realizado Ideal da Unidade</span>
                <div className="flex items-end gap-3 z-10 relative">
                  <span className="text-base font-black text-[#a22ab2]">
                    {(custoRealizadoIdeal || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                  </span>
                  <span className="text-[10px] text-[#a22ab2]/70 mb-1 leading-none">{fracaoTotal > 0 ? `(${(fracaoTotal * 100).toFixed(2)}% da Obra)` : ''}</span>
                </div>
                <div className="absolute right-0 bottom-0 text-5xl font-black text-[#a22ab2]/5 -rotate-12 translate-x-2 translate-y-2 select-none pointer-events-none">TARGET</div>
              </div>
            </div>
          </div>

          <div className="px-5 py-4 border-b border-[#1a1a1a]">
            <div className="text-[9px] font-black uppercase tracking-widest text-[#3b82f6] mb-3 flex items-center gap-2">
              <span>◈</span> EVOLUÇÃO MENSAL DE GASTOS — QUESTOR (Histórico Completo LCTOCTB)
            </div>
            {isLoading ? (
              <div className="px-4 py-8 text-center text-[#555] animate-pulse uppercase tracking-widest text-[10px]">Baixando histórico LCTOGER...</div>
            ) : mesesQ.length === 0 ? (
              <p className="text-[#444] italic text-xs">Sem lançamentos Questor para esta unidade em nenhum ano.</p>
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
                      <td className="px-3 py-2 font-black text-[#888] uppercase text-[9px] tracking-widest">TOTAL GERAL</td>
                      <td className="px-3 py-2 text-right font-black text-[#3b82f6] font-mono">
                        {mesesQ.reduce((s,m) => s+m.debitos,0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-right font-black text-[#ff4500] font-mono">
                        {mesesQ.reduce((s,m) => s+m.creditos,0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'})}
                      </td>
                      <td colSpan={2} className="px-3 py-2 text-right font-black text-[#ffb020] font-mono text-base">
                        {mesesQ.length > 0 ? mesesQ[mesesQ.length-1].acumulado.toLocaleString('pt-BR', {style:'currency', currency:'BRL'}) : '—'}
                      </td>
                      <td className="px-3 py-2 text-right text-[#555] font-bold">{questorHistory.length}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>

          <div className="px-5 py-4">
            <div className="text-[9px] font-black uppercase tracking-widest text-[#ff4500] mb-3 flex items-center gap-2">
              <span>◈</span> EVOLUÇÃO MENSAL DE CUSTOS REALIZADOS — VU 2.0 (Espelho Estimado)
            </div>
            {mesesV2.length === 0 ? (
              <p className="text-[#444] italic text-xs">Sem lançamentos de realização VU 2.0 neste mês.</p>
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
                    {/* Linha inicial agregada do Saldo Histórico */}
                    {custoRealizadoIdeal - custoAtualMes > 0 && (
                       <tr className="border-b border-[#111] bg-[#090503] uppercase">
                          <td colSpan={4} className="px-3 py-2 font-black text-[#ff4500]/50 tracking-widest">Múltiplos Meses Anteriores</td>
                          <td className="px-3 py-2 text-right font-black text-[#ff4500]/70 font-mono text-xs">
                             {(custoRealizadoIdeal - custoAtualMes).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                          </td>
                          <td className="px-3 py-2 text-right text-[#555]">--</td>
                       </tr>
                    )}
                    {mesesV2.map((m, i) => {
                      const pct = mesesV2.length > 0 ? Math.abs(m.acumulado) / Math.max(...mesesV2.map(x => Math.abs(x.acumulado)), 1) * 100 : 0;
                      return (
                        <tr key={m.mes} className={`border-b border-[#2a1208] ${i % 2 === 0 ? 'bg-[#1a0c06]' : 'bg-[#140804]'} hover:bg-[#200f07] transition-colors`}>
                          <td className="px-3 py-2 font-bold text-white font-mono">{m.mes}</td>
                          <td className="px-3 py-2 text-right text-[#3b82f6] font-bold font-mono">
                            {m.debitos.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                          </td>
                          <td className="px-3 py-2 text-right text-[#ff4500] font-bold font-mono">
                            {m.creditos > 0 ? m.creditos.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'}) : '-'}
                          </td>
                          <td className={`px-3 py-2 text-right font-black font-mono ${m.liquido >= 0 ? 'text-[#ff4500]' : 'text-[#d32f2f]'}`}>
                            {m.liquido.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                          </td>
                          <td className="px-3 py-2 text-right font-black font-mono">
                            <div className="flex flex-col items-end gap-1">
                              <span className="text-[#ff4500]">
                                {m.acumulado.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                              </span>
                              <div className="w-full bg-[#1a1a1a] rounded-full h-1 max-w-[80px]">
                                <div className="bg-[#ff4500] h-1 rounded-full transition-all" style={{ width: `${Math.min(pct, 100).toFixed(1)}%` }}/>
                              </div>
                            </div>
                          </td>
                          <td className="px-3 py-2 text-right text-[#555]">{m.lancamentos.length}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 border-[#ff4500]/30 bg-[#140804]">
                      <td colSpan={4} className="px-3 py-2 font-black text-[#ff4500]/60 uppercase text-[9px] tracking-widest">ACUMULADO TARGET FINAL</td>
                      <td className="px-3 py-2 text-right font-black text-[#ff4500] font-mono text-base">
                        {mesesV2.length > 0 ? mesesV2[mesesV2.length-1].acumulado.toLocaleString('pt-BR', {style:'currency', currency:'BRL'}) : '—'}
                      </td>
                      <td className="px-3 py-2 text-right text-[#ff4500]/60 font-bold">{d.vulcano2.length}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
