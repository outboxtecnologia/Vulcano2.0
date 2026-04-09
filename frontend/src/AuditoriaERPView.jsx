import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle,
  RefreshCw, Building2, ChevronDown, ChevronUp, ArrowRight
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const fmt = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 }).format(v || 0);
const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// ── helpers ──────────────────────────────────────────────────────────────────
function gerarCompetencias(de, ate) {
  const res = [];
  let [y, m] = de.split('-').map(Number);
  const [ey, em] = ate.split('-').map(Number);
  while (y < ey || (y === ey && m <= em)) {
    res.push(`${y}-${String(m).padStart(2, '0')}`);
    m++; if (m > 12) { m = 1; y++; }
  }
  return res;
}
const labelMes = (comp) => {
  const [y, m] = comp.split('-').map(Number);
  return `${MESES_ABREV[m - 1]}/${String(y).slice(2)}`;
};

const abs = (v) => Math.abs(v || 0);
const DIVERGENCIA_CORTE = 0.5; // abaixo disso, considera ok

// Semáforo de status
function Status({ diff }) {
  if (abs(diff) < DIVERGENCIA_CORTE) return <CheckCircle2 size={14} className="text-[#34c759] shrink-0"/>;
  if (abs(diff) < 5000)             return <AlertTriangle size={14} className="text-[#ffcc00] shrink-0"/>;
  return <XCircle size={14} className="text-[#ff4d00] shrink-0"/>;
}

// Cor da divergência
function corDiff(diff) {
  if (abs(diff) < DIVERGENCIA_CORTE) return '#34c759';
  if (abs(diff) < 5000)             return '#ffcc00';
  return '#ff4d00';
}

