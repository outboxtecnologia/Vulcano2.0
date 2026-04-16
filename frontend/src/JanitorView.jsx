import React, { useState, useEffect, useCallback } from 'react';
import { Trash2, Zap, Activity, HardDrive, RefreshCw, Shield, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, MoveRight } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const fmt      = (v) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v || 0);
const fmtKB    = (v) => v >= 1024 ? `${(v / 1024).toFixed(1)} MB` : `${v.toFixed(0)} KB`;

// â”€â”€ Cores por latência â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const latencyColor = (ms) => {
  if (!ms || ms < 200)  return '#34c759';
  if (ms < 800)  return '#ffcc00';
  if (ms < 2000) return '#ff9f0a';
  return '#ff4d00';
};

const riskColor = (risk) => ({
  safe_delete: '#34c759',
  review:      '#ffcc00',
  keep:        '#007aff',
}[risk] || '#888');

const riskLabel = (risk) => ({
  safe_delete: 'Lixo seguro',
  review:      'Revisar',
  keep:        'Manter',
}[risk] || risk);

const categoriaLabel = (cat) => ({
  SCRIPT_PATCH:   'ðŸ©¹ Script de Patch',
  SCRIPT_FIX:     'ðŸ”§ Script Fix',
  SCRIPT_UPDATE:  'ðŸ“¦ Script Update',
  SCRIPT_RECOVER: 'ðŸ”„ Script Recover',
  DEBUG_SCRIPT:   'ðŸ› Debug Script',
  TMP_FILE:       '⏱ Temporário',
  LOG_FILE:       'ðŸ“„ Log/TXT',
  DUMP_JSON:      'ðŸ“Š Dump JSON',
  DUMP_SCRIPT:    'ðŸ—‚ Script Dump',
}[cat] || cat);

// â”€â”€ Card de KPI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function KpiCard({ icon, label, value, sub, color = 'var(--v-accent)' }) {
  return (
    <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] p-4 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span style={{ color }}>{icon}</span>
        <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">{label}</span>
      </div>
      <div className="font-mono text-2xl font-black" style={{ color }}>{value}</div>
      {sub && <div className="text-[9px] text-[var(--v-text-faint)] font-bold">{sub}</div>}
    </div>
  );
}

// â”€â”€ Barra de latência â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function LatencyBar({ ms, max }) {
  const pct = Math.min(100, (ms / Math.max(max, 1)) * 100);
  const color = latencyColor(ms);
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-1.5 bg-[var(--v-hover)] rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="font-mono text-[10px] font-black w-16 text-right" style={{ color }}>
        {ms?.toFixed(0)}ms
      </span>
    </div>
  );
}

