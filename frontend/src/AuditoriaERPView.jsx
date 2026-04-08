import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle,
  RefreshCw, ChevronDown
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:6000";

const fmt = (v) =>
  new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v || 0);

const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
const DIVERGENCIA_CORTE = 0.50;
const abs = (v) => Math.abs(v || 0);

// ── Helpers ──────────────────────────────────────────────────────────────────
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

function corDiff(v) {
  if (abs(v) < DIVERGENCIA_CORTE) return '#34c759';
  if (abs(v) < 5000)              return '#ffcc00';
  return '#ff4d00';
}

// ── Célula de valor ───────────────────────────────────────────────────────────
function Valor({ v, cor }) {
  if (abs(v) < 0.01) return <span className="text-[#2a2a2a]">—</span>;
  return <span style={{ color: cor }} className="font-mono text-[10px]">{fmt(v)}</span>;
}

// ── Linha Δ (delta) ───────────────────────────────────────────────────────────
function DeltaCell({ v }) {
  if (abs(v) < DIVERGENCIA_CORTE) return <span className="text-[#333] text-[10px]">✓</span>;
  return (
    <span className="font-mono text-[10px] font-bold" style={{ color: corDiff(v) }}>
      {v > 0 ? '+' : ''}{fmt(v)}
    </span>
  );
}

// ── Bloco de 4 valores por fonte (SA | Déb | Créd | SF) ───────────────────────
function CelulaMes({ sa, deb, cred, sf, cor }) {
  return (
    <>
      <td className="px-1.5 py-1.5 text-right border-r border-[#151515] w-24">
        <Valor v={sa}  cor={cor + 'aa'} />
      </td>
      <td className="px-1.5 py-1.5 text-right border-r border-[#151515] w-24">
        <Valor v={deb} cor="#34c759aa" />
      </td>
      <td className="px-1.5 py-1.5 text-right border-r border-[#151515] w-24">
        <Valor v={cred} cor="#ff4d00aa" />
      </td>
      <td className="px-1.5 py-1.5 text-right border-r border-[#1e1e1e] w-24">
        <Valor v={sf}  cor={cor} />
      </td>
    </>
  );
}

