import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle,
  ArrowUpRight, ArrowDownRight, TrendingUp, Building2, ChevronDown, ChevronUp
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts';

const API_BASE = "http://127.0.0.1:8000";
const fmt = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);
const fmtPct = (v) => `${(+v || 0).toFixed(1)}%`;

const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// ── Gauge de % auditoria ─────────────────────────────────────────────────────
function AuditGauge({ pct, label }) {
  const clamped = Math.min(100, Math.max(0, pct));
  const color = clamped >= 95 ? '#34c759' : clamped >= 80 ? '#ffcc00' : '#ff4d00';
  const r = 40, cx = 50, cy = 50;
  const circ = 2 * Math.PI * r;
  const dash = (clamped / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="110" height="110" viewBox="0 0 100 100">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e1e1e" strokeWidth="10"/>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color}
          strokeWidth="10" strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round" transform="rotate(-90 50 50)"/>
        <text x="50" y="46" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold" fontFamily="monospace">{clamped.toFixed(0)}%</text>
        <text x="50" y="62" textAnchor="middle" fill="#555" fontSize="8" fontFamily="sans-serif" textTransform="uppercase">AUDITADO</text>
      </svg>
      <p className="text-[9px] font-black uppercase tracking-widest text-[#666]">{label}</p>
    </div>
  );
}

