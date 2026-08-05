import React, { useState, useEffect, useCallback } from 'react';
import { Trash2, Zap, Activity, HardDrive, RefreshCw, Shield, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, MoveRight } from 'lucide-react';
import { API_BASE } from './apiBase';
const fmt      = (v) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v || 0);
const fmtKB    = (v) => v >= 1024 ? `${(v / 1024).toFixed(1)} MB` : `${v.toFixed(0)} KB`;

// ── Cores por latência ────────────────────────────────────────────────────────
const latencyColor = (ms) => {
  if (!ms || ms < 200)  return 'var(--v-ok)';
  if (ms < 800)  return 'var(--v-warn-hi)';
  if (ms < 2000) return 'var(--v-warn)';
  return 'var(--v-accent)';
};

const riskColor = (risk) => ({
  safe_delete: 'var(--v-ok)',
  review:      'var(--v-warn-hi)',
  keep:        'var(--v-info)',
}[risk] || 'var(--v-text-muted)');

const riskLabel = (risk) => ({
  safe_delete: 'Lixo seguro',
  review:      'Revisar',
  keep:        'Manter',
}[risk] || risk);

const categoriaLabel = (cat) => ({
  SCRIPT_PATCH:   '🩹 Script de Patch',
  SCRIPT_FIX:     '🔧 Script Fix',
  SCRIPT_UPDATE:  '📦 Script Update',
  SCRIPT_RECOVER: '🔄 Script Recover',
  DEBUG_SCRIPT:   '🐛 Debug Script',
  TMP_FILE:       '⏱ Temporário',
  LOG_FILE:       '📄 Log/TXT',
  DUMP_JSON:      '📊 Dump JSON',
  DUMP_SCRIPT:    '🗂 Script Dump',
}[cat] || cat);

// ── Card de KPI ───────────────────────────────────────────────────────────────
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

// ── Barra de latência ─────────────────────────────────────────────────────────
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