// ── Linha de conta ────────────────────────────────────────────────────────────
function ContaRow({ contaId, contaNome, competencias, dadosPorMes }) {
  const [open, setOpen] = useState(false);

  const porComp = competencias.map(comp => {
    const bloco = dadosPorMes[comp] || {};
    const f = (bloco.fisico  || []).find(r => String(r.conta) === String(contaId)) || {};
    const v = (bloco.virtual || []).find(r => String(r.conta) === String(contaId)) || {};
    return {
      comp,
      f_sa:  f.saldo_anterior   || 0,
      f_deb: f.movimento_debito || 0,
      f_cred:f.movimento_credito|| 0,
      f_sf:  f.saldo_final      || 0,
      v_sa:  v.saldo_anterior   || 0,
      v_deb: v.movimento_debito || 0,
      v_cred:v.movimento_credito|| 0,
      v_sf:  v.saldo_final      || 0,
      det_f: f.detalhes || [],
      det_v: v.detalhes || [],
    };
  });

  const temDado = porComp.some(c =>
    abs(c.f_deb) > 0 || abs(c.f_cred) > 0 ||
    abs(c.v_deb) > 0 || abs(c.v_cred) > 0
  );
  if (!temDado) return null;

  const ultimo = porComp[porComp.length - 1] || {};
  const diffSF  = ultimo.v_sf - ultimo.f_sf;
  const temDiv  = abs(diffSF) >= DIVERGENCIA_CORTE;

  const trBase  = temDiv
    ? 'border-b border-[#ff4d00]/10 bg-[#0f0600]'
    : 'border-b border-[#111] bg-[#0a0a0a]';

  return (
    <>
      {/* ── Linha QUESTOR ──────────────────────────────────────── */}
      <tr className={`${trBase} hover:brightness-125 cursor-pointer`} onClick={() => setOpen(o => !o)}>
        {/* Conta — rowspan visual via primeira linha */}
        <td className="px-3 py-1.5 sticky left-0 z-10 bg-[#0d0d0d] min-w-[200px] border-r border-[#1e1e1e]" rowSpan={2}>
          <div className="flex items-center gap-2">
            {temDiv
              ? <XCircle size={12} className="text-[#ff4d00] shrink-0"/>
              : <CheckCircle2 size={12} className="text-[#34c759] shrink-0"/>
            }
            <span className="font-mono text-[11px] font-bold text-[#ff4d00]">{contaId}</span>
            <span className="text-[10px] text-[#555] truncate max-w-[110px]" title={contaNome}>{contaNome}</span>
            <ChevronDown size={9} className={`text-[#444] shrink-0 ml-auto transition-transform ${open ? 'rotate-180':''}`}/>
          </div>
        </td>
        {/* Label fonte */}
        <td className="px-2 py-1.5 border-r border-[#1e1e1e] w-20">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#ff4d00]">Questor</span>
        </td>
        {/* Valores por mês */}
        {porComp.map(c => (
          <CelulaMes key={c.comp}
            sa={c.f_sa} deb={c.f_deb} cred={c.f_cred} sf={c.f_sf}
            cor="#ff8c00"
          />
        ))}
        {/* Status */}
        <td className="px-3 py-1.5 text-right w-28 border-l border-[#1e1e1e]" rowSpan={2}>
          {temDiv ? (
            <div>
              <span className="font-mono text-xs font-black" style={{ color: corDiff(diffSF) }}>
                {diffSF > 0 ? '+' : ''}{fmt(diffSF)}
              </span>
              <p className="text-[8px] font-bold uppercase text-[#555] mt-0.5">Δ saldo</p>
            </div>
          ) : (
            <span className="text-[9px] font-black text-[#34c759] uppercase tracking-wider">OK</span>
          )}
        </td>
      </tr>

      {/* ── Linha VULCANO ──────────────────────────────────────── */}
      <tr className={`${trBase} hover:brightness-125`}>
        <td className="px-2 py-1.5 border-r border-[#1e1e1e] w-20">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#a259ff]">Vulcano</span>
        </td>
        {porComp.map(c => (
          <CelulaMes key={c.comp}
            sa={c.v_sa} deb={c.v_deb} cred={c.v_cred} sf={c.v_sf}
            cor="#a259ff"
          />
        ))}
      </tr>

      {/* ── Linha Δ (só se houver divergência) ────────────────── */}
      {temDiv && (
        <tr className="border-b border-[#ff4d00]/20 bg-[#0d0400]">
          <td className="sticky left-0 z-10 bg-[#0d0400]"/>
          <td className="px-2 py-1 border-r border-[#1e1e1e]">
            <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Δ</span>
          </td>
          {porComp.map(c => (
            <React.Fragment key={c.comp}>
              <td className="px-1.5 py-1 text-right border-r border-[#151515] w-24">
                <DeltaCell v={c.v_sa - c.f_sa} />
              </td>
              <td className="px-1.5 py-1 text-right border-r border-[#151515] w-24">
                <DeltaCell v={c.v_deb - c.f_deb} />
              </td>
              <td className="px-1.5 py-1 text-right border-r border-[#151515] w-24">
                <DeltaCell v={c.v_cred - c.f_cred} />
              </td>
              <td className="px-1.5 py-1 text-right border-r border-[#1e1e1e] w-24">
                <DeltaCell v={c.v_sf - c.f_sf} />
              </td>
            </React.Fragment>
          ))}
          <td className="border-l border-[#1e1e1e]"/>
        </tr>
      )}

      {/* ── Detalhe expandido ─────────────────────────────────── */}
      {open && (
        <tr>
          <td colSpan={3 + competencias.length * 4 + 1} className="p-0 bg-[#060606]">
            <div className="grid grid-cols-2 divide-x divide-[#111]">
              {[
                { label: 'Questor — Físico', cor: '#ff4d00', rows: porComp.flatMap(c => c.det_f) },
                { label: 'Vulcano — Societário', cor: '#a259ff', rows: porComp.flatMap(c => c.det_v) },
              ].map(({ label, cor, rows }) => (
                <div key={label}>
                  <div className="px-4 py-1.5 bg-[#0f0f0f] border-b border-[#111]">
                    <span className="text-[8px] font-black uppercase tracking-widest" style={{ color: cor }}>{label}</span>
                  </div>
                  {rows.length === 0 ? (
                    <p className="px-5 py-3 text-[9px] text-[#333] italic uppercase font-bold">Sem lançamentos</p>
                  ) : (
                    <table className="w-full text-[10px]">
                      <tbody>
                        {rows.map((d, i) => (
                          <tr key={i} className="border-b border-[#0e0e0e] hover:bg-[#0a0a0a]">
                            <td className="px-4 py-1 font-mono text-[#444] w-24 shrink-0">{d.data}</td>
                            <td className="px-2 py-1 text-[#555] truncate max-w-[260px]" title={d.historico || d.logica}>{d.historico || d.logica}</td>
                            <td className="px-2 py-1 text-center font-bold w-6" style={{ color: d.natureza === 'D' ? '#34c759' : '#ff4d00' }}>{d.natureza}</td>
                            <td className="px-4 py-1 text-right font-mono text-[#888] w-28">{fmt(d.valor)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ))}
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
  const [dadosPorMes, setDadosPorMes] = useState({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

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

  const periodoValido = competencias.length <= 12;

  const fetchTudo = useCallback(async () => {
    if (!selectedEmpresa || !periodoValido) return;
    setLoading(true); setError('');
    const novos = {};
    try {
      await Promise.all(competencias.map(async (comp) => {
        const [ano, mes] = comp.split('-').map(Number);
        let url = `${API_BASE}/api/questor/contabilizacoes?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}`;
        if (filtroEmpId) url += `&empreendimento_id=${filtroEmpId}`;
        const json = await (await fetch(url)).json();

        const merge = (source, acc) => {
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

        const accF = {}, accV = {};
        (json.data || []).forEach(emp => {
          merge(emp.contas_fisicas,  accF);
          merge(emp.contas_virtuais, accV);
        });
        novos[comp] = { fisico: Object.values(accF), virtual: Object.values(accV) };
      }));
      setDadosPorMes(novos);
    } catch (e) { setError(String(e)); }
    setLoading(false);
  }, [selectedEmpresa, competencias, filtroEmpId, periodoValido]);

  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ fisico, virtual }) => {
      [...(fisico || []), ...(virtual || [])].forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta}`;
      });
    });
    return m;
  }, [dadosPorMes]);

  const metrics = useMemo(() => {
    let ok = 0, div = 0;
    Object.keys(contasMap).forEach(id => {
      const diffTotal = competencias.reduce((s, comp) => {
        const f = dadosPorMes[comp]?.fisico?.find( r => String(r.conta) === id);
        const v = dadosPorMes[comp]?.virtual?.find(r => String(r.conta) === id);
        return s + ((v?.saldo_final || 0) - (f?.saldo_final || 0));
      }, 0);
      abs(diffTotal) < DIVERGENCIA_CORTE ? ok++ : div++;
    });
    const pct = (ok + div) > 0 ? (ok / (ok + div)) * 100 : 0;
    return { ok, div, pct };
  }, [dadosPorMes, contasMap, competencias]);

  const temDados = Object.keys(dadosPorMes).length > 0;
  // Largura fixa por mês: 4 colunas × 96px = 384px
  const COL_W = 96;
  const COLS_PER_MES = 4;

  return (
    <div className="flex flex-col gap-5 pb-10 text-[#e5e2e1] animate-in fade-in">

      {/* Header */}
      <div className="border-b border-[#222] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3 mb-1">
          <ShieldCheck className="text-[#ff4d00]" size={36}/> Auditoria ERP
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#555] font-black">
          Confronto <span className="text-[#ff4d00]">Questor (Físico)</span> × <span className="text-[#a259ff]">Vulcano (Societário)</span> — Saldo Ant · Déb · Créd · Saldo Final por Conta/Mês
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
        <div className="flex flex-col justify-end">
          <span className="text-[9px] font-bold text-[#444] uppercase tracking-wider">
            {competencias.length} mês{competencias.length !== 1 ? 'es' : ''}
            {!periodoValido && <span className="text-[#ff4d00] ml-2">⚠ máx. 12</span>}
          </span>
        </div>
        <button onClick={fetchTudo} disabled={loading || !periodoValido || !selectedEmpresa}
          className="ml-auto px-6 py-2.5 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? `Auditando ${competencias.length} meses...` : 'Auditar'}
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

      {/* Resumo */}
      {!loading && temDados && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">
            <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-2">Conciliação Global</p>
            <div className="flex items-end gap-2 mb-2">
              <span className="text-3xl font-black font-mono" style={{ color: metrics.pct >= 95 ? '#34c759' : metrics.pct >= 80 ? '#ffcc00' : '#ff4d00' }}>
                {metrics.pct.toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-[#1a1a1a] rounded-full h-1 mb-2">
              <div className="h-1 rounded-full" style={{ width: `${metrics.pct}%`, background: metrics.pct >= 95 ? '#34c759' : metrics.pct >= 80 ? '#ffcc00' : '#ff4d00' }}/>
            </div>
            <p className="text-[9px] text-[#444] font-bold">
              <span className="text-[#34c759]">{metrics.ok}</span> conciliadas · <span className="text-[#ff4d00]">{metrics.div}</span> divergentes
            </p>
          </div>
          <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4 col-span-2 flex items-center gap-6">
            <div>
              <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-1">Legenda das colunas</p>
              <div className="flex gap-4 text-[9px] font-bold uppercase tracking-widest flex-wrap">
                <span className="text-[#666]">SA = Saldo Anterior</span>
                <span className="text-[#34c759]/70]">Déb = Movimento Débito</span>
                <span className="text-[#ff4d00]/70]">Créd = Movimento Crédito</span>
                <span className="text-[#888]">SF = Saldo Final</span>
              </div>
              <div className="flex gap-4 mt-1 text-[9px] font-bold uppercase tracking-widest">
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
          </div>
        </div>
      )}

      {/* Tabela */}
      {!loading && Object.keys(contasMap).length > 0 && (
        <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table
              className="border-collapse"
              style={{
                tableLayout: 'fixed',
                width: `${200 + 20 + competencias.length * COLS_PER_MES * COL_W + 110}px`
              }}
            >
              <colgroup>
                {/* Conta */}
                <col style={{ width: '200px' }}/>
                {/* Fonte */}
                <col style={{ width: '80px' }}/>
                {/* Colunas por mês */}
                {competencias.flatMap(c => Array(COLS_PER_MES).fill(c)).map((c, i) => (
                  <col key={`${c}-${i}`} style={{ width: `${COL_W}px` }}/>
                ))}
                {/* Status */}
                <col style={{ width: '110px' }}/>
              </colgroup>

              <thead>
                {/* Linha 1: meses */}
                <tr className="bg-[#111]">
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#222] sticky left-0 z-20 bg-[#111]" rowSpan={2}>
                    Conta
                  </th>
                  <th className="px-2 py-2 border-b border-[#222] border-r border-[#222]" rowSpan={2}>
                    <span className="text-[7px] font-black uppercase tracking-widest text-[#333]">Fonte</span>
                  </th>
                  {competencias.map(comp => (
                    <th key={comp} colSpan={COLS_PER_MES}
                        className="px-2 py-2 text-center text-[9px] font-black uppercase tracking-widest text-[#888] border-b border-[#222] border-l border-[#222]">
                      {labelMes(comp)}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#222] border-l border-[#222]" rowSpan={2}>
                    Δ SF
                  </th>
                </tr>
                {/* Linha 2: SA | Déb | Créd | SF por mês */}
                <tr className="bg-[#0f0f0f]">
                  {competencias.flatMap(comp => (
                    ['SA', 'Déb', 'Créd', 'SF'].map((col, i) => (
                      <th key={`${comp}-${col}`}
                          className={`py-1.5 text-right text-[7px] font-black uppercase tracking-widest border-b border-[#222] ${i === 0 ? 'border-l border-[#222]' : ''} ${i === 3 ? 'border-r border-[#222] text-white' : 'text-[#333]'}`}>
                        {col}
                      </th>
                    ))
                  ))}
                </tr>
              </thead>

              <tbody>
                {Object.entries(contasMap).map(([contaId, contaNome]) => (
                  <ContaRow
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
          <p className="font-black uppercase tracking-widest text-white text-sm">Selecione o período e clique em Auditar</p>
          <p className="text-[10px] text-[#444] uppercase tracking-widest max-w-sm">
            Confronta Questor (físico) com Vulcano (societário) — Saldo Anterior, Débito, Crédito e Saldo Final por conta
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
