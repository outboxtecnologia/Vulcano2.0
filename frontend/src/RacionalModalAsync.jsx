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
  periodoFim,
  API_BASE
}) {
  const [questorHistory, setQuestorHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProporcionalMode, setIsProporcionalMode] = useState(false);

  // rawAptoNum: pega só o número APÓS 'APTO' no detalheApto (ex: 'APTO 202' → '202')
  // Isso garante que o padrão de busca seja 'APTO 202' e não '202112' (número de contrato+vaga)
  const rawAptoNum = useMemo(() => {
    if (!detalheApto) return '';
    const m = detalheApto.match(/APTO\s*(\d+)/i);
    return m ? m[1] : detalheApto.replace(/\D/g, '');
  }, [detalheApto]);

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

      // O cc fica em emp.cc (injetado pelo graph_logic_builder via receitas_meta)
      if (emp.cc) cc = emp.cc;

      // Conta de estoque: campo CONTAESTAND no formato '5639 - IMÓVEIS EM CONSTRUÇÃO'
      // Também pode estar como CONTAESTCON para obras concluídas
      const contas_ctb = emp.contas_contabeis || {};
      for (const key of ['CONTAESTAND', 'CONTAESTCON']) {
        const raw = contas_ctb[key];
        if (raw) {
          // Extrai só o número antes do hífen: '5639 - nome' → '5639'
          const num = String(raw).split(/[\s-]/)[0].trim();
          if (/^\d+$/.test(num)) qCsv.add(num);
        }
      }
    });

    const fracao = vendas.reduce((s, v) => s + (v.fracao || 0), 0);
    console.log('[RacionalModal] meta derivado:', { ccId: cc, contasCsv: Array.from(qCsv).join(','), fracaoTotal: fracao, rawAptoNum });
    return {
      todasVendas: vendas,
      ccId: cc,
      custoGlobalObra: custoGlobal,
      contasCsv: Array.from(qCsv).join(','),
      fracaoTotal: fracao,
      custoRealizadoIdeal: custoGlobal * fracao,
    };
  }, [dashboardMeta, filtroEmpNome, rawAptoNum]);


  // fracaoTotal como ref para acessar dentro do useEffect sem adicionar dep desnecessária
  const fracaoRef = React.useRef(fracaoTotal);
  React.useEffect(() => { fracaoRef.current = fracaoTotal; }, [fracaoTotal]);

  useEffect(() => {
    async function loadHistory() {
      setIsLoading(true);
      if (!contasCsv) {
        setQuestorHistory([]);
        setIsLoading(false);
        return;
      }

      try {
        const url = `${API_BASE}/api/questor/saldo-contas?empresa_id=${selectedEmpresa}&contas=${contasCsv}${ccId ? `&empreendimento_id=${ccId}` : ''}`;
        const res = await fetch(url);
        const json = await res.json();

        const targetUnit = detalheApto.trim();
        const numPattern = `APTO ${rawAptoNum}`;

        // Todos os lancamentos de todas as contas retornadas
        const allDetails = (json.data || []).flatMap(c => c.detalhes || []);

        // Filtra por data <= periodoFim (ex: '2025-04') para não mostrar meses futuros ao Kanban
        const corteYM = periodoFim || '';
        const allDetailsCortados = corteYM
          ? allDetails.filter(linha => {
              const ym = mesExtract(linha.data || '');
              return !ym || ym <= corteYM;
            })
          : allDetails;

        // 1. Tentativa: filtro direto por texto/override (lançamentos explicitamente da unidade)
        const filtered = allDetailsCortados.filter(linha => {
          if (linha.override_apto) return linha.override_apto === targetUnit;
          const h1 = (linha.historico || '').toUpperCase();
          const h2 = (linha.historico_base || '').toUpperCase();
          return h1.includes(numPattern) || h2.includes(numPattern);
        });

        if (filtered.length > 0) {
          // Modo direto: encontrou lancamentos explícitos para esta unidade
          setQuestorHistory(filtered);
          setIsProporcionalMode(false);
        } else if (allDetailsCortados.length > 0) {
          // Modo proporcional CC (POC/IFRS-15):
          const fracao = fracaoRef.current;
          if (fracao > 0) {
            const proporcional = allDetailsCortados.map(linha => ({
              ...linha,
              valor: (linha.valor || 0) * fracao,
              historico: linha.historico || '',
              _proporcional: true,
            }));
            setQuestorHistory(proporcional);
            setIsProporcionalMode(true);
          } else {
            setQuestorHistory([]);
            setIsProporcionalMode(false);
          }
        } else {
          setQuestorHistory([]);
          setIsProporcionalMode(false);
        }
      } catch (e) {
        console.error('Failed to load historical timeline', e);
        setQuestorHistory([]);
        setIsProporcionalMode(false);
      }
      setIsLoading(false);
    }
    if (detalheApto) loadHistory();
  }, [detalheApto, selectedEmpresa, contasCsv, ccId, API_BASE]);

  // ───── VU 2.0 HISTÓRICO (derivado do historico_poc × custo_global × fracaoTotal) ─────
  // REGRA DE HOOKS: este useMemo DEVE ficar antes do `if (!detalheApto) return null`
  // para garantir que o número de hooks seja sempre o mesmo em todo render.
  const mesesV2Hist = useMemo(() => {
    const corteYM = periodoFim || '';
    let pocList = [];
    let custoGlobal = 0;
    Object.entries(dashboardMeta || {}).forEach(([empKey, emp]) => {
      if (filtroEmpNome && !empKey.toLowerCase().includes(filtroEmpNome.toLowerCase()) &&
          !filtroEmpNome.toLowerCase().includes(empKey.toLowerCase())) return;
      if (emp.historico_poc && emp.historico_poc.length > 0) pocList = emp.historico_poc;
      if (emp.custo_gasto_vigente > custoGlobal) custoGlobal = emp.custo_gasto_vigente;
    });
    if (pocList.length === 0 || custoGlobal === 0 || fracaoTotal === 0) return [];

    const sorted = [...pocList]
      .sort((a, b) => (a.periodo || '').localeCompare(b.periodo || ''))
      .filter(p => !corteYM || (p.periodo || '') <= corteYM);

    const result = [];
    let acum = 0;
    sorted.forEach((entry, i) => {
      const pocAnterior = i === 0 ? 0 : (sorted[i - 1].poc || 0);
      const pocAtual = entry.poc || 0;
      const deltaPoc = Math.max(0, pocAtual - pocAnterior) / 100.0;
      const custoMes = deltaPoc * custoGlobal * fracaoTotal;
      acum += custoMes;
      result.push({
        mes: (entry.periodo || '').substring(0, 7),
        pocAtual,
        deltaPoc: deltaPoc * 100,
        custoMes,
        acumulado: acum,
      });
    });
    return result;
  }, [dashboardMeta, filtroEmpNome, fracaoTotal, periodoFim]);

  // ↓ Early return DEPOIS de todos os hooks — Rules of Hooks obrigam isso
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

  // (mesesV2Hist já computado acima, antes do early return)

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
                <span className="text-[9px] text-[#555]">{d.questor.length} lançamentos</span>
              </div>
              <div className="bg-[#0a1628] rounded-lg border border-[#1a3a66] p-3 flex flex-col gap-1">
                <span className="text-[8px] text-[#3b82f6]/70 uppercase tracking-widest">
                  {isProporcionalMode ? `Acumulado Questor (${(fracaoTotal*100).toFixed(4)}% da Obra)` : 'Acumulado Questor (Histórico)'}
                </span>
                {isLoading ? (
                  <span className="text-sm font-black text-[#3b82f6]/40 animate-pulse">...</span>
                ) : (
                  <span className="text-base font-black text-[#3b82f6]">
                    {mesesQ.length > 0
                      ? mesesQ[mesesQ.length - 1].acumulado.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})
                      : '—'}
                  </span>
                )}
                <span className="text-[9px] text-[#3b82f6]/40">
                  {isProporcionalMode ? '⅀ CC proporcional' : `${questorHistory.length} lnç históricos`}
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
            <div className="text-[9px] font-black uppercase tracking-widest text-[#3b82f6] mb-2 flex items-center gap-2">
              <span>◈</span>
              {isProporcionalMode
                ? `EVOLUÇÃO MENSAL — QUESTOR (MODO PROPORCIONAL CC · ${(fracaoTotal * 100).toFixed(4)}% da Obra)`
                : `EVOLUÇÃO MENSAL DE GASTOS — QUESTOR (Histórico${periodoFim ? ` até ${periodoFim}` : ' Completo'})`}
            </div>
            {isProporcionalMode && (
              <div className="mb-3 px-3 py-2 bg-[#1a1400] border border-[#ffb020]/30 rounded text-[9px] text-[#ffb020] leading-snug">
                ⚡ <strong>Modo Proporcional POC:</strong> Lançamentos LCTOGER de obra não contêm a unidade no histórico.
                Os valores exibidos = custo total do CC × <strong>{(fracaoTotal * 100).toFixed(4)}%</strong> (fração DIMOB VGV desta unidade).
                Use o Kanban para arrastar lançamentos e criar atribuição direta.
              </div>
            )}
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
            <div className="text-[9px] font-black uppercase tracking-widest text-[#a259ff] mb-3 flex items-center gap-2">
              <span>◈</span> EVOLUÇÃO MENSAL DE CUSTOS RECONHECIDOS — VU 2.0 (Motor POC Histórico{periodoFim ? ` até ${periodoFim}` : ''})
            </div>
            {mesesV2Hist.length === 0 ? (
              <p className="text-[#444] italic text-xs">Sem dados de POC histórico disponíveis para construir evolução VU 2.0.</p>
            ) : (
              <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full text-[10px] border-collapse">
                  <thead>
                    <tr className="border-b border-[#222]">
                      <th className="text-left px-3 py-2 text-[#555] font-black uppercase tracking-widest w-24">Mês</th>
                      <th className="text-right px-3 py-2 text-[#a259ff] font-black uppercase tracking-widest">POC (%)</th>
                      <th className="text-right px-3 py-2 text-[#a259ff]/70 font-black uppercase tracking-widest">ΔPOC</th>
                      <th className="text-right px-3 py-2 text-white font-black uppercase tracking-widest">Custo Reconhec.</th>
                      <th className="text-right px-3 py-2 text-[#ffb020] font-black uppercase tracking-widest">Acumulado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mesesV2Hist.map((m, i) => {
                      const maxAcum = Math.max(...mesesV2Hist.map(x => x.acumulado), 1);
                      const pct = (m.acumulado / maxAcum) * 100;
                      return (
                        <tr key={m.mes} className={`border-b border-[#111] ${i % 2 === 0 ? 'bg-[#130e18]' : 'bg-[#0e0e0e]'} hover:bg-[#1e1828] transition-colors`}>
                          <td className="px-3 py-2 font-bold text-white font-mono">{m.mes}</td>
                          <td className="px-3 py-2 text-right text-[#a259ff] font-bold font-mono">{m.pocAtual.toFixed(2)}%</td>
                          <td className="px-3 py-2 text-right text-[#a259ff]/70 font-mono">
                            {m.deltaPoc > 0 ? `+${m.deltaPoc.toFixed(2)}%` : '—'}
                          </td>
                          <td className={`px-3 py-2 text-right font-black font-mono ${m.custoMes > 0 ? 'text-[#22c55e]' : 'text-[#555]'}`}>
                            {m.custoMes > 0.01 ? m.custoMes.toLocaleString('pt-BR', {style:'currency', currency:'BRL'}) : '—'}
                          </td>
                          <td className="px-3 py-2 text-right font-black font-mono">
                            <div className="flex flex-col items-end gap-1">
                              <span className="text-[#ffb020]">{m.acumulado.toLocaleString('pt-BR', {style:'currency', currency:'BRL'})}</span>
                              <div className="w-full bg-[#1a1a1a] rounded-full h-1 max-w-[80px]">
                                <div className="bg-[#a259ff] h-1 rounded-full transition-all" style={{ width: `${Math.min(pct,100).toFixed(1)}%` }}/>
                              </div>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 border-[#333] bg-[#14101a]">
                      <td colSpan={2} className="px-3 py-2 font-black text-[#888] uppercase text-[9px] tracking-widest">ACUMULADO TARGET</td>
                      <td className="px-3 py-2 text-right font-black text-[#a259ff] font-mono"></td>
                      <td colSpan={2} className="px-3 py-2 text-right font-black text-[#ffb020] font-mono text-base">
                        {mesesV2Hist.length > 0 ? mesesV2Hist[mesesV2Hist.length-1].acumulado.toLocaleString('pt-BR', {style:'currency', currency:'BRL'}) : '—'}
                        <span className="ml-2 text-[9px] text-[#555] font-normal">{mesesV2Hist.length}</span>
                      </td>
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