// ── Painel de Performance ────────────────────────────────────────────────────
function PerformancePanel({ data }) {
  const endpoints = data?.performance?.endpoints || [];
  const maxMs = Math.max(...endpoints.map(e => e.p95_ms || 0), 1);
  const [janela, setJanela] = useState(24);

  return (
    <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--v-border)] bg-[var(--v-info)]/5">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-[var(--v-info)]" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-info)]">
            Performance por Endpoint (P50/P95/P99)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] text-[var(--v-text-faint)] font-bold">Janela:</span>
          {[1, 6, 24, 72].map(h => (
            <button key={h} onClick={() => setJanela(h)}
              className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest transition-all border ${
                janela === h ? 'bg-[var(--v-info)]/20 border-[var(--v-info)]/50 text-[var(--v-info)]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)]'
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
                <tr key={i} className="border-b border-[var(--v-bg)] hover:bg-[rgb(var(--v-hover-rgb)_/_0.4)] transition-colors">
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
                      : <span className="text-[var(--v-text-ghost)]">—</span>
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

// ── Painel de Disco ───────────────────────────────────────────────────────────
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
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--v-border)] bg-[rgb(var(--v-accent-rgb)_/_0.05)] flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <HardDrive size={14} className="text-[var(--v-accent)]" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-accent)]">
            Arquivos Residuais — {diskData?.total_arquivos || 0} candidatos, {fmtKB(diskData?.total_size_kb || 0)}
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
              filterRisk === r ? 'bg-[rgb(var(--v-accent-rgb)_/_0.2)] border-[rgb(var(--v-accent-rgb)_/_0.5)] text-[var(--v-accent)]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)]'
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
            className="px-2 py-0.5 bg-[var(--v-ok)]/10 border border-[var(--v-ok)]/30 rounded text-[8px] font-black uppercase tracking-widest text-[var(--v-ok)] hover:bg-[var(--v-ok)]/20 transition-all">
            ✓ Selecionar Lixo Seguro ({filtered.filter(c => c.risk === 'safe_delete').length})
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
          <div className="p-8 text-center text-[var(--v-ok)] text-[10px] font-black uppercase tracking-widest">
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
                    selected.has(c.path) ? 'bg-[rgb(var(--v-accent-rgb)_/_0.1)]' : 'hover:bg-[rgb(var(--v-hover-rgb)_/_0.4)]'
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
                {selected.size} arquivo(s) selecionado(s) — {fmtKB(totalSelecionado)}
              </span>
              <button onClick={moverParaQuarentena} disabled={quarentando}
                className="flex items-center gap-2 px-4 py-2 bg-[rgb(var(--v-accent-rgb)_/_0.1)] border border-[rgb(var(--v-accent-rgb)_/_0.4)] rounded text-[9px] font-black uppercase tracking-widest text-[var(--v-accent)] hover:bg-[rgb(var(--v-accent-rgb)_/_0.2)] transition-all disabled:opacity-40">
                {/* Rotulo em <span>: texto solto irmao de icone condicional vira no de referencia
                    do insertBefore e quebra o commit do React se algo (tradutor de pagina) tiver
                    embrulhado o texto. */}
                {quarentando ? <RefreshCw size={10} className="animate-spin" /> : <MoveRight size={10} />}
                <span>{quarentando ? 'Movendo...' : 'Mover para Quarentena'}</span>
              </button>
            </>
          )}
          {result && (
            <div className="flex items-center gap-2 text-[10px] font-bold">
              <CheckCircle2 size={12} className="text-[var(--v-ok)]" />
              <span className="text-[var(--v-ok)]">{result.movidos} arquivo(s) movidos para quarentena.</span>
              {result.erros > 0 && <span className="text-[var(--v-accent)]">{result.erros} erro(s).</span>}
              <span className="text-[var(--v-text-faint)] text-[8px]">📁 {result.quarentena}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── View Principal ────────────────────────────────────────────────────────────
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
          SRE Autônomo — Performance · Limpeza · Governança
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <button onClick={fetchReport} disabled={loading}
          className="px-5 py-2 bg-[var(--v-accent)] text-[var(--v-text-inv)] text-[9px] font-black uppercase tracking-widest rounded hover:bg-[var(--v-hover)] transition-all flex items-center gap-2 disabled:opacity-40">
          {loading ? <RefreshCw size={12} className="animate-spin" /> : <RefreshCw size={12} />}
          <span>{loading ? 'Atualizando...' : 'Atualizar'}</span>
        </button>
        <button onClick={() => setAutoRefresh(a => !a)}
          className={`px-4 py-2 text-[9px] font-black uppercase tracking-widest rounded border flex items-center gap-2 transition-all ${
            autoRefresh
              ? 'bg-[var(--v-ok)]/20 border-[var(--v-ok)]/50 text-[var(--v-ok)]'
              : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-ok)]'
          }`}>
          <Zap size={12} className={autoRefresh ? 'animate-pulse' : ''} />
          {autoRefresh ? 'Auto-refresh 30s ativo' : 'Auto-refresh'}
        </button>
        {lastRefresh && (
          <span className="text-[9px] text-[var(--v-text-faint)] font-bold ml-auto">
            Última atualização: {lastRefresh}
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
            color="var(--v-info)"
          />
          <KpiCard
            icon={<Zap size={16} />}
            label="Endpoint Mais Lento (P95)"
            value={slowest ? `${slowest.p95_ms?.toFixed(0)}ms` : '—'}
            sub={slowest?.path?.split('/').slice(-2).join('/') || 'Sem dados ainda'}
            color={latencyColor(slowest?.p95_ms)}
          />
          <KpiCard
            icon={<Shield size={16} />}
            label="Cache Hit Rate"
            value={`${cache?.hit_rate_pct?.toFixed(0) || 0}%`}
            sub={`${cache?.valid_entries || 0} entradas válidas`}
            color={cache?.hit_rate_pct > 60 ? 'var(--v-ok)' : 'var(--v-warn-hi)'}
          />
          <KpiCard
            icon={<HardDrive size={16} />}
            label="N+1 Queries Fixadas"
            value="3 / 14"
            sub="Endpoint venda cadastro"
            color="var(--v-ok)"
          />
        </div>
      )}

      {/* Performance Panel */}
      {reportData && <PerformancePanel data={reportData} />}

      {/* Disk Inspector */}
      <div className="flex items-center gap-2 mt-2">
        <HardDrive size={16} className="text-[var(--v-accent)]" />
        <h3 className="text-[11px] font-black uppercase tracking-widest text-[var(--v-text-bold)]">
          Inspetor de Disco — Arquivos Residuais
        </h3>
      </div>
      <DiskPanel />
    </div>
  );
};