// ── Linha de conta na tabela de confronto ────────────────────────────────────
function ContaConfronto({ contaId, contaNome, competencias, dadosPorMes }) {
  const [open, setOpen] = useState(false);
  const [racionalOpen, setRacionalOpen] = useState(false);

  // Para cada competência: soma fisico e virtual desta conta
  const porComp = competencias.map(comp => {
    const lista = dadosPorMes[comp] || {};
    const fisico   = lista.fisico?.find(r => String(r.conta) === String(contaId));
    const virtual  = lista.virtual?.find(r => String(r.conta) === String(contaId));
    return {
      comp,
      temFisico:    !!fisico,
      movFisico:    fisico ? ((fisico.saldo_final || 0) - (fisico.saldo_anterior || 0)) : 0,
      saldoFisico:  fisico?.saldo_final         || 0,
      movVirtual:   virtual?.movimento_liquido  || 0,
      saldoVirtual: virtual?.saldo_final        || 0,
      diffMov:      (virtual?.movimento_liquido || 0) - (fisico ? ((fisico.saldo_final || 0) - (fisico.saldo_anterior || 0)) : 0),
      diffSaldo:    (virtual?.saldo_final       || 0) - (fisico?.saldo_final       || 0),
      detalhesFisico:   fisico?.detalhes  || [],
      detalhesVirtual:  virtual?.detalhes || [],
    };
  });

  // Totais do período
  const totalMovFisico   = porComp.reduce((s, c) => s + c.movFisico, 0);
  const totalMovVirtual  = porComp.reduce((s, c) => s + c.movVirtual, 0);
  const totalDiffMov     = totalMovVirtual - totalMovFisico;
  // Saldo final = último mês
  const ultimo           = porComp[porComp.length - 1] || {};
  const totalDiffSaldo   = ultimo.diffSaldo || 0;

  const temDivergencia   = abs(totalDiffMov) >= DIVERGENCIA_CORTE || abs(totalDiffSaldo) >= DIVERGENCIA_CORTE;

  // Só mostra contas que têm qualquer movimento em algum lado
  const temQualquerDado = porComp.some(c => abs(c.movFisico) > 0 || abs(c.movVirtual) > 0 || c.saldoFisico || c.saldoVirtual);
  if (!temQualquerDado) return null;

  // Todos os lançamentos virtuais com logica (para o Racional)
  const todosVirtualLogica = porComp.flatMap(({ comp, detalhesVirtual }) =>
    detalhesVirtual.filter(d => d.logica).map(d => ({ ...d, comp }))
  );

  return (
    <>
      <tr
        className={`border-b transition-colors cursor-pointer ${temDivergencia ? 'border-[#ff4d00]/10 hover:bg-[#1a0800]' : 'border-[#1a1a1a] hover:bg-[#141414]'}`}
        onClick={() => setOpen(o => !o)}
      >
        {/* Conta + nome */}
        <td className="px-3 py-2.5 sticky left-0 z-10 bg-[#0d0d0d] min-w-[220px]">
          <div className="flex items-center gap-2">
            <Status diff={totalDiffSaldo}/>
            <span className="font-mono text-[13px] font-black text-[#ff4d00] shrink-0">{contaId}</span>
            <span className="text-[12px] font-bold text-[#666] truncate" title={contaNome}>{contaNome}</span>
            <ChevronDown size={10} className={`text-[#444] shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}/>
          </div>
        </td>

        {/* Por competência: mov fisico / mov virtual / diff */}
        {porComp.map(({ comp, movFisico, movVirtual, diffMov, saldoFisico, saldoVirtual, temFisico }) => (
          <td key={comp} className="px-1 py-0" style={{ minWidth: '270px' }}>
            <div className="flex gap-0 h-full">
              {/* Questor */}
              <div className="flex-1 px-2 py-2.5 text-right border-r border-[#1a1a1a] flex flex-col justify-center">
                <div className="font-mono text-[12px] font-black">
                  {temFisico || abs(movFisico) > 0.01 ? (
                    <span className={movFisico == 0 ? 'text-[#888]' : movFisico >= 0 ? 'text-[#34c759]/80' : 'text-[#ff4d00]/80'}>
                      {movFisico > 0 ? '+' : ''}{fmt(movFisico)}
                    </span>
                  ) : <span className="text-[#252525]">—</span>}
                </div>
                {abs(saldoFisico) > 0.01 && (
                  <div className="text-[10px] font-bold font-mono text-[#555] mt-0.5" title="Saldo Final no Mês">
                    S: {fmt(saldoFisico)}
                  </div>
                )}
              </div>
              {/* Vulcano */}
              <div className="flex-1 px-2 py-2.5 text-right border-r border-[#1a1a1a] flex flex-col justify-center">
                <div className="font-mono text-[12px] font-black">
                  {abs(movVirtual) > 0.01 ? (
                    <span className={movVirtual >= 0 ? 'text-[#a259ff]' : 'text-[#ff9f0a]'}>
                      {movVirtual > 0 ? '+' : ''}{fmt(movVirtual)}
                    </span>
                  ) : <span className="text-[#252525]">—</span>}
                </div>
                {abs(saldoVirtual) > 0.01 && (
                  <div className="text-[10px] font-bold font-mono text-[#555] mt-0.5" title="Saldo Final no Mês (Virtual)">
                    S: {fmt(saldoVirtual)}
                  </div>
                )}
              </div>
              {/* Delta */}
              <div className="flex-1 px-2 py-2.5 text-right font-mono text-[13px] font-black">
                {abs(diffMov) < DIVERGENCIA_CORTE ? (
                  <span className="text-[#333]">✓</span>
                ) : (
                  <span style={{ color: corDiff(diffMov) }}>
                    {diffMov > 0 ? '+' : ''}{fmt(diffMov)}
                  </span>
                )}
              </div>
            </div>
          </td>
        ))}

        {/* Saldo final total diff */}
        <td className="px-3 py-2.5 text-right min-w-[130px]">
          {abs(totalDiffSaldo) < DIVERGENCIA_CORTE ? (
            <span className="text-[12px] font-black text-[#34c759] uppercase tracking-wider">Conciliado</span>
          ) : (
            <div>
              <span className="font-mono text-[14px] font-black" style={{ color: corDiff(totalDiffSaldo) }}>
                {totalDiffSaldo > 0 ? '+' : ''}{fmt(totalDiffSaldo)}
              </span>
              <p className="text-[10px] font-black uppercase tracking-widest text-[#555] mt-0.5">divergência saldo</p>
            </div>
          )}
        </td>
      </tr>

      {/* Detalhe expandido: lançamentos lado a lado */}
      {open && (
        <tr>
          <td colSpan={porComp.length + 2} className="p-0 bg-[#070707]">
            {/* Botão Racional */}
            {todosVirtualLogica.length > 0 && (
              <div className="px-4 py-2 border-b border-[#111] flex items-center gap-2">
                <button
                  onClick={e => { e.stopPropagation(); setRacionalOpen(true); }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#a259ff]/15 border border-[#a259ff]/30 rounded text-[11px] font-black uppercase tracking-widest text-[#a259ff] hover:bg-[#a259ff]/25 transition-all"
                >
                  <Zap size={11}/> Racional do Cálculo
                </button>
                <span className="text-[10px] text-[#444] font-bold">{todosVirtualLogica.length} etapa{todosVirtualLogica.length !== 1 ? 's' : ''} de cálculo</span>
              </div>
            )}
            <div className="grid grid-cols-2 divide-x divide-[#111]">
              {/* Questor */}
              <div>
                <div className="px-4 py-1.5 bg-[#0f0f0f] border-b border-[#111]">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#ff4d00]">Questor — Físico</span>
                </div>
                {porComp.flatMap(c => c.detalhesFisico).length === 0 ? (
                  <p className="px-5 py-3 text-[11px] font-bold text-[#333] uppercase italic">Sem lançamentos físicos</p>
                ) : (
                  <div className="overflow-x-auto pb-2">
                    <table className="w-auto text-[11px] table-auto whitespace-nowrap ml-2 mt-1">
                      <tbody>
                        {porComp.flatMap((c, ci) => c.detalhesFisico.map((d, i) => (
                          <tr key={`${ci}-${i}`} className="border-b border-[#0e0e0e] hover:bg-[#0a0a0a]">
                            <td className="px-2 py-1 font-mono font-bold text-[#555]">{d.data}</td>
                            <td className="px-2 py-1 font-bold text-[#666]" title={d.historico}>{d.historico}</td>
                            <td className="px-2 py-1 text-center font-black text-[13px]" style={{ color: d.natureza === 'D' ? '#34c759' : '#ff4d00' }}>{d.natureza}</td>
                            <td className="px-2 py-1 text-right font-mono font-black text-[#999]">{fmt(d.valor)}</td>
                          </tr>
                        )))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
              {/* Vulcano */}
              <div>
                <div className="px-4 py-1.5 bg-[#0f0f0f] border-b border-[#111]">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#a259ff]">Vulcano — Societário</span>
                </div>
                {porComp.flatMap(c => c.detalhesVirtual).length === 0 ? (
                  <p className="px-5 py-3 text-[11px] font-bold text-[#333] uppercase italic">Sem lançamentos societários</p>
                ) : (
                  <div className="overflow-x-auto pb-2">
                    <table className="w-auto text-[11px] table-auto whitespace-nowrap ml-2 mt-1">
                      <tbody>
                        {porComp.flatMap((c, ci) => c.detalhesVirtual.map((d, i) => (
                          <tr key={`${ci}-${i}`} className="border-b border-[#0e0e0e] hover:bg-[#0a0a0a]">
                            <td className="px-2 py-1 font-mono font-bold text-[#555]">{d.data}</td>
                            <td className="px-2 py-1 font-bold text-[#666]" title={d.historico || d.logica}>{d.historico}</td>
                            <td className="px-2 py-1 text-center font-black text-[13px]" style={{ color: d.natureza === 'D' ? '#a259ff' : '#ff9f0a' }}>{d.natureza}</td>
                            <td className="px-2 py-1 text-right font-mono font-black text-[#999]">{fmt(d.valor)}</td>
                          </tr>
                        )))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}

      {/* ── Modal Racional ── */}
      {racionalOpen && (
        <tr>
          <td colSpan={porComp.length + 2} className="p-0">
            <div
              className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6"
              onClick={() => setRacionalOpen(false)}
            >
              <div
                className="bg-[#0d0d0d] border border-[#a259ff]/30 rounded-lg w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl shadow-[#a259ff]/10"
                onClick={e => e.stopPropagation()}
              >
                <div className="flex items-center justify-between px-6 py-4 border-b border-[#1a1a1a]">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-[#a259ff] mb-0.5">Racional de Cálculo — Vulcano Motor Societário</p>
                    <p className="text-white font-black text-[15px]">
                      <span className="text-[#ff4d00] font-mono mr-2">{contaId}</span>{contaNome}
                    </p>
                  </div>
                  <button
                    onClick={() => setRacionalOpen(false)}
                    className="w-8 h-8 rounded bg-[#1a1a1a] hover:bg-[#222] text-[#666] hover:text-white font-black text-[18px] flex items-center justify-center transition-all"
                  >×</button>
                </div>
                <div className="overflow-y-auto flex-1 px-6 py-4 flex flex-col gap-3">
                  {todosVirtualLogica.map((d, i) => (
                    <div key={i} className="border border-[#1e1e1e] rounded p-4 bg-[#0a0a0a] hover:border-[#a259ff]/20 transition-colors">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-[9px] font-black uppercase tracking-widest text-[#555]">{d.comp} · {d.data}</span>
                        <span
                          className="text-[10px] font-black px-2 py-0.5 rounded"
                          style={{ background: d.natureza === 'D' ? '#a259ff22' : '#ff9f0a22', color: d.natureza === 'D' ? '#a259ff' : '#ff9f0a' }}
                        >
                          {d.natureza === 'D' ? 'DÉBITO' : 'CRÉDITO'} {fmt(d.valor)}
                        </span>
                      </div>
                      <p className="text-[12px] font-bold text-[#888] mb-1">{d.historico}</p>
                      {d.logica && (
                        <p className="text-[11px] font-mono text-[#a259ff]/70 bg-[#a259ff]/5 rounded px-3 py-2 border-l-2 border-[#a259ff]/30">
                          {d.logica}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── MAIN VIEW ────────────────────────────────────────────────────────────────
export const AuditoriaERPView = ({ selectedEmpresa }) => {
  const now = new Date();
  const mesAtual = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

  const [periodoInicio, setPeriodoInicio] = useState(mesAtual);
  const [periodoFim,    setPeriodoFim]    = useState(mesAtual);
  const [filtroEmpId,   setFiltroEmpId]   = useState('');
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [empsLoading,     setEmpsLoading]     = useState(false);
  // dados: { 'YYYY-MM': { fisico: [...contas], virtual: [...contas] } }
  const [dadosPorMes, setDadosPorMes] = useState({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  // ── Diagnóstico IA (PyOD + DuckDB + KMeans + LevelShift) ──────────────────
  const [diagData,    setDiagData]    = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [showDiag,    setShowDiag]    = useState(false);

  // ── Carrega empreendimentos na montagem ──────────────────────────────────
  useEffect(() => {
    if (!selectedEmpresa) return;
    setEmpsLoading(true);
    fetch(`${API_BASE}/api/empreendimentos/basico?empresa_id=${selectedEmpresa}`)
      .then(r => r.json())
      .then(j => { setEmpreendimentos(j.empreendimentos || []); setEmpsLoading(false); })
      .catch(() => setEmpsLoading(false));
  }, [selectedEmpresa]);

  const competencias = useMemo(() => {
    try { return gerarCompetencias(periodoInicio, periodoFim); }
    catch { return [periodoInicio]; }
  }, [periodoInicio, periodoFim]);

  const periodoValido = competencias.length <= 18;

  // ── Fetch: virtual via contabilizacoes, fisico via saldo-contas direto no LCTOCTB ──
  const fetchTudo = useCallback(async () => {
    if (!selectedEmpresa || !periodoValido) return;
    setLoading(true);
    setError('');
    const novos = {};
    try {
      const virtuaisPorMes = {};
      const contasGlobais = new Set();

      // PASS 1: Busca Virtual para todos os meses (SEQUENCIAL PARA EVITAR LOCK DO FIREBIRD)
      for (const comp of competencias) {
        const [ano, mes] = comp.split('-').map(Number);

        // 1. Busca virtual (motor societário Vulcano)
        let urlV = `${API_BASE}/api/questor/contabilizacoes?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}`;
        if (filtroEmpId) urlV += `&empreendimento_id=${filtroEmpId}`;
        const respV = await fetch(urlV);
        const jsonV = await respV.json();

        const accVirtual = {};
        const mergeConta = (source, acc) => {
          (source || []).forEach(c => {
            const k = String(c.conta);
            if (!acc[k]) {
              acc[k] = { ...c, detalhes: [...(c.detalhes || [])] };
            } else {
              acc[k].saldo_anterior    = (acc[k].saldo_anterior    || 0) + (c.saldo_anterior    || 0);
              acc[k].movimento_debito  = (acc[k].movimento_debito  || 0) + (c.movimento_debito  || 0);
              acc[k].movimento_credito = (acc[k].movimento_credito || 0) + (c.movimento_credito || 0);
              acc[k].movimento_liquido = (acc[k].movimento_liquido || 0) + (c.movimento_liquido || 0);
              acc[k].saldo_final       = (acc[k].saldo_final       || 0) + (c.saldo_final       || 0);
              acc[k].detalhes.push(...(c.detalhes || []));
            }
          });
        };
        (jsonV.data || []).forEach(emp => mergeConta(emp.contas_virtuais, accVirtual));
        const virtualList = Object.values(accVirtual);
        
        virtualList.forEach(c => contasGlobais.add(c.conta));
        virtuaisPorMes[comp] = virtualList;
      }

      // PASS 2: Busca Físico (Questor) para todos os meses usando a união de todas as contas
      const contasCsv = Array.from(contasGlobais).join(',');
      
      if (contasGlobais.size > 0) {
        for (const comp of competencias) {
          const [ano, mes] = comp.split('-').map(Number);
          
          let fisicoList = [];
          let urlF = `${API_BASE}/api/questor/saldo-contas?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}&contas=${contasCsv}`;
          if (filtroEmpId) urlF += `&empreendimento_id=${filtroEmpId}`;
          
          try {
            const respF = await fetch(urlF);
            const jsonF = await respF.json();
            fisicoList = jsonF.data || [];
          } catch (ef) {
            console.warn('saldo-contas error:', ef);
          }

          novos[comp] = {
            fisico:  fisicoList,
            virtual: virtuaisPorMes[comp],
          };
        }
      } else {
        competencias.forEach(comp => {
          novos[comp] = { fisico: [], virtual: [] };
        });
      }

      setDadosPorMes(novos);
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  }, [selectedEmpresa, competencias, filtroEmpId]);

  const fetchDiagnostico = async () => {
    if (!selectedEmpresa) return;

    // Converte os dados carregados na auditoria para a lista de DiagnosticoRow
    const linhasMap = {};
    Object.entries(dadosPorMes).forEach(([comp, data]) => {
      // 1. Processa virtuais
      (data.virtual || []).forEach(v => {
        const key = `${v.conta}_${comp}`;
        if (!linhasMap[key]) {
          linhasMap[key] = { conta_id: parseInt(v.conta), competencia: comp, saldo_q: 0, saldo_v: 0, n_lanc_q: 0, n_lanc_v: 0 };
        }
        linhasMap[key].saldo_v += (v.movimento_liquido || 0);
        linhasMap[key].n_lanc_v += 1;
      });
      // 2. Processa físicos
      (data.fisico || []).forEach(f => {
        const key = `${f.conta}_${comp}`;
        if (!linhasMap[key]) {
          linhasMap[key] = { conta_id: parseInt(f.conta), competencia: comp, saldo_q: 0, saldo_v: 0, n_lanc_q: 0, n_lanc_v: 0 };
        }
        linhasMap[key].saldo_q += (f.movimento_liquido || 0);
        linhasMap[key].n_lanc_q += 1;
      });
    });

    const linhas = Object.values(linhasMap).filter(r => r.conta_id > 0);

    if (linhas.length === 0) {
      setDiagData({ error: 'Nenhum dado carregado. Clique em "Auditar" primeiro.' });
      setShowDiag(true);
      return;
    }

    setDiagLoading(true);
    setShowDiag(true);
    try {
      const r = await fetch(`${API_BASE}/api/auditoria/diagnostico`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa),
          linhas: linhas,
          top_n: 20
        })
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Erro no diagnóstico');
      setDiagData(j);
    } catch (e) {
      setDiagData({ error: String(e) });
    }
    setDiagLoading(false);
  };

  // ── Apenas contas que o Vulcano calculou para injeção (contas_virtuais) ──
  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ virtual }) => {
      (virtual || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta}`;
      });
    });
    return m; // { contaId → nome } — apenas contas com lançamento societário
  }, [dadosPorMes]);

  // ── Métricas globais — filtra fisico apenas nas contas que geramos ────────
  const metrics = useMemo(() => {
    let totMovFisico = 0, totMovVirtual = 0;
    let contasConciliadas = 0, contasDivergentes = 0;
    const contasVirtualIds = Object.keys(contasMap);

    Object.values(dadosPorMes).forEach(({ fisico, virtual }) => {
      // Questor: só as contas que o Vulcano calcula
      (fisico || []).filter(c => contasVirtualIds.includes(String(c.conta)))
        .forEach(c => { totMovFisico += c.movimento_liquido || 0; });
      (virtual || []).forEach(c => { totMovVirtual += c.movimento_liquido || 0; });
    });

    Object.keys(contasMap).forEach(contaId => {
      let diffTotal = 0;
      competencias.forEach(comp => {
        const f = dadosPorMes[comp]?.fisico?.find( r => String(r.conta) === contaId);
        const v = dadosPorMes[comp]?.virtual?.find(r => String(r.conta) === contaId);
        diffTotal += ((v?.movimento_liquido || 0) - (f?.movimento_liquido || 0));
      });
      if (abs(diffTotal) < DIVERGENCIA_CORTE) contasConciliadas++;
      else contasDivergentes++;
    });

    const diffMov   = totMovVirtual - totMovFisico;
    const pctAdh    = (contasConciliadas + contasDivergentes) > 0
      ? (contasConciliadas / (contasConciliadas + contasDivergentes)) * 100
      : 0;

    return { totMovFisico, totMovVirtual, diffMov, pctAdh, contasConciliadas, contasDivergentes };
  }, [dadosPorMes, contasMap, competencias]);

  const temDados = Object.keys(dadosPorMes).length > 0;

  return (
    <div className="flex flex-col gap-5 pb-10 text-[#e5e2e1] animate-in fade-in">
      {/* Header */}
      <div className="border-b border-[#222] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3 mb-1">
          <ShieldCheck className="text-[#ff4d00]" size={36}/> Auditoria ERP
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#555] font-black">
          Contas a Injetar no Questor — Calculado (Vulcano) × Registrado (Questor)
        </p>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-end bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Período De</span>
          <input type="month" value={periodoInicio}
            onChange={e => { const v = e.target.value; setPeriodoInicio(v); if (v > periodoFim) setPeriodoFim(v); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Até</span>
          <input type="month" value={periodoFim}
            onChange={e => { const v = e.target.value; setPeriodoFim(v); if (v < periodoInicio) setPeriodoInicio(v); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>
        <div className="flex flex-col gap-1 min-w-[220px]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">
            Empreendimento {empsLoading ? '(carregando...)' : `(${empreendimentos.length})`}
          </span>
          <select value={filtroEmpId} onChange={e => setFiltroEmpId(e.target.value)}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-bold outline-none focus:border-[#ff4d00] transition-colors">
            <option value="">Todos os empreendimentos</option>
            {empreendimentos.map(e => <option key={e.id} value={String(e.id)}>{e.nome}</option>)}
          </select>
        </div>
        <div className="flex flex-col justify-end pb-0.5">
          <span className="text-[9px] font-bold text-[#444] uppercase tracking-wider">
            {competencias.length} mês{competencias.length !== 1 ? 'es' : ''}
            {!periodoValido && <span className="text-[#ff4d00] ml-2">⚠ máx. 18</span>}
          </span>
        </div>
        <button onClick={fetchTudo} disabled={loading || !periodoValido || !selectedEmpresa}
          className="ml-auto px-6 py-2.5 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? `Auditando ${competencias.length} meses...` : 'Auditar'}
        </button>
        <button onClick={fetchDiagnostico} disabled={diagLoading || !selectedEmpresa}
          title="Analisa Questor ↔ Vulcano com PyOD + DuckDB + KMeans (24 meses)"
          className={`px-5 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all disabled:opacity-40 border ${
            showDiag ? 'bg-[#a259ff]/20 border-[#a259ff]/60 text-[#a259ff]' : 'bg-[#111] border-[#333] text-[#555] hover:text-[#a259ff] hover:border-[#a259ff]/40'
          }`}>
          {diagLoading ? <Zap className="animate-spin" size={12}/> : <Zap size={12}/>}
          {diagLoading ? 'Analisando...' : '🧠 Diagnóstico IA'}
        </button>
      </div>

      {error && (
        <div className="bg-[#ff4d00]/10 border border-[#ff4d00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={14} className="text-[#ff4d00] shrink-0"/>
          <p className="text-sm font-mono text-[#ff4d00]">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-12">
          <Zap className="animate-spin text-[#ff4d00]" size={28}/>
          <span className="text-xs font-black uppercase tracking-widest text-[#555]">
            Confrontando {competencias.length} competência{competencias.length > 1 ? 's' : ''}...
          </span>
        </div>
      )}

      {/* ── Painel Diagnóstico IA ── */}
      {showDiag && (
        <div className="bg-[#0a0a0a] border border-[#a259ff]/30 rounded-lg overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-[#a259ff]/20 bg-[#a259ff]/5">
            <div className="flex items-center gap-3">
              <span className="text-[#a259ff] text-lg">🧠</span>
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-[#a259ff]">Diagnóstico IA — Causa Raiz Questor ↔ Vulcano</p>
                <p className="text-[9px] text-[#555] mt-0.5">PyOD IsolationForest · DuckDB · KMeans · LevelShift (24 meses)</p>
              </div>
            </div>
            <button onClick={() => setShowDiag(false)} className="text-[#555] hover:text-white text-xs px-2 py-1">✕ Fechar</button>
          </div>

          {diagLoading && (
            <div className="flex items-center justify-center gap-3 py-10">
              <span className="text-[#a259ff] animate-spin text-xl">⚡</span>
              <span className="text-[10px] font-black uppercase tracking-widest text-[#555]">Rodando PyOD + DuckDB + KMeans...</span>
            </div>
          )}

          {diagData?.error && (
            <div className="p-4 text-[#ff4d00] text-xs font-mono">{diagData.error}</div>
          )}

          {diagData && !diagData.error && !diagLoading && (
            <div className="p-4 space-y-4">
              {/* Summary banner */}
              <div className="bg-[#111] border border-[#222] rounded p-3 text-[10px] text-[#888] font-mono">
                {diagData.summary}
              </div>

              {/* Tabela de contas */}
              <div className="overflow-auto max-h-[500px] custom-scrollbar">
                <table className="w-full text-left border-collapse text-[10px]">
                  <thead className="sticky top-0 bg-[#0d0d0d] border-b border-[#222]">
                    <tr>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest">Conta</th>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest w-32">Score IA</th>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest">Padrão</th>
                      <th className="p-2 text-right text-[#555] font-black uppercase tracking-widest">Δ Médio</th>
                      <th className="p-2 text-right text-[#555] font-black uppercase tracking-widest">Δ Máx</th>
                      <th className="p-2 text-center text-[#555] font-black uppercase tracking-widest">Meses Div.</th>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest">Mudança de Nível</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(diagData.contas || []).map((c, i) => {
                      const score = c.anomaly_score ?? 0;
                      const isAnomalia = c.anomaly_label === 'ANOMALIA';
                      const scoreColor = score > 0.7 ? '#ff4d00' : score > 0.4 ? '#ffcc00' : '#34c759';
                      const padraoColors = {
                        'Exato': 'bg-[#34c759]/10 text-[#34c759] border-[#34c759]/30',
                        'Lag Temporal': 'bg-[#007aff]/10 text-[#007aff] border-[#007aff]/30',
                        'Percentual Fixo': 'bg-[#ffcc00]/10 text-[#ffcc00] border-[#ffcc00]/30',
                        'Caótico': 'bg-[#ff4d00]/10 text-[#ff4d00] border-[#ff4d00]/30',
                      };
                      const padraoClass = padraoColors[c.padrao] || 'bg-[#222] text-[#555] border-[#333]';
                      return (
                        <tr key={i} className={`border-b border-[#111] ${isAnomalia ? 'bg-[#ff4d00]/5' : ''} hover:bg-[#111]/60`}>
                          <td className="p-2">
                            <div className="font-black text-white text-[10px]">{c.conta_nome}</div>
                            <div className="text-[#555] font-mono text-[9px]">#{c.conta_id}</div>
                          </td>
                          <td className="p-2">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-[#1a1a1a] rounded-full h-1.5">
                                <div className="h-1.5 rounded-full transition-all" style={{width:`${score*100}%`, background: scoreColor}}/>
                              </div>
                              <span className="font-black text-[9px] font-mono" style={{color: scoreColor}}>{Math.round(score*100)}%</span>
                            </div>
                            {isAnomalia && <span className="text-[8px] text-[#ff4d00] font-black uppercase">⚠ Anômalo</span>}
                          </td>
                          <td className="p-2">
                            <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border uppercase tracking-widest ${padraoClass}`}>
                              {c.padrao}
                            </span>
                          </td>
                          <td className="p-2 text-right font-mono text-[#ccc]">
                            {c.media_delta >= 0 ? '+' : ''}{c.media_delta?.toLocaleString('pt-BR', {minimumFractionDigits:0, maximumFractionDigits:0})}
                          </td>
                          <td className="p-2 text-right font-mono text-[#ff4d00]">
                            {c.max_delta_abs?.toLocaleString('pt-BR', {minimumFractionDigits:0, maximumFractionDigits:0})}
                          </td>
                          <td className="p-2 text-center">
                            <span className={`font-black text-[9px] ${c.pct_meses_divergentes > 80 ? 'text-[#ff4d00]' : c.pct_meses_divergentes > 40 ? 'text-[#ffcc00]' : 'text-[#34c759]'}`}>
                              {c.pct_meses_divergentes?.toFixed(0)}%
                            </span>
                          </td>
                          <td className="p-2">
                            {c.level_shift ? (
                              <div>
                                <span className="text-[#ffcc00] font-black text-[9px]">⬆ {c.level_shift.competencia}</span>
                                <div className="text-[8px] text-[#555] mt-0.5 font-mono">
                                  {c.level_shift.delta_antes?.toFixed(0)} → {c.level_shift.delta_depois?.toFixed(0)}
                                </div>
                              </div>
                            ) : (
                              <span className="text-[#333] text-[8px]">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Cards de resumo ── */}
      {!loading && temDados && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Gauge conciliação */}
          <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4 col-span-1">
            <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-2">Conciliação Global</p>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-black font-mono" style={{ color: metrics.pctAdh >= 95 ? '#34c759' : metrics.pctAdh >= 80 ? '#ffcc00' : '#ff4d00' }}>
                {metrics.pctAdh.toFixed(0)}%
              </span>
              <span className="text-[10px] text-[#555] mb-0.5 font-bold">aderência</span>
            </div>
            <div className="w-full bg-[#1a1a1a] rounded-full h-1.5 mt-2">
              <div className="h-1.5 rounded-full transition-all" style={{
                width: `${metrics.pctAdh}%`,
                background: metrics.pctAdh >= 95 ? '#34c759' : metrics.pctAdh >= 80 ? '#ffcc00' : '#ff4d00'
              }}/>
            </div>
            <p className="text-[9px] text-[#444] mt-2 font-bold">
              <span className="text-[#34c759]">{metrics.contasConciliadas}</span> OK · <span className="text-[#ff4d00]">{metrics.contasDivergentes}</span> div.
            </p>
          </div>

          {[
            { label: 'Movimento Total Questor', val: metrics.totMovFisico,  cor: '#ff4d00' },
            { label: 'Movimento Total Vulcano', val: metrics.totMovVirtual, cor: '#a259ff' },
            { label: 'Diferença de Movimento',  val: metrics.diffMov, cor: corDiff(metrics.diffMov) },
          ].map(m => (
            <div key={m.label} className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">
              <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-2">{m.label}</p>
              <p className="text-xl font-black font-mono" style={{ color: m.cor }}>{fmt(m.val)}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Tabela de confronto ── */}
      {!loading && Object.keys(contasMap).length > 0 && (
        <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded-sm overflow-hidden">
          {/* Cabeçalho da legenda de colunas */}
          <div className="px-4 py-3 border-b border-[#1a1a1a] flex items-center gap-4 flex-wrap">
            <h3 className="text-[10px] font-black uppercase tracking-widest text-white">Confronto por Conta</h3>
            <div className="flex gap-4 ml-auto text-[9px] font-bold uppercase tracking-widest">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#ff4d00] inline-block"/>
                <span className="text-[#ff4d00]">Questor (Físico)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#a259ff] inline-block"/>
                <span className="text-[#a259ff]">Vulcano (Societário)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#ffcc00] inline-block"/>
                <span className="text-[#ffcc00]">Δ Divergência</span>
              </span>
            </div>
          </div>

          <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 300px)' }}>
            <table
              className="w-full border-collapse"
              style={{ minWidth: `${220 + competencias.length * 270 + 140}px` }}
            >
              <thead>
                <tr className="bg-[#111]">
                  {/* Conta */}
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#1a1a1a] sticky left-0 top-0 z-30 bg-[#111] min-w-[220px]">
                    Conta
                  </th>
                  {/* Grupos de colunas por mês */}
                  {competencias.map(comp => (
                    <th key={comp} colSpan={1} className="p-0 border-b border-[#1a1a1a] border-l border-[#111] sticky top-0 z-20 bg-[#111]"
                        style={{ minWidth: '270px' }}>
                      <div className="px-2 py-1.5 text-center text-[9px] font-black uppercase tracking-widest text-[#666] border-b border-[#222]">
                        {labelMes(comp)}
                      </div>
                      <div className="flex text-[7px] font-black uppercase tracking-widest text-[#333]">
                        <div className="flex-1 px-2 py-1 text-right border-r border-[#111]">Questor</div>
                        <div className="flex-1 px-2 py-1 text-right border-r border-[#111]">Vulcano</div>
                        <div className="flex-1 px-2 py-1 text-right">Δ</div>
                      </div>
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-white border-b border-[#1a1a1a] sticky top-0 z-20 bg-[#111] min-w-[130px]">
                    Status Final
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(contasMap).map(([contaId, contaNome]) => (
                  <ContaConfronto
                    key={contaId}
                    contaId={contaId}
                    contaNome={contaNome}
                    competencias={competencias}
                    dadosPorMes={dadosPorMes}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !temDados && !error && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <div className="w-16 h-16 bg-[#ff4d00]/10 border border-[#ff4d00]/20 rounded flex items-center justify-center">
            <ShieldCheck className="text-[#ff4d00]" size={28}/>
          </div>
          <p className="font-black uppercase tracking-widest text-white text-sm">
            Selecione o período e clique em Auditar
          </p>
          <p className="text-[10px] text-[#444] uppercase tracking-widest max-w-sm">
            Confronta movimento e saldo do Questor (físico) com o motor societário Vulcano (POC + tributos) conta a conta
          </p>
          <button onClick={fetchTudo} disabled={!selectedEmpresa}
            className="mt-2 px-6 py-3 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40">
            <Zap size={13}/> Iniciar Auditoria
          </button>
        </div>
      )}
    </div>
  );
};