// ── Card de divergência por empreendimento ───────────────────────────────────
function EmpCard({ emp }) {
  const [open, setOpen] = useState(false);
  const fisicTotal  = (emp.contas_fisicas  || []).reduce((s, c) => s + (c.saldo_final || 0), 0);
  const virtualTotal = (emp.contas_virtuais || []).reduce((s, c) => s + (c.saldo_final || 0), 0);
  const diff  = virtualTotal - fisicTotal;
  const adh   = fisicTotal !== 0 ? Math.min(100, (1 - Math.abs(diff) / Math.abs(fisicTotal)) * 100) : 0;
  const ok    = Math.abs(diff) < 1000;

  return (
    <div className={`bg-[#111] border rounded-sm ${ok ? 'border-[#1e1e1e]' : 'border-[#ff4d00]/30'} shadow-lg`}>
      <div className="px-5 py-4 flex items-center gap-4 cursor-pointer" onClick={() => setOpen(o => !o)}>
        {/* Status dot */}
        {ok ? <CheckCircle2 size={16} className="text-[#34c759] shrink-0"/> : <XCircle size={16} className="text-[#ff4d00] shrink-0"/>}
        
        <div className="flex-1 min-w-0">
          <p className="text-white font-black text-sm truncate">{emp.empreendimento_nome}</p>
          <p className="text-[9px] font-bold uppercase tracking-widest text-[#555]">ID {emp.empreendimento_id}</p>
        </div>

        <div className="text-right">
          <p className="text-[9px] font-bold uppercase tracking-widest text-[#555] mb-0.5">Físico (Questor)</p>
          <p className="font-mono text-sm text-[#aaa]">{fmt(fisicTotal)}</p>
        </div>
        <div className="text-right">
          <p className="text-[9px] font-bold uppercase tracking-widest text-[#555] mb-0.5">Societário (Vulcano)</p>
          <p className="font-mono text-sm text-[#aaa]">{fmt(virtualTotal)}</p>
        </div>
        <div className="text-right">
          <p className="text-[9px] font-bold uppercase tracking-widest text-[#555] mb-0.5">Divergência</p>
          <p className={`font-mono font-bold text-sm ${ok ? 'text-[#34c759]' : 'text-[#ff4d00]'}`}>
            {diff >= 0 ? '+' : ''}{fmt(diff)}
          </p>
        </div>
        <div className="w-16 text-center">
          <p className="text-[9px] font-bold uppercase tracking-widest text-[#555] mb-1">Aderência</p>
          <div className="w-full bg-[#1a1a1a] rounded-full h-1.5">
            <div className="h-1.5 rounded-full" style={{ width: `${adh}%`, background: ok ? '#34c759' : '#ff4d00' }}/>
          </div>
          <p className="text-[10px] font-mono font-bold mt-0.5" style={{ color: ok ? '#34c759' : '#ff4d00' }}>{adh.toFixed(0)}%</p>
        </div>
        {open ? <ChevronUp size={14} className="text-[#555]"/> : <ChevronDown size={14} className="text-[#555]"/>}
      </div>

      {open && (
        <div className="border-t border-[#1a1a1a] px-5 py-4 grid grid-cols-2 gap-6">
          {/* Contas físicas */}
          <div>
            <p className="text-[9px] font-black uppercase tracking-widest text-[#ff4d00] mb-3">Contas Físicas (Questor)</p>
            <div className="flex flex-col gap-1">
              {(emp.contas_fisicas || []).slice(0, 15).map(c => (
                <div key={c.conta} className="flex justify-between items-center py-1 border-b border-[#171717]">
                  <span className="font-mono text-[10px] text-[#ff4d00] mr-2">{c.conta}</span>
                  <span className="text-[10px] text-[#666] flex-1 truncate">{c.nome}</span>
                  <span className="font-mono text-[10px] text-[#aaa] ml-2">{fmt(c.saldo_final)}</span>
                </div>
              ))}
            </div>
          </div>
          {/* Contas virtuais societárias */}
          <div>
            <p className="text-[9px] font-black uppercase tracking-widest text-[#a259ff] mb-3">Lançamentos Societários (Vulcano)</p>
            <div className="flex flex-col gap-1">
              {(emp.contas_virtuais || []).slice(0, 15).map(c => (
                <div key={c.conta} className="flex justify-between items-center py-1 border-b border-[#171717]">
                  <span className="font-mono text-[10px] text-[#a259ff] mr-2">{c.conta}</span>
                  <span className="text-[10px] text-[#666] flex-1 truncate">{c.nome}</span>
                  <span className="font-mono text-[10px] text-[#aaa] ml-2">{fmt(c.saldo_final)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── MAIN ────────────────────────────────────────────────────────────────────
export const AuditoriaERPView = ({ selectedEmpresa }) => {
  const now = new Date();
  const [mes, setMes] = useState(now.getMonth() + 1);
  const [ano, setAno] = useState(now.getFullYear());
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = () => {
    if (!selectedEmpresa) return;
    setLoading(true);
    setError('');
    fetch(`${API_BASE}/api/questor/contabilizacoes?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}`)
      .then(r => r.json())
      .then(j => { setData(j.data || []); setLoading(false); })
      .catch(e => { setError(String(e)); setLoading(false); });
  };

  useEffect(() => { fetchData(); }, [selectedEmpresa, mes, ano]);

  // Métricas globais
  const metrics = useMemo(() => {
    let totalFisico = 0, totalVirtual = 0, empOk = 0;
    data.forEach(emp => {
      const f = (emp.contas_fisicas  || []).reduce((s, c) => s + (c.saldo_final || 0), 0);
      const v = (emp.contas_virtuais || []).reduce((s, c) => s + (c.saldo_final || 0), 0);
      totalFisico  += f;
      totalVirtual += v;
      if (Math.abs(v - f) < 1000) empOk++;
    });
    const diff = totalVirtual - totalFisico;
    const adh  = totalFisico !== 0 ? Math.min(100, (1 - Math.abs(diff) / Math.abs(totalFisico)) * 100) : 0;
    return { totalFisico, totalVirtual, diff, adh, empOk, total: data.length };
  }, [data]);

  // Dados para gráfico de barras comparativo
  const chartData = useMemo(() => {
    return data.map(emp => ({
      name: (emp.empreendimento_nome || '').substring(0, 18),
      Físico: +(((emp.contas_fisicas  || []).reduce((s, c) => s + (c.saldo_final || 0), 0)) / 1000).toFixed(0),
      Societário: +(((emp.contas_virtuais || []).reduce((s, c) => s + (c.saldo_final || 0), 0)) / 1000).toFixed(0),
    }));
  }, [data]);

  const empsNok = data.filter(emp => {
    const f = (emp.contas_fisicas  || []).reduce((s, c) => s + (c.saldo_final || 0), 0);
    const v = (emp.contas_virtuais || []).reduce((s, c) => s + (c.saldo_final || 0), 0);
    return Math.abs(v - f) >= 1000;
  });

  return (
    <div className="flex flex-col gap-6 pb-10 text-[#e5e2e1] animate-in fade-in">
      {/* Header */}
      <div className="border-b border-[#222] pb-5">
        <h2 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3 mb-1">
          <ShieldCheck className="text-[#ff4d00]" size={38}/> Auditoria ERP
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#555] font-black">Confronto Físico (Questor) × Societário (Vulcano IFRS15)</p>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="bg-[#111] border border-[#222] rounded p-3 flex flex-col gap-1 focus-within:border-[#ff4d00]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Mês</span>
          <select value={mes} onChange={e => setMes(+e.target.value)}
            className="bg-transparent outline-none text-[#ccc] text-xs font-bold">
            {MESES.map((m,i) => <option key={i} value={i+1}>{m}</option>)}
          </select>
        </div>
        <div className="bg-[#111] border border-[#222] rounded p-3 flex flex-col gap-1 focus-within:border-[#ff4d00]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Ano</span>
          <select value={ano} onChange={e => setAno(+e.target.value)}
            className="bg-transparent outline-none text-[#ccc] text-xs font-bold">
            {[2022,2023,2024,2025,2026].map(y => <option key={y}>{y}</option>)}
          </select>
        </div>
        <button onClick={fetchData}
          className="px-5 py-2.5 text-[9px] font-black uppercase tracking-widest border border-[#333] hover:border-[#ff4d00] hover:text-[#ff4d00] text-[#888] rounded flex items-center gap-2 ml-auto">
          <Zap size={12}/> Auditar
        </button>
      </div>

      {/* Loading / Error */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-16">
          <Zap className="animate-spin text-[#ff4d00]" size={28}/>
          <span className="text-xs font-black uppercase tracking-[0.2em] text-[#555]">Confrontando Registros...</span>
        </div>
      )}
      {error && (
        <div className="bg-[#ff4d00]/10 border border-[#ff4d00]/30 rounded p-4 flex items-center gap-3">
          <AlertTriangle size={18} className="text-[#ff4d00] shrink-0"/>
          <p className="text-sm text-[#ff4d00] font-mono">{error}</p>
        </div>
      )}

      {!loading && data.length > 0 && (
        <>
          {/* Painel de métricas executivas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Gauge */}
            <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-5 flex flex-col items-center justify-center gap-2">
              <AuditGauge pct={metrics.adh} label="Status de Conciliação"/>
              <p className="text-[9px] font-black uppercase tracking-widest text-[#555]">
                {metrics.empOk}/{metrics.total} obras OK
              </p>
            </div>
            {/* Métricas */}
            {[
              { label: 'Total Físico (Questor)', val: metrics.totalFisico, cor: '#ff4d00' },
              { label: 'Total Societário (Vulcano)', val: metrics.totalVirtual, cor: '#a259ff' },
              { label: 'Divergência Global', val: metrics.diff, cor: Math.abs(metrics.diff) < 1000 ? '#34c759' : '#ff4d00' },
            ].map(m => (
              <div key={m.label} className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-5 flex flex-col justify-between">
                <p className="text-[9px] font-black uppercase tracking-widest text-[#555] mb-2">{m.label}</p>
                <p className="text-2xl font-black font-mono" style={{ color: m.cor }}>{fmt(m.val)}</p>
              </div>
            ))}
          </div>

          {/* Gráfico comparativo */}
          {chartData.length > 0 && (
            <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-5">
              <p className="text-[10px] font-black uppercase tracking-widest text-[#555] mb-4">Confronto por Empreendimento (R$ Mil)</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} barCategoryGap="25%">
                  <CartesianGrid strokeDasharray="2 4" stroke="#1e1e1e"/>
                  <XAxis dataKey="name" tick={{ fill: '#555', fontSize: 9 }} angle={-25} textAnchor="end" height={50}/>
                  <YAxis tick={{ fill: '#555', fontSize: 9 }}/>
                  <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', color: '#fff', fontSize: 11 }}
                    formatter={(v) => [`R$ ${v}k`, '']}/>
                  <Legend wrapperStyle={{ fontSize: 10, color: '#888', paddingTop: 8 }}/>
                  <Bar dataKey="Físico" fill="#ff4d00" radius={[2,2,0,0]}/>
                  <Bar dataKey="Societário" fill="#a259ff" radius={[2,2,0,0]}/>
                  <ReferenceLine y={0} stroke="#333"/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Alertas críticos */}
          {empsNok.length > 0 && (
            <div className="bg-[#ff4d00]/5 border border-[#ff4d00]/20 rounded p-4">
              <div className="flex items-center gap-3 mb-3">
                <AlertTriangle size={16} className="text-[#ff4d00]"/>
                <p className="text-[10px] font-black uppercase tracking-widest text-[#ff4d00]">
                  {empsNok.length} empreendimento{empsNok.length > 1 ? 's' : ''} com divergência acima de R$ 1.000
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {empsNok.map(e => (
                  <span key={e.empreendimento_id} className="bg-[#ff4d00]/10 text-[#ff4d00] text-[9px] font-black uppercase tracking-widest px-3 py-1 rounded">
                    {e.empreendimento_nome}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Listagem por empreendimento */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-[#555] mb-3">
              Detalhamento por Empreendimento ({data.length} obra{data.length !== 1 ? 's' : ''})
            </p>
            <div className="flex flex-col gap-3">
              {data.map(emp => <EmpCard key={emp.empreendimento_id} emp={emp}/>)}
            </div>
          </div>
        </>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="text-center py-16 text-[#555]">
          <ShieldCheck size={40} className="mx-auto mb-4 opacity-30"/>
          <p className="font-black uppercase tracking-widest text-[#444] text-sm">Nenhum dado para {MESES[mes-1]}/{ano}</p>
          <p className="text-[10px] text-[#333] uppercase tracking-widest mt-1">Selecione uma empresa e clique em Auditar</p>
        </div>
      )}
    </div>
  );
};