// â”€â”€ Painel de Performance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function PerformancePanel({ data }) {
  const endpoints = data?.performance?.endpoints || [];
  const maxMs = Math.max(...endpoints.map(e => e.p95_ms || 0), 1);
  const [janela, setJanela] = useState(24);

  return (
    <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--v-border)] bg-[#007aff]/5">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-[#007aff]" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[#007aff]">
            Performance por Endpoint (P50/P95/P99)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] text-[var(--v-text-faint)] font-bold">Janela:</span>
          {[1, 6, 24, 72].map(h => (
            <button key={h} onClick={() => setJanela(h)}
              className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest transition-all border ${
                janela === h ? 'bg-[#007aff]/20 border-[#007aff]/50 text-[#007aff]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)]'
              }`}>{h}h</button>
          ))}
        </div>
      </div>

      {endpoints.length === 0 ? (
        <div className="p-8 text-center text-[var(--v-text-faint)] text-[10px] font-bold uppercase tracking-widest">
          Aguardando primeiras métricas... (faça algumas requests para popular)
        </div>
      ) : (
        <div className="overflow-auto max-h-[400px] custom-scrollbar">
          <table className="w-full text-left border-collapse text-[10px]">
            <thead className="sticky top-0 bg-[var(--v-deep)] border-b border-[var(--v-border)]">
              <tr>
                <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest">Endpoint</th>
                <th className="p-2 text-center text-[var(--v-text-faint)] font-black uppercase tracking-widest w-16">Calls</th>
                <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest w-48">P95 Latência</th>
                <th className="p-2 text-right text-[var(--v-text-faint)] font-black uppercase tracking-widest w-20">P50</th>
                <th className="p-2 text-right text-[var(--v-text-faint)] font-black uppercase tracking-widest w-20">P99</th>
                <th className="p-2 text-center text-[var(--v-text-faint)] font-black uppercase tracking-widest w-16">Erros</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map((e, i) => (
                <tr key={i} className="border-b border-[var(--v-bg)] hover:bg-[var(--v-hover)]/40 transition-colors">
                  <td className="p-2">
                    <div className="font-mono text-[var(--v-text-bold)] font-black text-[10px] truncate max-w-[280px]">{e.path}</div>
                    <div className="text-[8px] text-[var(--v-text-faint)]">{e.method}</div>
                  </td>
                  <td className="p-2 text-center font-mono font-black text-[var(--v-text)]">{fmt(e.n_calls)}</td>
                  <td className="p-2"><LatencyBar ms={e.p95_ms} max={maxMs} /></td>
                  <td className="p-2 text-right font-mono text-[10px]" style={{ color: latencyColor(e.p50_ms) }}>{e.p50_ms?.toFixed(0)}ms</td>
                  <td className="p-2 text-right font-mono text-[10px]" style={{ color: latencyColor(e.p99_ms) }}>{e.p99_ms?.toFixed(0)}ms</td>
                  <td className="p-2 text-center">
                    {e.n_errors > 0
                      ? <span className="text-[var(--v-accent)] font-black">{e.n_errors}</span>
                      : <span className="text-[#333]">â€”</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// â”€â”€ Painel de Disco â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function DiskPanel({ onRefresh }) {
  const [diskData,   setDiskData]   = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [selected,   setSelected]   = useState(new Set());
  const [quarentando, setQuarentando] = useState(false);
  const [result,     setResult]     = useState(null);
  const [filterRisk, setFilterRisk] = useState('all');
  const [filterCat,  setFilterCat]  = useState('all');
  const [expandCats, setExpandCats] = useState({});

  const fetchDisk = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/janitor/disk`);
      const d = await r.json();
      setDiskData(d);
      setSelected(new Set());
      setResult(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDisk(); }, [fetchDisk]);

  const candidatos = diskData?.candidatos || [];
  const filtered = candidatos.filter(c =>
    (filterRisk === 'all' || c.risk === filterRisk) &&
    (filterCat  === 'all' || c.categoria === filterCat)
  );

  const cats = [...new Set(candidatos.map(c => c.categoria))].sort();
  const totalSelecionado = [...selected].reduce((s, p) => {
    const c = candidatos.find(x => x.path === p);
    return s + (c?.size_kb || 0);
  }, 0);

  const toggleSelect = (path) => {
    setSelected(prev => {
      const n = new Set(prev);
      n.has(path) ? n.delete(path) : n.add(path);
      return n;
    });
  };

  const selectAll = () => setSelected(new Set(filtered.map(c => c.path)));
  const clearAll  = () => setSelected(new Set());
  const selectAllSafe = () => setSelected(new Set(filtered.filter(c => c.risk === 'safe_delete').map(c => c.path)));

  const moverParaQuarentena = async () => {
    if (selected.size === 0) return;
    setQuarentando(true);
    try {
      const r = await fetch(`${API_BASE}/api/janitor/quarantine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paths: [...selected] }),
      });
      const d = await r.json();
      setResult(d);
      setSelected(new Set());
      setTimeout(fetchDisk, 1000);
    } catch (e) {
      console.error(e);
    } finally {
      setQuarentando(false);
    }
  };

  if (diskData?.status === 'pending') return (
    <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] p-8 text-center">
      <RefreshCw className="animate-spin text-[var(--v-text-faint)] mx-auto mb-3" size={20} />
      <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">
        Scanner de disco inicializando (aguarde ~5s após startup)...
      </p>
    </div>
  );

  return (
    <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--v-border)] bg-[var(--v-accent)]/5 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <HardDrive size={14} className="text-[var(--v-accent)]" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-accent)]">
            Arquivos Residuais â€” {diskData?.total_arquivos || 0} candidatos, {fmtKB(diskData?.total_size_kb || 0)}
          </span>
          <span className="text-[9px] text-[var(--v-text-faint)] ml-2">Gerado: {diskData?.gerado_em?.slice(0, 16)}</span>
        </div>
        <button onClick={fetchDisk} disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--v-hover)] border border-[var(--v-border)] rounded text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-colors">
          <RefreshCw size={10} className={loading ? 'animate-spin' : ''} /> Reescanear
        </button>
      </div>

      {/* Filtros */}
      <div className="px-4 py-2 border-b border-[var(--v-border)] flex flex-wrap gap-2 items-center">
        <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Risco:</span>
        {['all', 'safe_delete', 'review'].map(r => (
          <button key={r} onClick={() => setFilterRisk(r)}
            className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest border transition-all ${
              filterRisk === r ? 'bg-[var(--v-accent)]/20 border-[var(--v-accent)]/50 text-[var(--v-accent)]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)]'
            }`}>
            {r === 'all' ? 'Todos' : riskLabel(r)}
          </button>
        ))}
        <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] ml-2">Categ:</span>
        <select value={filterCat} onChange={e => setFilterCat(e.target.value)}
          className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-2 py-0.5 text-[8px] font-bold text-[var(--v-text)] outline-none">
          <option value="all">Todas</option>
          {cats.map(c => <option key={c} value={c}>{categoriaLabel(c)}</option>)}
        </select>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <button onClick={selectAllSafe}
            className="px-2 py-0.5 bg-[#34c759]/10 border border-[#34c759]/30 rounded text-[8px] font-black uppercase tracking-widest text-[#34c759] hover:bg-[#34c759]/20 transition-all">
            âœ“ Selecionar Lixo Seguro ({filtered.filter(c => c.risk === 'safe_delete').length})
          </button>
          <button onClick={selectAll}
            className="px-2 py-0.5 bg-[var(--v-hover)] border border-[var(--v-border)] rounded text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-all">
            Tudo
          </button>
          <button onClick={clearAll}
            className="px-2 py-0.5 bg-[var(--v-hover)] border border-[var(--v-border)] rounded text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-all">
            Limpar
          </button>
        </div>
      </div>

      {/* Lista */}
      <div className="overflow-auto max-h-[500px] custom-scrollbar">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-[#34c759] text-[10px] font-black uppercase tracking-widest">
            <CheckCircle2 className="mx-auto mb-2" size={24} />
            Nenhum arquivo residual encontrado com esses filtros.
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-[10px]">
            <thead className="sticky top-0 bg-[var(--v-deep)] border-b border-[var(--v-border)]">
              <tr>
                <th className="p-2 w-8">
                  <input type="checkbox"
                    checked={selected.size > 0 && filtered.every(c => selected.has(c.path))}
                    onChange={e => e.target.checked ? selectAll() : clearAll()}
                    className="accent-[var(--v-accent)]" />
                </th>
                <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest">Arquivo</th>
                <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest">Categoria</th>
                <th className="p-2 text-center text-[var(--v-text-faint)] font-black uppercase tracking-widest w-20">Risco</th>
                <th className="p-2 text-right text-[var(--v-text-faint)] font-black uppercase tracking-widest w-16">Tamanho</th>
                <th className="p-2 text-right text-[var(--v-text-faint)] font-black uppercase tracking-widest w-16">Idade</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c, i) => (
                <tr key={i}
                  onClick={() => toggleSelect(c.path)}
                  className={`border-b border-[var(--v-bg)] cursor-pointer transition-colors ${
                    selected.has(c.path) ? 'bg-[var(--v-accent)]/10' : 'hover:bg-[var(--v-hover)]/40'
                  }`}>
                  <td className="p-2">
                    <input type="checkbox" checked={selected.has(c.path)} onChange={() => {}}
                      className="accent-[var(--v-accent)]" />
                  </td>
                  <td className="p-2">
                    <span className="font-mono font-black text-[var(--v-text-bold)] text-[10px]">{c.arquivo}</span>
                  </td>
                  <td className="p-2 text-[var(--v-text-faint)]">{categoriaLabel(c.categoria)}</td>
                  <td className="p-2 text-center">
                    <span className="text-[8px] font-black px-1.5 py-0.5 rounded uppercase tracking-widest border"
                      style={{ color: riskColor(c.risk), borderColor: `${riskColor(c.risk)}40`, background: `${riskColor(c.risk)}15` }}>
                      {riskLabel(c.risk)}
                    </span>
                  </td>
                  <td className="p-2 text-right font-mono text-[var(--v-text-muted)]">{fmtKB(c.size_kb)}</td>
                  <td className="p-2 text-right text-[var(--v-text-faint)]">{c.age_days.toFixed(0)}d</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer de ação */}
      {(selected.size > 0 || result) && (
        <div className="border-t border-[var(--v-border)] px-4 py-3 bg-[var(--v-bg)] flex items-center gap-4">
          {selected.size > 0 && (
            <>
              <span className="text-[10px] font-bold text-[var(--v-text-faint)]">
                {selected.size} arquivo(s) selecionado(s) â€” {fmtKB(totalSelecionado)}
              </span>
              <button onClick={moverParaQuarentena} disabled={quarentando}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/40 rounded text-[9px] font-black uppercase tracking-widest text-[var(--v-accent)] hover:bg-[var(--v-accent)]/20 transition-all disabled:opacity-40">
                {quarentando ? <RefreshCw size={10} className="animate-spin" /> : <MoveRight size={10} />}
                {quarentando ? 'Movendo...' : 'Mover para Quarentena'}
              </button>
            </>
          )}
          {result && (
            <div className="flex items-center gap-2 text-[10px] font-bold">
              <CheckCircle2 size={12} className="text-[#34c759]" />
              <span className="text-[#34c759]">{result.movidos} arquivo(s) movidos para quarentena.</span>
              {result.erros > 0 && <span className="text-[var(--v-accent)]">{result.erros} erro(s).</span>}
              <span className="text-[var(--v-text-faint)] text-[8px]">ðŸ“ {result.quarentena}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// â”€â”€ View Principal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const JanitorView = () => {
  const [reportData, setReportData] = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/janitor/report?janela_horas=24&top_n=25`);
      const d = await r.json();
      setReportData(d);
      setLastRefresh(new Date().toLocaleTimeString('pt-BR'));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  useEffect(() => {
    if (!autoRefresh) return;
    const t = setInterval(fetchReport, 30000);
    return () => clearInterval(t);
  }, [autoRefresh, fetchReport]);

  const cache = reportData?.cache;
  const perf  = reportData?.performance;
  const endpoints = perf?.endpoints || [];
  const slowest = endpoints[0];

  return (
    <div className="flex flex-col gap-5 pb-10 text-[var(--v-text)] animate-in fade-in">
      {/* Header */}
      <div className="border-b border-[var(--v-border)] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-[var(--v-text-bold)] flex items-center gap-3 mb-1">
          <Trash2 className="text-[var(--v-accent)]" size={36} /> Agente Janitor
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--v-text-faint)] font-black">
          SRE Autônomo â€” Performance · Limpeza · Governança
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <button onClick={fetchReport} disabled={loading}
          className="px-5 py-2 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40">
          {loading ? <RefreshCw size={12} className="animate-spin" /> : <RefreshCw size={12} />}
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
        <button onClick={() => setAutoRefresh(a => !a)}
          className={`px-4 py-2 text-[9px] font-black uppercase tracking-widest rounded border flex items-center gap-2 transition-all ${
            autoRefresh
              ? 'bg-[#34c759]/20 border-[#34c759]/50 text-[#34c759]'
              : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[#34c759]'
          }`}>
          <Zap size={12} className={autoRefresh ? 'animate-pulse' : ''} />
          {autoRefresh ? 'Auto-refresh 30s ativo' : 'Auto-refresh'}
        </button>
        {lastRefresh && (
          <span className="text-[9px] text-[var(--v-text-faint)] font-bold ml-auto">
            Ãšltima atualização: {lastRefresh}
          </span>
        )}
      </div>

      {/* KPIs */}
      {reportData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard
            icon={<Activity size={16} />}
            label="Endpoints Monitorados"
            value={perf?.total_paths || 0}
            sub={`Janela: ${perf?.janela_horas}h`}
            color="#007aff"
          />
          <KpiCard
            icon={<Zap size={16} />}
            label="Endpoint Mais Lento (P95)"
            value={slowest ? `${slowest.p95_ms?.toFixed(0)}ms` : 'â€”'}
            sub={slowest?.path?.split('/').slice(-2).join('/') || 'Sem dados ainda'}
            color={latencyColor(slowest?.p95_ms)}
          />
          <KpiCard
            icon={<Shield size={16} />}
            label="Cache Hit Rate"
            value={`${cache?.hit_rate_pct?.toFixed(0) || 0}%`}
            sub={`${cache?.valid_entries || 0} entradas válidas`}
            color={cache?.hit_rate_pct > 60 ? '#34c759' : '#ffcc00'}
          />
          <KpiCard
            icon={<HardDrive size={16} />}
            label="N+1 Queries Fixadas"
            value="3 / 14"
            sub="Endpoint venda cadastro"
            color="#34c759"
          />
        </div>
      )}

      {/* Performance Panel */}
      {reportData && <PerformancePanel data={reportData} />}

      {/* Disk Inspector */}
      <div className="flex items-center gap-2 mt-2">
        <HardDrive size={16} className="text-[var(--v-accent)]" />
        <h3 className="text-[11px] font-black uppercase tracking-widest text-[var(--v-text-bold)]">
          Inspetor de Disco â€” Arquivos Residuais
        </h3>
      </div>
      <DiskPanel />
    </div>
  );
};
