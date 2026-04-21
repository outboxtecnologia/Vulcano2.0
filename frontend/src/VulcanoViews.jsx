import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
    Download, RefreshCw, Upload, Play, CheckCircle2, CheckCircle, ChevronDown, Layers, Activity,
    Database, TableProperties, Fingerprint, TrendingUp, Search, X, Maximize2, RotateCcw,
    Zap, Link as LinkIcon, Cpu, AlertCircle, FileText, CheckSquare, MessageSquare, Plus, PlusCircle, PenTool, Hash, Filter,
    LayoutGrid, History, ListFilter, ShoppingCart, Users, DollarSign, Building2, Loader2, ShieldAlert,
    UploadCloud, Send, Save, Trash2, Code, FileSpreadsheet, Minimize, Maximize, Sparkles, ChevronUp, Lock
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar,
  PieChart, Pie, Cell, Legend
} from 'recharts';




const API_BASE = "http://127.0.0.1:8000";

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const DashboardMeta = ({ selectedEmpresa }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [dataIniFilter, setDataIniFilter] = useState(`${new Date().getFullYear()}-01`);
    const [dataFimFilter, setDataFimFilter] = useState('');
    const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
    const [expandedRow, setExpandedRow] = useState(null);
    const [fetchTrigger, setFetchTrigger] = useState(0);

    const isFiltered = Boolean(dataIniFilter || dataFimFilter);

    useEffect(() => {
        if (!selectedEmpresa) return;
        setLoading(true);
        setError(null);

        // Fetching the vectorized Pandas data (Limited to filters)
        fetch(`${API_BASE}/api/receitas-caixa?empresa_id=${selectedEmpresa}${dataIniFilter ? `&data_ini=${dataIniFilter}` : ''}${dataFimFilter ? `&data_fim=${dataFimFilter}` : ''}`)
            .then(res => {
                if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
                return res.json();
            })
            .then(json => {
                setData(json);
                setLoading(false);
            })
            .catch(err => {
                console.error("Dashboard Fetch Error:", err);
                setError(err.message);
                setLoading(false);
            });
    }, [selectedEmpresa, fetchTrigger]);

    const stats = useMemo(() => {
        if (!data || !data.dashboard_meta) return null;
        // Totalize meta for all enterprises in the result
        const metaValues = Object.values(data.dashboard_meta);
        return {
            vgv: metaValues.reduce((acc, curr) => acc + (curr.vgv || 0), 0),
            receita_caixa: metaValues.reduce((acc, curr) => acc + (isFiltered ? curr.caixa_mes : curr.caixa_acumulado || 0), 0),
            receita_soc: metaValues.reduce((acc, curr) => acc + (isFiltered ? curr.receita_soc_mes : curr.receita_societaria || 0), 0),
            tributos_caixa: metaValues.reduce((acc, curr) => acc + (isFiltered ? curr.tributos_caixa_mes : curr.tributos_caixa_acumulado || 0), 0),
            tributos_soc: metaValues.reduce((acc, curr) => acc + (isFiltered ? curr.tributos_soc_mes : curr.tributos_soc_acumulado || 0), 0),
            unidades_count: metaValues.reduce((acc, curr) => acc + (curr.unidades?.length || 0), 0)
        };
    }, [data, isFiltered]);

    const chartData = useMemo(() => {
        if (!data || !data.dashboard_timeline) return [];
        return data.dashboard_timeline.map(row => ({
            period: row.periodo,
            caixa: row.caixa,
            soc: row.caixa * 0.9, // Estimated for visualization on historical timeline
            trib: row.trib
        })).sort((a, b) => a.period.localeCompare(b.period));
    }, [data]);

    const filteredMeta = useMemo(() => {
        if (!data || !data.dashboard_meta) return [];
        let entries = Object.entries(data.dashboard_meta);
        if (empreendimentoFilter) {
            entries = entries.filter(([name]) => name.toLowerCase().includes(empreendimentoFilter.toLowerCase()));
        }
        return entries;
    }, [data, empreendimentoFilter]);

    if (loading) return (
        <div className="flex-1 flex flex-col items-center justify-center p-12 space-y-4">
            <RefreshCw className="animate-spin text-[var(--v-accent)]" size={48} />
            <p className="text-[10px] uppercase font-bold tracking-[0.3em] text-[var(--v-text-muted)]">Processando Vetorização Pandas...</p>
        </div>
    );

    if (error) return (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-[var(--v-error)]">
            <AlertCircle size={48} className="mb-4" />
            <h3 className="text-xl font-bold uppercase mb-2">Falha na Sincronização</h3>
            <p className="text-sm opacity-70 mb-6">{error}</p>
            <button 
                onClick={() => window.location.reload()}
                className="bg-[var(--v-error)] text-[var(--v-text-bold)] px-6 py-2 rounded-[var(--v-radius)] font-bold uppercase text-[10px] tracking-widest"
            >
                Tentar Novamente
            </button>
        </div>
    );

    if (!stats) return (
        <div className="flex-1 flex items-center justify-center p-12 text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-xs">
            Nenhum dado financeiro localizado para esta competência.
        </div>
    );

    return (
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8 animate-in fade-in duration-700">
            {/* Filter Bar */}
            <div className="magma-card p-4 flex gap-4 items-end flex-wrap">
                <div className="flex-1 min-w-[200px]">
                    <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Pesquisar Empreendimento</label>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--v-text-muted)]" size={14} />
                        <input
                            type="text"
                            value={empreendimentoFilter}
                            onChange={(e) => setEmpreendimentoFilter(e.target.value)}
                            placeholder="Buscar res./cond. ..."
                            className="bento-input w-full pl-9"
                        />
                    </div>
                </div>
                <div>
                    <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Mês Inicial</label>
                    <input type="month" value={dataIniFilter} onChange={(e) => setDataIniFilter(e.target.value)} className="bento-input min-w-[140px]" />
                </div>
                <div>
                    <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Mês Final</label>
                    <input type="month" value={dataFimFilter} onChange={(e) => setDataFimFilter(e.target.value)} className="bento-input min-w-[140px]" />
                </div>
                <div className="flex-1 flex justify-end">
                    <button 
                        onClick={() => setFetchTrigger(prev => prev + 1)}
                        className="bg-[var(--v-accent-4)] text-black font-black uppercase tracking-widest text-[10px] px-6 py-2 rounded-[var(--v-radius)] hover:opacity-80 transition-opacity flex items-center gap-2"
                    >
                        <RefreshCw size={14} /> Atualizar Matriz
                    </button>
                </div>
            </div>

            {/* KPI Header */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { label: 'VGV Total Acumulado', val: stats.vgv, icon: <Layers />, color: 'var(--v-accent-4)' },
                    { label: 'Receita Caixa (Dinheiro)', val: stats.receita_caixa, icon: <Database />, color: 'var(--v-accent-3)' },
                    { label: 'Receita Societária (POC)', val: stats.receita_soc, icon: <TrendingUp />, color: 'var(--v-accent-5)' },
                    { label: 'Unidades Ativas', val: stats.unidades_count, icon: <LayoutGrid />, color: 'var(--v-accent-2)', noCurr: true }
                ].map((k, i) => (
                    <div key={i} className="magma-card p-6 flex flex-col justify-between group overflow-hidden">
                        <div className="flex justify-between items-start mb-4">
                            <span className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-faint)]">{k.label}</span>
                            <div style={{ color: k.color }} className="opacity-40 group-hover:opacity-100 transition-opacity">
                                {React.cloneElement(k.icon, { size: 20 })}
                            </div>
                        </div>
                        <h4 className="text-2xl font-black text-[var(--v-text-bold)] truncate">
                            {k.noCurr ? k.val : formatCurrency(k.val)}
                        </h4>
                        <div className="absolute -right-2 -bottom-2 opacity-[0.03] group-hover:scale-125 transition-transform" style={{ color: k.color }}>
                             {React.cloneElement(k.icon, { size: 80 })}
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 magma-card p-6 h-[400px] flex flex-col">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xs uppercase font-black tracking-widest text-[var(--v-text-muted)]">Evolução Financeira (Mensal)</h3>
                        <div className="flex gap-4 text-[9px] uppercase font-bold tracking-widest">
                            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-[var(--v-radius)] bg-[var(--v-accent-3)]"></span> Caixa</span>
                            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-[var(--v-radius)] bg-[var(--v-accent-5)]"></span> Societária</span>
                        </div>
                    </div>
                    <div className="flex-1">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorCaixa" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--v-accent-3)" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="var(--v-accent-3)" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorSoc" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--v-accent-5)" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="var(--v-accent-5)" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                                <XAxis dataKey="period" stroke="#444" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="#444" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => `R$${(v/1000).toFixed(0)}k`} />
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#131313', border: '1px solid #333', borderRadius: '4px' }}
                                    itemStyle={{ fontSize: '10px', textTransform: 'uppercase' }}
                                />
                                <Area type="monotone" dataKey="caixa" stroke="var(--v-accent-3)" fillOpacity={1} fill="url(#colorCaixa)" />
                                <Area type="monotone" dataKey="soc" stroke="var(--v-accent-5)" fillOpacity={1} fill="url(#colorSoc)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="magma-card p-6 h-[400px] flex flex-col">
                    <h3 className="text-xs uppercase font-black tracking-widest text-[var(--v-text-muted)] mb-6 text-center">Peso dos Impostos</h3>
                    <div className="flex-1">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={[
                                        { name: 'Caixa', value: stats.tributos_caixa },
                                        { name: 'Societário', value: stats.tributos_soc }
                                    ]}
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    <Cell fill="var(--v-accent-3)" />
                                    <Cell fill="var(--v-accent-5)" />
                                </Pie>
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#131313', border: '1px solid #333', borderRadius: '4px' }}
                                />
                                <Legend verticalAlign="bottom" align="center" iconType="circle" />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4 pt-4 border-t border-[var(--v-border)] text-center">
                        <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest mb-1">Carga Caixa Acumulada</p>
                        <h5 className="text-lg font-bold text-[var(--v-accent-3)]">{formatCurrency(stats.tributos_caixa)}</h5>
                    </div>
                </div>
            </div>

            {/* Table Detail */}
            <div className="magma-card rounded-[var(--v-radius)] overflow-hidden border border-[var(--v-border)]">
                <div className="p-4 bg-[var(--v-surface-container)] border-b border-[var(--v-border)] flex justify-between items-center">
                    <h3 className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)]">Detalhamento por Empreendimento</h3>
                    <div className="text-[9px] text-[var(--v-text-faint)] uppercase font-bold bg-black/30 px-2 py-1 rounded">Visualização Consolidada Pandas</div>
                </div>
                <div className="overflow-x-auto custom-scrollbar">
                    <table className="w-full text-left text-xs border-collapse">
                        <thead>
                            <tr className="bg-black/20 text-[var(--v-text-faint)] uppercase tracking-widest font-black border-b border-[var(--v-border)]">
                                <th className="p-4">Empreendimento</th>
                                <th className="p-4 text-right">VGV</th>
                                <th className="p-4 text-right">POC (%)</th>
                                <th className="p-4 text-right">Rec. Societária</th>
                                <th className="p-4 text-right">Rec. Caixa</th>
                                <th className="p-4 text-right">Tributos (CX)</th>
                                <th className="p-4 text-right">Tributos (SOC)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredMeta.map(([name, meta], idx) => (
                                <React.Fragment key={idx}>
                                    <tr 
                                        onClick={() => setExpandedRow(expandedRow === idx ? null : idx)}
                                        className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors cursor-pointer"
                                    >
                                        <td className="p-4 font-bold text-[var(--v-text-bold)] flex gap-2 items-center">
                                            {expandedRow === idx ? <ChevronDown size={14} /> : <Plus size={14} />} {name}
                                        </td>
                                        <td className="p-4 text-right font-mono">{formatCurrency(meta.vgv)}</td>
                                        <td className="p-4 text-right font-mono text-[var(--v-accent-5)]">{(meta.poc || 0).toFixed(2)}%</td>
                                        <td className="p-4 text-right font-mono">{formatCurrency(isFiltered ? meta.receita_soc_mes : meta.receita_societaria)}</td>
                                        <td className="p-4 text-right font-mono text-[var(--v-accent-3)]">{formatCurrency(isFiltered ? meta.caixa_mes : meta.caixa_acumulado)}</td>
                                        <td className="p-4 text-right font-mono text-[var(--v-error)]">{formatCurrency(isFiltered ? meta.tributos_caixa_mes : meta.tributos_caixa_acumulado)}</td>
                                        <td className="p-4 text-right font-mono">{formatCurrency(isFiltered ? meta.tributos_soc_mes : meta.tributos_soc_acumulado)}</td>
                                    </tr>
                                    {expandedRow === idx && meta.unidades && meta.unidades.length > 0 && (
                                        <tr className="bg-[var(--v-bg)]/50">
                                            <td colSpan={7} className="p-4">
                                                <div className="overflow-x-auto max-h-[300px] custom-scrollbar border border-[var(--v-border)]">
                                                    <table className="w-full text-left text-[10px]">
                                                        <thead className="bg-[var(--v-deep)] sticky top-0">
                                                            <tr className="text-[var(--v-text-muted)] uppercase tracking-widest font-bold">
                                                                <th className="p-2">Unidade</th>
                                                                <th className="p-2">Comprador</th>
                                                                <th className="p-2 text-right">VGV</th>
                                                                <th className="p-2 text-right">Rec. Caixa</th>
                                                                <th className="p-2 text-right">Trib. Caixa</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {meta.unidades.map((u, i) => (
                                                                <tr key={i} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)]">
                                                                    <td className="p-2">{u.unidade}</td>
                                                                    <td className="p-2 max-w-[200px] truncate">{u.comprador}</td>
                                                                    <td className="p-2 text-right font-mono text-[#aa3333]">{formatCurrency(u.vgv)}</td>
                                                                    <td className="p-2 text-right font-mono text-[var(--v-accent-3)]">{formatCurrency(u.caixa_acumulado)}</td>
                                                                    <td className="p-2 text-right font-mono text-[var(--v-error)]">{formatCurrency(u.tributos_caixa_acumulado)}</td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export const VendasView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [dataIniFilter, setDataIniFilter] = useState('');
  const [dataFimFilter, setDataFimFilter] = useState('');
  const [compradorFilter, setCompradorFilter] = useState('');
  const [unidadeFilter, setUnidadeFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [distratoModal, setDistratoModal] = useState(null);
  const [condicoesModal, setCondicoesModal] = useState(null); // { venda, payload, loading, error }
  
  // Custom form state
  const [compradores, setCompradores] = useState([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
  const [condicoes, setCondicoes] = useState([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 100;

  const openCondicoes = async (venda) => {
    setCondicoesModal({ venda, payload: null, loading: true, error: '' });
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${encodeURIComponent(venda.id)}/condicoes`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
      setCondicoesModal({ venda, payload: json, loading: false, error: '' });
    } catch (e) {
      console.error(e);
      setCondicoesModal({ venda, payload: null, loading: false, error: e.message || 'Falha ao carregar condições.' });
    }
  };

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        setData(Array.isArray(d) ? d : []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(v => v.empreendimento))].sort();
  const filtered = data.filter(v => {
    let ok = true;
    if (empreendimentoFilter && v.empreendimento !== empreendimentoFilter) ok = false;
    if (compradorFilter && !(v.cliente_nome || '').toLowerCase().includes(compradorFilter.toLowerCase())) ok = false;
    if (unidadeFilter && !(v.descricao || '').toLowerCase().includes(unidadeFilter.toLowerCase())) ok = false;
    
    if (dataIniFilter || dataFimFilter) {
      if (v.data && v.data.includes('/')) {
        const [d, m, y] = v.data.split('/');
        const vDate = new Date(y, m - 1, d);
        if (dataIniFilter) {
          const ini = new Date(dataIniFilter);
          ini.setHours(0,0,0,0);
          if (vDate < ini) ok = false;
        }
        if (dataFimFilter) {
          const fim = new Date(dataFimFilter);
          fim.setHours(23,59,59,999);
          if (vDate > fim) ok = false;
        }
      }
    }
    return ok;
  });

  useEffect(() => {
     setCurrentPage(1);
  }, [empreendimentoFilter, dataIniFilter, dataFimFilter, compradorFilter, unidadeFilter]);

  const totalVgv = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);
  const totalDistratos = filtered.filter(v => v.distrato === 'S').reduce((acc, curr) => acc + (curr.total || 0), 0);

  // Pagination Math
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const addComprador = () => setCompradores([...compradores, { id: Date.now(), nome: '', cpf_cnpj: '', percentual: 0 }]);
  const updateComprador = (id, field, value) => setCompradores(compradores.map(c => c.id === id ? { ...c, [field]: value } : c));
  const removeComprador = (id) => setCompradores(compradores.filter(c => c.id !== id));

  const addCondicao = () => setCondicoes([...condicoes, { id: Date.now(), tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);
  const updateCondicao = (id, field, value) => setCondicoes(condicoes.map(c => c.id === id ? { ...c, [field]: value } : c));
  const removeCondicao = (id) => setCondicoes(condicoes.filter(c => c.id !== id));

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd);
    payload.compradores = compradores;
    payload.condicoes = condicoes;
    
    try {
      await fetch(`${API_BASE}/api/vulcano/vendas`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      alert("Venda cadastrada!"); 
      e.target.reset(); 
      setCompradores([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
      setCondicoes([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);
      setShowForm(false);
      
      // Reload Table
      setLoading(true);
      fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
        .then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
    } catch (err) { alert("Erro ao cadastrar."); }
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
      {/* HEADER STITCH */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
             <ShoppingCart className="text-[var(--v-accent-3)]" size={32}/> 
             Painel de Vendas
          </h2>
          <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Unidades Comercializadas e Distratos</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="bg-[var(--v-accent-3)] text-black text-[11px] font-bold uppercase tracking-widest px-4 py-3 rounded-[var(--v-radius)] hover:opacity-90 transition-opacity flex items-center gap-2">
          <Plus size={16}/> Cadastrar Venda
        </button>
      </div>
      
      {showForm && (
        <div className="magma-card border border-[var(--v-accent-3)]/30 rounded-[var(--v-radius)] p-6 animate-in slide-in-from-top-4 overflow-y-auto max-h-[60vh] custom-scrollbar">
          <div className="flex justify-between items-center mb-6 border-b border-[var(--v-border)] pb-3">
            <h3 className="text-xs uppercase tracking-widest text-[var(--v-accent-3)] font-black">Nova Venda</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] text-[10px] uppercase tracking-widest font-bold">FECHAR X</button>
          </div>
          
          <form className="flex flex-col gap-6" onSubmit={handleFormSubmit}>
            <input type="hidden" name="empresa_id" value={selectedEmpresa} />
            
            <div className="flex gap-4">
              <div className="w-24"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">ID Emp.</label><input name="id_empreendimento" type="number" required className="bento-input w-full" /></div>
              <div className="w-32"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Unidade</label><input name="unidade" required className="bento-input w-full" /></div>
              <div className="flex-1"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Total Venda</label><input name="total" type="number" step="0.01" required className="bento-input w-full" /></div>
              <div className="w-40"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Data Venda</label><input name="data" type="date" required className="bento-input w-full" /></div>
            </div>

            <div className="border border-[var(--v-border)] bg-[var(--v-surface-container)] p-4 rounded-[var(--v-radius)]">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold flex items-center gap-2"><Users size={12}/> Compradores / Sociedade</h4>
                <button type="button" onClick={addComprador} className="text-[var(--v-accent-3)] hover:text-[var(--v-text-bold)] text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Adicionar Comprador</button>
              </div>
              <div className="flex flex-col gap-3">
                {compradores.map((comp, idx) => (
                  <div key={comp.id} className="flex gap-3 items-end">
                    <div className="flex-1"><label className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest block mb-1">Nome/Razão Social</label><input value={comp.nome} onChange={(e) => updateComprador(comp.id, 'nome', e.target.value)} required className="bento-input w-full" /></div>
                    <div className="w-40"><label className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest block mb-1">CPF/CNPJ</label><input value={comp.cpf_cnpj} onChange={(e) => updateComprador(comp.id, 'cpf_cnpj', e.target.value)} required className="bento-input w-full" /></div>
                    <div className="w-24"><label className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest block mb-1">% Compra</label><input type="number" step="0.01" value={comp.percentual} onChange={(e) => updateComprador(comp.id, 'percentual', parseFloat(e.target.value) || 0)} required className="bento-input w-full text-right" /></div>
                    {compradores.length > 1 && (
                      <button type="button" onClick={() => removeComprador(comp.id)} className="bg-[var(--v-text-red)]/10 text-[var(--v-text-red)] border border-[var(--v-text-red)]/30 hover:bg-[var(--v-text-red)] hover:text-[var(--v-text-bold)] p-2 rounded-[var(--v-radius)] mb-[1px] transition-colors"><AlertCircle size={14}/></button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-[var(--v-border)] bg-[var(--v-surface-container)] p-4 rounded-[var(--v-radius)] overflow-x-auto custom-scrollbar">
              <div className="flex justify-between items-center mb-4 min-w-[700px]">
                <h4 className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold flex items-center gap-2"><DollarSign size={12}/> Condições / Projeção</h4>
                <button type="button" onClick={addCondicao} className="text-[var(--v-accent)] hover:text-[var(--v-text-bold)] text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Nova Condição</button>
              </div>
              <div className="flex flex-col gap-3 min-w-[700px]">
                <div className="flex gap-3 px-1">
                  <span className="w-32 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Tipo</span>
                  <span className="w-20 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Qtd.</span>
                  <span className="flex-1 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">1º Vencimento</span>
                  <span className="flex-1 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Valor Base</span>
                  <span className="w-32 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Indexador</span>
                  <span className="w-8"></span>
                </div>
                {condicoes.map((cond, idx) => (
                  <div key={cond.id} className="flex gap-3 items-center">
                    <select value={cond.tipo} onChange={(e) => updateCondicao(cond.id, 'tipo', e.target.value)} className="bento-select w-32">
                      <option value="SINAL">Sinal/Ato</option>
                      <option value="MENSAL">Mensais</option>
                      <option value="REFORCO_ANUAL">Reforço Anual</option>
                      <option value="CHAVE">Balão das Chaves</option>
                      <option value="FINANCIAMENTO">Financiamento</option>
                    </select>
                    <input type="number" min="1" value={cond.quantidade} onChange={(e) => updateCondicao(cond.id, 'quantidade', parseInt(e.target.value) || 1)} required className="bento-input w-20 text-center" />
                    <input type="date" value={cond.vencimento} onChange={(e) => updateCondicao(cond.id, 'vencimento', e.target.value)} required className="bento-input flex-1" />
                    <input type="number" step="0.01" value={cond.valor} onChange={(e) => updateCondicao(cond.id, 'valor', e.target.value)} required className="bento-input flex-1" placeholder="R$" />
                    <select value={cond.indexador} onChange={(e) => updateCondicao(cond.id, 'indexador', e.target.value)} className="bento-select w-32">
                      <option value="NENHUM">Sem Indexador</option>
                      <option value="INCC">INCC</option>
                      <option value="IGPM">IGP-M</option>
                      <option value="IPCA">IPCA</option>
                    </select>
                    {condicoes.length > 1 ? (
                      <button type="button" onClick={() => removeCondicao(cond.id)} className="text-[var(--v-text-red)] hover:text-[var(--v-text-bold)] w-8 flex justify-center"><AlertCircle size={16}/></button>
                    ) : <span className="w-8"></span>}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end mt-2">
              <button type="submit" className="bg-[var(--v-accent-3)] text-black text-[11px] font-bold uppercase tracking-widest px-8 py-3 rounded-[var(--v-radius)] hover:opacity-90 transition-opacity">Registrar Contrato de Venda</button>
            </div>
          </form>
        </div>
      )}

      {/* STITCH MASTER-DETAIL LAYOUT */}
      <div className="flex gap-6 h-[calc(100vh-220px)] overflow-hidden">
        {/* SIDEBAR MASTER */}
        <div className="w-64 magma-card rounded-[var(--v-radius)] flex flex-col shrink-0 border border-[var(--v-border)]">
          <div className="p-4 border-b border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center gap-2">
            <Building2 size={16} className="text-[var(--v-text-faint)]"/>
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-[var(--v-text-muted)]">Obras/Empreendimentos</h3>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-[2px] custom-scrollbar">
            <div 
              onClick={() => setEmpreendimentoFilter('')}
              className={`px-3 py-1.5 text-[11px] font-bold cursor-pointer transition-colors border-l-[3px] rounded-r-[var(--v-radius)] ${empreendimentoFilter === '' ? 'border-[var(--v-accent-3)] text-[var(--v-accent-3)] bg-[var(--v-hover)]' : 'border-transparent text-[var(--v-text-muted)] hover:text-[var(--v-text)] hover:bg-[var(--v-surface-container)]'}`}
            >
              [ CONSOLIDADO GERAL ]
            </div>
            {uniqueEmps.map((emp, i) => (
              <div 
                key={i} 
                onClick={() => setEmpreendimentoFilter(emp)}
                className={`px-3 py-1.5 text-[11px] cursor-pointer transition-colors truncate border-l-[3px] rounded-r-[var(--v-radius)] ${empreendimentoFilter === emp ? 'border-[var(--v-accent-3)] text-[var(--v-accent-3)] bg-[var(--v-hover)] font-bold' : 'border-transparent text-[var(--v-text-faint)] hover:text-[var(--v-text)] hover:bg-[var(--v-surface-container)]'}`} 
                title={emp}
              >
                {emp || 'Indefinido'}
              </div>
            ))}
          </div>
        </div>

        {/* DETAIL CONTENT */}
        <div className="flex-1 flex flex-col gap-5 overflow-hidden">
          {/* SEARCH FILTERS */}
          <div className="magma-card p-4 border border-[var(--v-border)] flex gap-4 shrink-0 rounded-[var(--v-radius)]">
             <div className="flex-1">
                <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Pesquisar Comprador</label>
                <input type="text" placeholder="Nome ou Documento..." value={compradorFilter} onChange={(e) => setCompradorFilter(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono px-3 py-1.5 rounded outline-none placeholder-[#444] transition-colors" />
             </div>
             <div className="flex-1">
                <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Unidade / Num / Desc</label>
                <input type="text" placeholder="Ex: Apto 101..." value={unidadeFilter} onChange={(e) => setUnidadeFilter(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono px-3 py-1.5 rounded outline-none placeholder-[#444] transition-colors" />
             </div>
             <div className="w-32">
                <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Data Inicial</label>
                <input type="date" value={dataIniFilter} onChange={(e) => setDataIniFilter(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono px-3 py-1.5 rounded outline-none placeholder-[#444] transition-colors" />
             </div>
             <div className="w-32">
                <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Data Final</label>
                <input type="date" value={dataFimFilter} onChange={(e) => setDataFimFilter(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono px-3 py-1.5 rounded outline-none placeholder-[#444] transition-colors" />
             </div>
             <div className="flex items-end text-[var(--v-text-faint)] text-[11px] font-mono whitespace-nowrap pb-1.5">
                <span className="text-[var(--v-accent-3)] font-black mr-1">{filtered.length}</span> VENDAS
             </div>
          </div>

          {/* KPI BENTO GRIDS */}
          <div className="grid grid-cols-2 gap-5 shrink-0">
            <div className="magma-card overflow-hidden relative group p-4 border-l-2 border-l-[var(--v-accent-3)] flex justify-between items-center bg-[#111]">
               <div className="flex flex-col">
                  <p className="text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-muted)] font-black mb-0.5">VGV Lançado (Período/Empresa)</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)] tabular-nums">{formatCurrency(totalVgv)}</h4>
               </div>
               <ShoppingCart size={40} className="text-[var(--v-accent-3)] opacity-20 absolute -right-2 -bottom-2 group-hover:scale-110 transition-transform"/>
            </div>
            <div className="magma-card overflow-hidden relative group p-4 border-l-2 border-l-[var(--v-text-red)] flex justify-between items-center bg-[#111]">
               <div className="flex flex-col">
                  <p className="text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-muted)] font-black mb-0.5">Total de Distratos Realizados</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)] tabular-nums">{formatCurrency(totalDistratos)}</h4>
               </div>
            </div>
          </div>

          {/* TABLE DATA GRID (PAGINATED) */}
          <div className="magma-card border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col flex-1 overflow-hidden relative">
            {loading && (
               <div className="absolute inset-0 bg-[#00000099] backdrop-blur-sm flex flex-col items-center justify-center z-50">
                   <Loader2 className="animate-spin text-[var(--v-accent-3)] mb-3" size={40} />
                   <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-bold)]">Integrando Vendas Vulcano...</span>
               </div>
            )}
            <div className="overflow-auto flex-1 custom-scrollbar">
               <table className="w-full text-left text-xs border-collapse font-mono tabular-nums">
                  <thead className="bg-[var(--v-surface-container)] sticky top-0 z-10 shadow-sm border-b border-[var(--v-border)]">
                     <tr>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Contrato</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Data</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Descrição/Unid.</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">CPF/CNPJ</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Cliente</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold border-b border-[var(--v-border)] text-right">Total Venda</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[#888] uppercase font-bold border-b border-[var(--v-border)] text-center w-16" title="Projeção e Condições">Cond</th>
                       <th className="px-3 py-2 text-[9px] tracking-widest text-[#888] uppercase font-bold border-b border-[var(--v-border)] text-center w-16" title="Averbar Distrato/Cancelamento">Dist</th>
                     </tr>
                  </thead>
                  <tbody>
                     {paginatedData.map((v) => (
                       <tr key={v.id} className={`border-b border-[var(--v-border)] transition-colors hover:bg-[var(--v-hover)] ${v.distrato === 'S' ? 'bg-[var(--v-text-red)]/5 border-l-2 border-l-[var(--v-text-red)]' : ''}`}>
                          <td className="p-3 text-[var(--v-text-muted)] font-mono text-[11px]">{v.id} <span className="text-[var(--v-text-faint)] ml-1">#{v.num_cad}</span></td>
                          <td className="p-3 text-[var(--v-text-muted)] font-mono">{v.data}</td>
                          <td className="p-3 text-[var(--v-text)] font-bold truncate max-w-[200px]" title={v.descricao}>{v.descricao}</td>
                          <td className="p-3 text-[var(--v-text-faint)] font-mono">{v.cliente_cnpj}</td>
                          <td className="p-3 text-[var(--v-text-muted)] truncate max-w-[150px]" title={v.cliente_nome}>{v.cliente_nome}</td>
                          <td className={`p-3 text-right font-black text-[13px] ${v.distrato === 'S' ? 'text-[var(--v-text-red)]' : 'text-[var(--v-accent-3)]'}`}>{formatCurrency(v.total)}</td>
                          <td className="p-3 text-center">
                              <button onClick={() => openCondicoes(v)} className="text-[var(--v-accent)] border border-[var(--v-accent)]/40 hover:bg-[var(--v-accent)] hover:text-black transition-colors text-[9px] font-bold uppercase py-1 px-3 rounded-[var(--v-radius)]">Cond.</button>
                          </td>
                          <td className="p-3 text-center">
                              {v.distrato === 'S' ? (
                                  <button onClick={() => openCondicoes(v)} className="flex flex-col items-center gap-1 hover:scale-105 transition-transform" title="Ver detalhes do distrato">
                                      <span className="text-[var(--v-text-red)] text-[9px] uppercase font-bold px-2 py-0.5 bg-[var(--v-text-red)]/10 border border-[var(--v-text-red)]/20 rounded cursor-pointer">Anulado</span>
                                      {v.data_distrato && <span className="text-[8px] text-[var(--v-text-red)] font-mono tracking-widest">{v.data_distrato}</span>}
                                  </button>
                              ) : (
                                  <button onClick={() => setDistratoModal(v)} className="text-[var(--v-text-muted)] border border-[var(--v-border)] hover:border-[var(--v-text-red)] hover:text-[var(--v-text-red)] transition-colors text-[9px] font-bold uppercase py-1 px-3 rounded-[var(--v-radius)]">Distratar</button>
                              )}
                          </td>
                       </tr>
                     ))}
                     {paginatedData.length === 0 && !loading && (
                        <tr><td colSpan="8" className="p-12 text-center text-[var(--v-text-faint)] uppercase tracking-widest text-[10px]">Nenhuma venda registrada para os filtros aplicados.</td></tr>
                     )}
                  </tbody>
               </table>
            </div>

            {/* PAGINATION FOOTER */}
            <div className="p-3 border-t border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center justify-between">
               <span className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold">
                  Exibindo {paginatedData.length} de {filtered.length} Registros
               </span>
               <div className="flex items-center gap-2">
                  <button onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))} disabled={currentPage === 1} className="bento-button disabled:opacity-30">PÁG ANTERIOR</button>
                  <span className="text-[10px] text-[var(--v-text)] uppercase font-bold tracking-widest px-4">{currentPage} / {totalPages || 1}</span>
                  <button onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))} disabled={currentPage === totalPages || totalPages === 0} className="bento-button disabled:opacity-30">PRÓXIMA PÁG</button>
               </div>
            </div>
          </div>
        </div>
      </div>

      {/* DISTRATO MODAL (STITCH) */}
      {distratoModal && (
        <div className="fixed inset-0 bg-[#000000CC] backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in">
          <div className="magma-card border border-[var(--v-text-red)] p-7 rounded-[var(--v-radius)] max-w-md w-full shadow-[0_0_50px_rgba(255,59,48,0.15)]">
            <h3 className="text-sm uppercase tracking-widest text-[var(--v-text-red)] font-black mb-5">Registrar Distrato/Rescisão</h3>
            
            <div className="bg-[var(--v-surface-container)] p-4 border border-[var(--v-border)] rounded-[var(--v-radius)] mb-5">
              <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Alvo do Distrato</p>
              <p className="text-sm font-bold text-[var(--v-text-bold)] block truncate mb-1">{distratoModal.descricao}</p>
              <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-muted)] font-bold">Cliente: {distratoModal.cliente_nome}</p>
            </div>
            
            <form className="flex flex-col gap-4" onSubmit={async (e) => {
              e.preventDefault();
              const fd = new FormData(e.target);
              fd.append('id_venda', distratoModal.id);
              try {
                await fetch(`${API_BASE}/api/distratos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
                alert("Distrato registrado com sucesso!"); 
                setDistratoModal(null);
                setLoading(true);
                fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
                  .then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
              } catch (err) { alert("Erro ao registrar distrato."); }
            }}>
              <div><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-2">Data do Distrato</label><input name="data_distrato" type="date" required className="bento-input w-full" /></div>
              <div><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-2">Valor Total a Devolver (R$)</label><input name="valor_devolvido" type="number" step="0.01" required className="bento-input w-full" /></div>
              <div><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-2">Data Previsão Pagto</label><input name="data_pagamento" type="date" required className="bento-input w-full" /></div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setDistratoModal(null)} className="bento-button border-transparent hover:bg-[var(--v-hover)]">Cancelar</button>
                <button type="submit" className="bg-[var(--v-text-red)] text-[var(--v-text-bold)] text-[10px] font-bold uppercase tracking-widest px-6 py-3 rounded-[var(--v-radius)] hover:opacity-90 transition-opacity">Confirmar Averbação</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONDICOES MODAL (STITCH) */}
      {condicoesModal && (
        <div className="fixed inset-0 bg-[#000000CC] backdrop-blur-sm flex items-center justify-center z-[99999] animate-in fade-in p-6">
          <div className="magma-card border border-[var(--v-accent)] p-6 rounded-[var(--v-radius)] w-full max-w-[1400px] h-full max-h-[85vh] flex flex-col shadow-[0_0_50px_rgba(52,199,89,0.1)]">
            <div className="flex justify-between items-start border-b border-[var(--v-border)] pb-4 mb-5 shrink-0">
               <div>
                  <h3 className="text-lg uppercase tracking-widest text-[var(--v-accent)] font-black flex items-center gap-3">
                     <Layers size={22}/> Estrutura Financeira da Venda
                  </h3>
                  <p className="text-[11px] text-[var(--v-text-faint)] uppercase tracking-widest mt-1">
                     Venda #{condicoesModal.venda?.id} <span className="mx-2">•</span> {condicoesModal.venda?.descricao}
                  </p>
               </div>
               <button onClick={() => setCondicoesModal(null)} className="bento-button border-transparent hover:bg-[var(--v-hover)]"><X size={18}/></button>
            </div>
            
            <div className="flex-1 overflow-auto custom-scrollbar flex flex-col gap-6">
               {condicoesModal.loading && (
                 <div className="flex flex-col items-center justify-center h-40 text-[var(--v-text-muted)] gap-3 bg-[var(--v-surface-container)] rounded-[var(--v-radius)] border border-[var(--v-border)]">
                   <Loader2 className="animate-spin text-[var(--v-accent)]" size={32} />
                   <span className="text-[10px] uppercase tracking-widest font-bold">Resgatando Fluxo Vulcano...</span>
                 </div>
               )}
               
               {!condicoesModal.loading && condicoesModal.error && (
                 <div className="magma-card border-l-4 border-l-[var(--v-text-red)] p-5">
                   <h4 className="text-[var(--v-text-red)] font-bold mb-2">Erro de Resgate</h4>
                   <p className="text-[var(--v-text-muted)] text-sm">{condicoesModal.error}</p>
                 </div>
               )}
               
               {!condicoesModal.loading && condicoesModal.payload && (
                  <>
                    <div className="grid grid-cols-3 gap-5">
                       <div className="bg-[var(--v-surface-container)] border border-[var(--v-border)] p-4 rounded-[var(--v-radius)] flex flex-col justify-center">
                          <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold">Target VGV</span>
                          <span className="text-xl font-black text-[var(--v-accent-3)]">{formatCurrency(condicoesModal.payload.venda?.total || 0)}</span>
                       </div>
                       <div className="bg-[var(--v-surface-container)] border border-[var(--v-border)] p-4 rounded-[var(--v-radius)]">
                          <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold">Cliente Base</span>
                          <span className="text-sm font-bold text-[var(--v-text)] block truncate">{condicoesModal.payload.venda?.cliente?.nome || '-'}</span>
                          <span className="text-[10px] uppercase font-mono text-[var(--v-text-muted)]">{condicoesModal.payload.venda?.cliente?.cnpj || ''}</span>
                       </div>
                       <div className="bg-[var(--v-surface-container)] border border-[var(--v-border)] p-4 rounded-[var(--v-radius)]">
                          <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold">Ref. Data</span>
                          <span className="text-sm font-bold text-[var(--v-text)] block">{condicoesModal.payload.venda?.data || '-'}</span>
                          <span className="text-[10px] uppercase text-[var(--v-text-muted)] truncate block">{condicoesModal.payload.venda?.empreendimento || '-'}</span>
                       </div>
                    </div>
                    
                    {condicoesModal.payload.distratos && condicoesModal.payload.distratos.length > 0 && (
                        <div className="magma-card border-l-4 border-l-[var(--v-text-red)] p-5 mt-2 bg-[var(--v-text-red)]/5">
                            <h4 className="text-[var(--v-text-red)] font-black text-xs uppercase tracking-widest mb-3 flex items-center gap-2"><AlertCircle size={14}/> Contrato Distratado</h4>
                            <div className="grid grid-cols-3 gap-5">
                                <div>
                                    <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-red)] opacity-70 block mb-1">Data do Distrato</span>
                                    <span className="text-sm font-bold font-mono text-[var(--v-text-red)]">{condicoesModal.payload.distratos[0].data}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-red)] opacity-70 block mb-1">Receita Caixa (Paga)</span>
                                    <span className="text-sm font-bold font-mono text-[var(--v-text-bold)]">
                                        {formatCurrency((condicoesModal.payload.parcelas || []).reduce((acc, p) => acc + (p.total_pago || 0), 0))}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-red)] opacity-70 block mb-1">Valor a Devolver</span>
                                    <span className="text-sm font-bold font-mono text-[var(--v-text-red)]">{formatCurrency(condicoesModal.payload.distratos[0].valor_devolvido)}</span>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-full min-h-0 mt-6">
                       {/* FORMAS DE PAGAMENTO */}
                       <div className="flex flex-col border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden bg-[var(--v-surface-container)]">
                          <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)]">
                             <h4 className="text-[10px] tracking-widest uppercase font-bold text-[var(--v-text-bold)]">Quadro de Condições Formais</h4>
                          </div>
                          <div className="flex-1 overflow-auto">
                             <table className="w-full text-left text-[11px] border-collapse">
                                <thead className="bg-[#0f0f0f] border-b border-[var(--v-border)] sticky top-0">
                                   <tr>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest">Macro Componente</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">Montante Base</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">Aberturas</th>
                                   </tr>
                                </thead>
                                <tbody>
                                  {(condicoesModal.payload.formas_pagto || []).map(f => (
                                     <tr key={f.id} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                                        <td className="p-3 font-bold text-[var(--v-text-muted)]">{f.descricao || '-'}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-text)] font-semibold">{formatCurrency(f.valor || 0)}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-text-faint)]">{f.quantidade_parcelas || 0} p.</td>
                                     </tr>
                                  ))}
                                  {(condicoesModal.payload.formas_pagto || []).length === 0 && (
                                     <tr><td colSpan="3" className="p-10 text-center text-[var(--v-text-faint)] italic text-[10px] uppercase">Nenhuma condição comercial fixada.</td></tr>
                                  )}
                                </tbody>
                             </table>
                          </div>
                       </div>
                       
                       {/* PLANILHA RECEBER (PARCELAS) */}
                       <div className="flex flex-col border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden bg-[var(--v-surface-container)]">
                          <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)] flex justify-between items-center">
                             <h4 className="text-[10px] tracking-widest uppercase font-bold text-[var(--v-text-bold)]">Projeção Dinâmica (Contas a Receber)</h4>
                             <span className="text-[10px] text-[var(--v-text-faint)] font-mono">{(condicoesModal.payload.parcelas || []).length} Títulos</span>
                          </div>
                          <div className="flex-1 overflow-auto">
                             <table className="w-full text-left text-[11px] border-collapse">
                                <thead className="bg-[#0f0f0f] border-b border-[var(--v-border)] sticky top-0">
                                   <tr>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest whitespace-nowrap">Venc. / Nº</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">R$ Parcela</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">R$ Variação</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">Status Quitação</th>
                                   </tr>
                                </thead>
                                <tbody>
                                  {(condicoesModal.payload.parcelas || []).map(p => (
                                     <tr key={p.id} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                                        <td className="p-3 font-mono text-[var(--v-text-muted)] whitespace-nowrap">{p.data || '-'} <span className="opacity-30">|</span> {p.parcela || '-'}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-text)] font-semibold">{formatCurrency(p.valor_parcela || 0)}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-accent-6)]">{p.variacao > 0 ? formatCurrency(p.variacao) : '-'}</td>
                                        <td className={`p-3 text-right font-mono font-bold font-black flex justify-end gap-2 items-center ${(p.total_pago || 0) > 0 ? 'text-[var(--v-accent)]' : 'text-[var(--v-text-faint)]'}`}>
                                          {(p.total_pago || 0) > 0 ? <><CheckCircle size={10}/> {formatCurrency(p.total_pago)}</> : 'Aberto'}
                                        </td>
                                     </tr>
                                  ))}
                                  {(condicoesModal.payload.parcelas || []).length === 0 && (
                                     <tr><td colSpan="4" className="p-10 text-center text-[var(--v-text-faint)] italic text-[10px] uppercase">Nenhum título projetado.</td></tr>
                                  )}
                                </tbody>
                             </table>
                          </div>
                       </div>
                    </div>
                  </>
               )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const RecebimentosView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [unidadeFilter, setUnidadeFilter] = useState('');
  const [clienteFilter, setClienteFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showConferencia, setShowConferencia] = useState(false);
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 100;

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        if (!Array.isArray(d)) {
           setData([]);
           setLoading(false);
           return;
        }
        setData(d);
        const emps = [...new Set(d.map(r => r.empreendimento))].sort();
        if (emps.length > 0) setEmpreendimentoFilter(emps[0]);
        else setEmpreendimentoFilter('');
        
        setUnidadeFilter(''); setClienteFilter('');
        setDateFrom(''); setDateTo('');
        setLoading(false);
      })
      .catch(err => { console.error(err); setLoading(false); });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(r => r.empreendimento))].sort();
  const filteredBase = data.filter(r => !empreendimentoFilter || r.empreendimento === empreendimentoFilter);
  const uniqueUnidades = [...new Set(filteredBase.map(r => r.descricao_venda).filter(Boolean))].sort();
  const uniqueClientes = [...new Set(filteredBase.map(r => r.cliente).filter(Boolean))].sort();

  const inDateRange = (dateStr) => {
    if (!dateFrom && !dateTo) return true;
    if (!dateStr || typeof dateStr !== 'string') return false;
    if (dateFrom && dateStr < dateFrom) return false;
    if (dateTo && dateStr > dateTo) return false;
    return true;
  };

  const filtered = filteredBase.filter(r =>
    inDateRange(r.vencimento_iso || r.data) &&
    (!unidadeFilter || r.descricao_venda === unidadeFilter) &&
    (!clienteFilter || r.cliente === clienteFilter)
  );

  useEffect(() => {
    setUnidadeFilter(''); setClienteFilter('');
    setDateFrom(''); setDateTo('');
    setCurrentPage(1); // Reset pagination on master filter change
  }, [empreendimentoFilter]);
  
  // When sub-filters change, reset page
  useEffect(() => {
     setCurrentPage(1);
  }, [unidadeFilter, clienteFilter, dateFrom, dateTo]);

  const totalPago = filtered.reduce((acc, curr) => acc + ((curr.total > 0) ? curr.total : 0), 0);
  const totalParcela = filtered.reduce((acc, curr) => acc + (curr.parcela || 0), 0);
  const totalVariacao = filtered.reduce((acc, curr) => acc + (curr.variacao || 0), 0);
  
  // Pagination Math
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const handleDarBaixa = async (r) => {
    if (!r.id) return alert("Parcela não possui ID vinculado.");
    const valorInput = prompt(`Dar baixa na parcela ${r.num_parcela} de ${formatCurrency(r.parcela)}?\nDigite o valor pago:`, r.parcela);
    if (!valorInput) return;
    const valorPago = parseFloat(valorInput.replace(',', '.'));
    if (isNaN(valorPago) || valorPago <= 0) return alert("Valor inválido");

    try {
      setLoading(true);
      await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_receber: r.id, valor_pago: valorPago })
      });
      fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
        .then(res => res.json()).then(d => { setData(d); setLoading(false); });
    } catch (err) {
      alert("Erro ao dar baixa");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
      {/* HEADER STITCH */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
             <DollarSign className="text-[var(--v-accent)]" size={32}/> 
             Extrato de Recebimentos
          </h2>
          <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Industrial Master-Detail Ledger</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowConferencia(true)} className="bento-button flex items-center gap-2">
            <CheckCircle2 size={16}/> Modo Conferência
          </button>
          <button onClick={() => {
            const csvContent = "data:text/csv;charset=utf-8," + "Data,Total_Pago,Parcela,Variacao,Venda,Cliente\n" + filtered.map(e => `${e.data},${e.total},${e.parcela},${e.variacao},"${e.descricao_venda}","${e.cliente}"`).join("\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "recebimentos.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }} className="bento-button flex items-center gap-2">
            <Download size={16}/> Baixar CSV
          </button>
          <button onClick={() => setShowForm(!showForm)} className="bg-[var(--v-accent)] text-black text-[11px] font-bold uppercase tracking-widest px-4 py-3 rounded-[var(--v-radius)] hover:opacity-90 transition-opacity flex items-center gap-2">
            <Plus size={16}/> Lançar Manual
          </button>
        </div>
      </div>

      {showForm && (
        <div className="magma-card border border-[var(--v-accent)]/30 rounded-[var(--v-radius)] p-5 animate-in slide-in-from-top-4">
          <h3 className="text-xs uppercase tracking-widest text-[var(--v-accent)] font-bold mb-4">Novo Recebimento (Bypass Caixa)</h3>
          <form className="flex flex-wrap gap-4 items-end" onSubmit={async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
              alert("Recebimento cadastrado!"); e.target.reset(); setShowForm(false);
            } catch (err) { alert("Erro ao cadastrar."); }
          }}>
            <input type="hidden" name="empresa_id" value={selectedEmpresa} />
            <div className="w-24"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">ID Venda</label><input name="id_venda" type="number" required className="bento-input" /></div>
            <div className="w-28"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Parcela</label><input name="parcela" type="number" required className="bento-input" /></div>
            <div className="w-32"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Valor Venda</label><input name="valor" type="number" step="0.01" required className="bento-input" /></div>
            <div className="w-40"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Data Pagto</label><input name="data" type="date" required className="bento-input" /></div>
            <button type="submit" className="bg-[var(--v-accent)] text-black text-[11px] font-bold uppercase tracking-widest px-8 py-3 rounded-[var(--v-radius)] hover:opacity-90">Confirmar</button>
          </form>
        </div>
      )}

      {/* STITCH MASTER-DETAIL LAYOUT */}
      <div className="flex gap-6 h-[calc(100vh-280px)] overflow-hidden">
        {/* SIDEBAR MASTER */}
        <div className="w-64 magma-card rounded-[var(--v-radius)] flex flex-col shrink-0 border border-[var(--v-border)]">
          <div className="p-4 border-b border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center gap-2">
            <Building2 size={16} className="text-[var(--v-text-faint)]"/>
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-[var(--v-text-muted)]">Obras/Empreendimentos</h3>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            <div 
              onClick={() => setEmpreendimentoFilter('')}
              className={`p-3 text-xs font-bold cursor-pointer transition-colors rounded-[var(--v-radius)] ${empreendimentoFilter === '' ? 'text-[var(--v-accent)] bg-[var(--v-hover)]' : 'text-[var(--v-text-muted)] hover:text-[var(--v-text)] hover:bg-[var(--v-border)]'}`}
            >
              [ CONSOLIDADO GERAL ]
            </div>
            {uniqueEmps.map((emp, i) => (
              <div 
                key={i} 
                onClick={() => setEmpreendimentoFilter(emp)}
                className={`p-3 text-xs cursor-pointer transition-colors truncate rounded-[var(--v-radius)] ${empreendimentoFilter === emp ? 'text-[var(--v-accent-3)] bg-[var(--v-hover)] font-bold' : 'text-[var(--v-text-faint)] hover:text-[var(--v-text)] hover:bg-[var(--v-surface-container)]'}`} 
                title={emp}
              >
                {emp}
              </div>
            ))}
          </div>
        </div>

        {/* DETAIL CONTENT */}
        <div className="flex-1 flex flex-col gap-5 overflow-hidden">
          {/* KPI BENTO GRIDS */}
          <div className="grid grid-cols-3 gap-5 shrink-0">
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Recebido (Caixa)</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalPago)}</h4>
               </div>
               <DollarSign size={40} className="text-[var(--v-accent)] opacity-20 absolute -right-2 -bottom-2 group-hover:scale-110 transition-transform"/>
            </div>
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent-3)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Origem Parcela</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalParcela)}</h4>
               </div>
            </div>
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent-6)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Variação Realizada</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalVariacao)}</h4>
               </div>
            </div>
          </div>

          {/* FILTER STRIP */}
          <div className="magma-card border border-[var(--v-border)] rounded-[var(--v-radius)] p-4 shrink-0 flex flex-wrap gap-4 items-end bg-[var(--v-surface-container)]">
            <div className="w-32"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">De</label><input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="bento-input w-full"/></div>
            <div className="w-32"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Até</label><input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="bento-input w-full"/></div>
            <div className="flex-1 min-w-[200px]"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Unidade</label>
              <select value={unidadeFilter} onChange={e => setUnidadeFilter(e.target.value)} className="bento-select w-full">
                 <option value="">TODAS AS UNIDADES</option>
                 {uniqueUnidades.map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <div className="flex-1 min-w-[200px]"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Comprador</label>
              <select value={clienteFilter} onChange={e => setClienteFilter(e.target.value)} className="bento-select w-full">
                 <option value="">TODOS COMPRADORES</option>
                 {uniqueClientes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <button onClick={() => { setDateFrom(''); setDateTo(''); setUnidadeFilter(''); setClienteFilter(''); }} className="bento-button py-3">LIMPAR</button>
          </div>

          {/* TABLE DATA GRID (PAGINATED) */}
          <div className="magma-card border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col flex-1 overflow-hidden relative">
            {loading && (
               <div className="absolute inset-0 bg-[#00000099] backdrop-blur-sm flex flex-col items-center justify-center z-50">
                   <Loader2 className="animate-spin text-[var(--v-accent)] mb-3" size={40} />
                   <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-bold)]">Carregando Diário de Caixa...</span>
               </div>
            )}
            <div className="overflow-auto flex-1 custom-scrollbar">
               <table className="w-full text-left text-xs border-collapse font-mono tabular-nums">
                  <thead className="bg-[var(--v-surface-container)] sticky top-0 z-10 shadow-sm border-b border-[var(--v-border)]">
                     <tr>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold w-24">Data</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent)] uppercase font-bold text-right">Pago</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">Parcela</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-right">Variação</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Unidade</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Comprador</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Obs</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-center w-24">Ação</th>
                     </tr>
                  </thead>
                  <tbody>
                     {paginatedData.map((r, idx) => {
                       const isAberto = !r.total || r.total <= 0;
                       let isAtrasada = false;
                       if (isAberto && r.data) {
                          const parts = r.data.split('/');
                          if (parts.length === 3) {
                             const vencDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}T00:00:00`);
                             const today = new Date(); today.setHours(0,0,0,0);
                             if (vencDate < today) isAtrasada = true;
                          }
                       }
                       return (
                         <tr key={idx} className={`border-b border-[var(--v-border)] transition-colors hover:bg-[var(--v-hover)] ${isAtrasada ? 'bg-[var(--v-accent)]/5 border-l-2 border-l-[var(--v-accent)]' : ''}`}>
                            <td className="p-3 text-[var(--v-text-muted)] font-mono">{r.data}</td>
                            <td className="p-3 text-right font-black text-[var(--v-accent)] text-[13px]">{!isAberto ? formatCurrency(r.total) : isAtrasada ? <span className="text-[var(--v-accent)] text-[9px] uppercase px-2 py-0.5 bg-[var(--v-accent)]/10 rounded">Atrasada</span> : <span className="text-[var(--v-text-faint)] text-[9px] uppercase">A Vencer</span>}</td>
                            <td className="p-3 text-right font-bold text-[var(--v-accent-3)] font-mono">{formatCurrency(r.parcela)}</td>
                            <td className="p-3 text-right font-bold text-[var(--v-accent-6)] font-mono">{formatCurrency(r.variacao)}</td>
                            <td className="p-3 text-[var(--v-text-muted)] truncate max-w-[150px]">{r.descricao_venda}</td>
                            <td className="p-3 text-[var(--v-text)] truncate max-w-[150px] font-bold">{r.cliente}</td>
                            <td className="p-3 text-[10px] uppercase text-[var(--v-text-faint)] truncate max-w-[100px]">{r.obs}</td>
                            <td className="p-3 text-center">
                               {isAberto ? (
                                   <button onClick={() => handleDarBaixa(r)} className="text-[var(--v-accent)] border border-[var(--v-accent)] hover:bg-[var(--v-accent)] hover:text-black transition-colors text-[9px] font-bold uppercase py-1 px-3 rounded-[var(--v-radius)]">Liquidar</button>
                               ) : <span className="text-[var(--v-text-muted)] text-[9px] uppercase font-bold flex items-center justify-center gap-1"><CheckCircle size={10}/> Baixado</span>}
                            </td>
                         </tr>
                       )
                     })}
                     {paginatedData.length === 0 && !loading && (
                        <tr><td colSpan="8" className="p-12 text-center text-[var(--v-text-faint)] uppercase tracking-widest text-[10px]">Nenhuma parcela encontrada.</td></tr>
                     )}
                  </tbody>
               </table>
            </div>

            {/* OVERENGINEERED PAGINATION FOOTER */}
            <div className="p-3 border-t border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center justify-between">
               <span className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold">
                  Exibindo {paginatedData.length} de {filtered.length} Registros
               </span>
               <div className="flex items-center gap-2">
                  <button onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))} disabled={currentPage === 1} className="bento-button disabled:opacity-30">PÁG ANTERIOR</button>
                  <span className="text-[10px] text-[var(--v-text)] uppercase font-bold tracking-widest px-4">{currentPage} / {totalPages || 1}</span>
                  <button onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))} disabled={currentPage === totalPages || totalPages === 0} className="bento-button disabled:opacity-30">PRÓXIMA PÁG</button>
               </div>
            </div>
          </div>
        </div>
      </div>

      {/* CONFERENCIA MODAL */}
      {showConferencia && (
         <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/95 p-6 animate-in fade-in">
           <div className="magma-card w-full h-full max-w-[1600px] flex flex-col border border-[var(--v-border)]">
             <div className="flex justify-between items-center p-5 border-b border-[var(--v-border)] bg-[var(--v-surface-container)] shrink-0">
               <div>
                 <h3 className="text-xl font-bold uppercase tracking-wider text-[var(--v-accent-3)] flex items-center gap-3">
                   <ShieldAlert size={24}/> Auditoria de Matriz Completa
                 </h3>
                 <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-[0.2em] mt-1">Conferência Tabela de Vendas / Recebimentos ({filtered.length} linhas globais)</p>
               </div>
               <button onClick={() => setShowConferencia(false)} className="text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] transition-colors p-2 bg-[var(--v-hover)] rounded border border-[var(--v-border)]">
                 <X size={20}/>
               </button>
             </div>
             
             <div className="flex-1 overflow-auto bg-[var(--v-deep)]">
               <table className="w-full text-left text-[11px] border-collapse whitespace-nowrap">
                 <thead className="sticky top-0 bg-[var(--v-surface-container)] z-10 border-b border-[var(--v-border)]">
                   <tr>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">CNPJ/CPF</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Comprador</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Unidade</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Vlr Venda</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Data</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-accent-3)]">Parcela</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-red)]">Desc.</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-accent-6)]">Variação</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-accent)]">Total Pago</th>
                     <th className="p-3 border-r border-[var(--v-border)] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">X/Y</th>
                   </tr>
                 </thead>
                 <tbody>
                   {/* Hard limiter to 1000 in Modal to prevent freeze if user clicks Conferencia without filters */}
                   {filtered.slice(0, 1000).map((r, i) => (
                     <tr key={i} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] text-[var(--v-text)] font-mono">
                       <td className="p-3 border-r border-[var(--v-border)] text-[var(--v-text-muted)]">{r.cliente_cnpj || '-'}</td>
                       <td className="p-3 border-r border-[var(--v-border)] font-sans truncate max-w-[200px]">{r.cliente}</td>
                       <td className="p-3 border-r border-[var(--v-border)] font-sans truncate max-w-[150px]">{r.descricao_venda}</td>
                       <td className="p-3 border-r border-[var(--v-border)] text-right text-[var(--v-text-muted)] bg-[var(--v-deep)]">{r.venda_total ? formatCurrency(r.venda_total) : '-'}</td>
                       <td className="p-3 border-r border-[var(--v-border)]">{r.data || '-'}</td>
                       <td className="p-3 border-r border-[var(--v-border)] text-right text-[var(--v-accent-3)] bg-[var(--v-accent-3)]/5">{formatCurrency(r.parcela)}</td>
                       <td className="p-3 border-r border-[var(--v-border)] text-right text-[var(--v-text-red)]">{r.desconto > 0 ? formatCurrency(r.desconto) : '-'}</td>
                       <td className="p-3 border-r border-[var(--v-border)] text-right text-[var(--v-accent-6)] font-semibold">{r.variacao > 0 ? formatCurrency(r.variacao) : '-'}</td>
                       <td className="p-3 border-r border-[var(--v-border)] text-right text-[var(--v-accent)] font-bold bg-[var(--v-accent)]/10">{formatCurrency(r.total)}</td>
                       <td className="p-3 border-r border-[var(--v-border)] text-center">{r.num_parcela || '-'}</td>
                     </tr>
                   ))}
                   {filtered.length > 1000 && (
                     <tr><td colSpan="10" className="p-6 text-center text-[var(--v-text-bold)] bg-[var(--v-accent)]/20 uppercase tracking-widest text-xs font-bold">Limitado a 1000 amostras na Conferência Visual. Exporte em CSV para visualizar os {filtered.length} registros.</td></tr>
                   )}
                 </tbody>
               </table>
             </div>
           </div>
         </div>
      )}
    </div>
  );
};

export const ConciliadorView = ({ selectedEmpresa }) => {
  const [pdfFile, setPdfFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [hasCode, setHasCode] = useState(false);
  const [codePreview, setCodePreview] = useState('');
  const [codeStats, setCodeStats] = useState({ chars: 0, lines: 0 });
  const fullCodeRef = React.useRef('');
  const [templateNome, setTemplateNome] = useState('');
  const [templateDescricao, setTemplateDescricao] = useState('');
  const [definirPadrao, setDefinirPadrao] = useState(true);
  const [savedTemplates, setSavedTemplates] = useState([]);
  const [pickTemplateId, setPickTemplateId] = useState('');
  const [lastTemplateId, setLastTemplateId] = useState(null);
  /** Se true, ignora modelo/padrão e chama só o Gemini na extração. */
  const [extractForceAi, setExtractForceAi] = useState(false);
  const [importMode, setImportMode] = useState('vendas'); 
  const [extractedData, setExtractedData] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  const [isSimulating, setIsSimulating] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [viewMode, setViewMode] = useState('raw'); // 'raw', 'preview'
  const [expandedRowIndex, setExpandedRowIndex] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [useSplinkMatch, setUseSplinkMatch] = useState(false); // ⚡ Splink probabilístico
  

  const [rawPdfLines, setRawPdfLines] = useState([]);
  const [selectedRawLines, setSelectedRawLines] = useState([]);
  const [chatTab, setChatTab] = useState('chat'); // 'chat', 'pdf_samples'
  
  const fileInputRef = React.useRef(null);

  const applyCodeToPreview = (raw) => {
    const code = typeof raw === 'string' ? raw : '';
    fullCodeRef.current = code;
    const lines = code ? code.split('\n').length : 0;
    const maxPreview = 14000;
    if (code.length > maxPreview) {
      setCodePreview(
        code.slice(0, maxPreview) +
          `\n\n# … ${code.length - maxPreview} caracteres omitidos na tela (use Baixar .py para o arquivo completo).`
      );
    } else {
      setCodePreview(code);
    }
    setCodeStats({ chars: code.length, lines });
    setHasCode(!!code.trim());
  };

  const resetSession = () => {
    setPdfFile(null);
    setExtractedData([]);
    setChatHistory([]);
    setChatInput('');
    setHasCode(false);
    setCodePreview('');
    setCodeStats({ chars: 0, lines: 0 });
    fullCodeRef.current = '';
    setTemplateNome('');
    setTemplateDescricao('');
    setLastTemplateId(null);
    setPickTemplateId('');
    setExtractForceAi(false);
    setErrorMsg('');
    setPreviewData(null);
    setViewMode('raw');
    setRawPdfLines([]);
    setSelectedRawLines([]);
    setChatTab('chat');
  };

  const fetchTemplates = () => {
    const q = selectedEmpresa ? `?empresa_id=${encodeURIComponent(selectedEmpresa)}` : '';
    fetch(`${API_BASE}/api/parser/templates${q}`)
      .then((r) => r.json())
      .then((d) => setSavedTemplates(Array.isArray(d) ? d : []))
      .catch(() => setSavedTemplates([]));
  };

  useEffect(() => {
    fetchTemplates();
  }, [selectedEmpresa]);

  const handleLoadSavedTemplate = async () => {
    const id = pickTemplateId;
    if (!id) {
      alert('Selecione um modelo na lista.');
      return;
    }
    setErrorMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/parser/templates/${encodeURIComponent(id)}`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
      const code = typeof json.python_code === 'string' ? json.python_code : '';
      applyCodeToPreview(code);
      if (json.nome) setTemplateNome(json.nome);
      if (json.descricao != null) setTemplateDescricao(json.descricao || '');
      if (json.id != null) setLastTemplateId(json.id);
    } catch (e) {
      console.error(e);
      setErrorMsg(e.message || 'Falha ao carregar modelo.');
    }
  };

  const handleSetPadraoLista = async () => {
    if (!selectedEmpresa || !pickTemplateId) {
      alert('Selecione empresa (topo) e um modelo na lista.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/parser/templates/set-default`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa, 10),
          parser_template_id: parseInt(pickTemplateId, 10),
        }),
      });
      if (!res.ok) throw new Error('Falha');
      fetchTemplates();
      alert('Modelo definido como padrão desta empresa.');
    } catch {
      alert('Não foi possível definir o padrão.');
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setPdfFile(f);
      setExtractedData([]);
      setChatHistory([]);
      setChatInput('');
      setErrorMsg('');
      setHasCode(false);
      setCodePreview('');
      fullCodeRef.current = '';
      setTemplateNome(f.name.replace(/\.pdf$/i, '').replace(/\.pdf\.pdf$/i, '') || '');
    }
  };

  const withTimeout = async (fn, ms, timeoutMessage) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), ms);
    try {
      return await fn(controller.signal);
    } catch (e) {
      if (e?.name === 'AbortError') throw new Error(timeoutMessage || 'Tempo limite excedido.');
      throw e;
    } finally {
      clearTimeout(id);
    }
  };

  const handleExtract = async () => {
    if (!pdfFile) return;
    setIsProcessing(true);
    setHasCode(false);
    setCodePreview('');
    fullCodeRef.current = '';
    setLastTemplateId(null);
    setExtractedData([]);
    setChatHistory([]);
    setChatInput('');
    setErrorMsg('');
    setPreviewData(null);
    setViewMode('raw');

    const formData = new FormData();
    formData.append('file', pdfFile);
    formData.append('import_mode', importMode);
    
    const qs = new URLSearchParams();
    if (!extractForceAi) {
      if (pickTemplateId) {
        qs.set('parser_template_id', String(pickTemplateId));
      } else if (selectedEmpresa) {
        qs.set('empresa_id', String(selectedEmpresa));
      }
      // Evita cair automaticamente em IA quando o modelo/padrão retorna 0 linhas.
      // O operador pode comparar manualmente ativando "Só IA".
      qs.set('allow_gemini_fallback', 'false');
    }
    const extractUrl = `${API_BASE}/api/extract-pdf${qs.toString() ? `?${qs.toString()}` : ''}`;

    try {
      const data = await withTimeout(async (signal) => {
        const res = await fetch(extractUrl, { method: 'POST', body: formData, signal });
        const text = await res.text();
        let json = {};
        try {
          json = text ? JSON.parse(text) : {};
        } catch {
          throw new Error(
            res.ok
              ? `Resposta inválida do servidor (não é JSON). Trecho: ${text.slice(0, 240)}`
              : `Erro HTTP ${res.status}: ${text.slice(0, 400)}`
          );
        }
        if (!res.ok) {
          const d = json.detail;
          const msg = Array.isArray(d)
            ? d.map((x) => (typeof x === 'string' ? x : x.msg || JSON.stringify(x))).join('; ')
            : typeof d === 'string'
              ? d
              : d != null
                ? JSON.stringify(d)
                : '';
          throw new Error(msg || `Erro HTTP ${res.status}`);
        }
        return json;
      }, 610000, `A extração demorou demais (~10 min). URL: ${extractUrl}. Modelo Ollama local pode estar sobrecarregado ou baixando cache na RAM.`);

      const rows = Array.isArray(data.extracted_data) ? data.extracted_data : [];
      setExtractedData(rows);
      setRawPdfLines(Array.isArray(data.raw_text_lines) ? data.raw_text_lines : []);
      const via =
        data.parser_source === 'template'
          ? `Script salvo (#${data.parser_template_id ?? pickTemplateId ?? '—'}), sem IA.`
          : data.parser_source === 'heuristic'
            ? `Heurística no servidor (modelo #${data.parser_template_id ?? pickTemplateId ?? '—'} não casou linhas no .py)`
            : data.parser_source === 'gemini_fallback'
              ? `Gemini (fallback do modelo #${data.parser_template_id ?? pickTemplateId ?? '—'})`
              : 'Gemini (IA).';
      const hintZero =
        rows.length === 0 && data.parser_source === 'template'
          ? ' Nenhuma linha: o regex do modelo pode não bater com este PDF (ou resposta inválida). Tente “Só IA” para comparar.'
          : '';
      if (data.error && data.hint) {
        setErrorMsg(data.hint);
      } else if (rows.length === 0 && (data.parser_source === 'gemini' || data.parser_source === 'gemini_fallback')) {
        setErrorMsg('A IA não encontrou linhas neste PDF. Pode ser outro tipo de relatório (o prompt atual busca recebimentos) ou o texto extraído está diferente do esperado.');
      } else if (rows.length === 0 && data.parser_source === 'template') {
        setErrorMsg('O Ollama rodou o manifesto salvo, mas devolveu zero recebimentos. O modelo Llama pode ter se confundido com o layout ou as diretrizes salvas. Atualize as regras ou use o botão SEM modelo (Gemini fallback).');
      }
      const tailHint = data.hint ? ` ${data.hint}` : '';
      setChatHistory([
        { role: 'assistant', content: `Extração concluída (${via}) Linhas: ${rows.length}.${hintZero}${tailHint}` },
      ]);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Falha ao extrair PDF.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleChatAdjust = async () => {
    let instruction = chatInput.trim();
    if (!instruction) return;
    if (!Array.isArray(extractedData)) return;
    setIsChatting(true);
    setErrorMsg('');

    const originalChatInput = chatInput.trim();
    if (selectedRawLines.length > 0) {
      const sampleText = selectedRawLines.map(idx => rawPdfLines[idx]).join('\n');
      instruction = `O operador selecionou os blocos estruturais do PDF abaixo como contexto izolado para calibração de posições das chaves JSON:\n---\n${sampleText}\n---\nCorreção pedida explicitamente: ${originalChatInput}`;
      setSelectedRawLines([]); 
    }

    const historyNext = [...chatHistory, { role: 'user', content: originalChatInput }];
    setChatHistory(historyNext);
    setChatInput('');

    try {
      const resp = await withTimeout(async (signal) => {
        const res = await fetch(`${API_BASE}/api/parser/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction, current_data: extractedData }),
          signal
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
        return json;
      }, 180000, 'O chat demorou demais (3 min). Verifique GEMINI_API_KEY e a conexão.');

      const updated = Array.isArray(resp.updated_data) ? resp.updated_data : extractedData;
      setExtractedData(updated);
      setChatHistory(prev => [...prev, { role: 'assistant', content: resp.message || `Aplicado ajuste. Linhas atuais: ${updated.length}.` }]);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Falha ao ajustar via chat.');
      setChatHistory(prev => [...prev, { role: 'assistant', content: `Erro: ${err.message || 'falha no ajuste'}` }]);
    } finally {
      setIsChatting(false);
    }
  };

  const handleGeneratePython = async () => {
    if (!Array.isArray(extractedData) || extractedData.length === 0) return;
    const nome = (templateNome || '').trim() || (pdfFile?.name?.replace(/\.pdf$/i, '') || 'Parser PDF');
    setIsSaving(true);
    setErrorMsg('');
    setHasCode(false);
    setCodePreview('');
    fullCodeRef.current = '';

    try {
      const resp = await withTimeout(async (signal) => {
        const res = await fetch(`${API_BASE}/api/parser/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            history: chatHistory,
            final_data: extractedData,
            nome,
            descricao: templateDescricao || null,
            empresa_id: selectedEmpresa ? parseInt(selectedEmpresa, 10) : null,
            definir_padrao_empresa: definirPadrao && !!selectedEmpresa,
          }),
          signal
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
        return json;
      }, 300000, 'A geração do script demorou demais (5 min). Verifique GEMINI_API_KEY e a conexão.');

      const raw =
        (resp.code && typeof resp.code === 'string' && resp.code) ||
        (resp.python_code && typeof resp.python_code === 'string' && resp.python_code) ||
        `# ${resp.status || 'Script'}\n# ${resp.filename || ''}\n`;
      applyCodeToPreview(raw);
      if (resp.template_id != null) {
        setLastTemplateId(resp.template_id);
        setPickTemplateId(String(resp.template_id));
      }
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            (resp.status || 'Script gerado.') +
            (resp.template_id ? ` Registro #${resp.template_id} no sistema.` : ''),
        },
      ]);
      fetchTemplates();
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Falha ao gerar o script.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadCode = () => {
    const full = fullCodeRef.current;
    if (!full) return;
    const blob = new Blob([full], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `${(templateNome || "pdf_parser_prompt").replace(/[^\w\-]+/g, "_")}.txt`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handlePreviewBaixas = async () => {
    if (!selectedEmpresa || !extractedData || extractedData.length === 0) {
      alert("Selecione uma empresa no topo e extraia os dados primeiro.");
      return;
    }
    try {
      setIsSimulating(true);
      setErrorMsg("");
      const res = await fetch(`${API_BASE}/api/parser/preview-baixas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa, 10),
          extracted_data: extractedData,
          use_splink: useSplinkMatch,
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erro na simulação");
      setPreviewData(data.resultados || []);
      setViewMode('preview');
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || "Falha ao simular conciliação.");
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCommitBaixas = async () => {
    if (!previewData || previewData.length === 0) return;
    
    const validos = previewData.filter(d => d.status === "MATCH_PERFEITO" && d.id_receber);
    if (validos.length === 0) {
      alert("Nenhum registro com MATCH_PERFEITO para gravar.");
      return;
    }
    
    if (!confirm(`Gravar ${validos.length} parcelas como PAGAS direto no Vulcano? Esta ação é IRREVERSÍVEL.`)) return;
    
    try {
      setIsCommitting(true);
      const payload = validos.map(d => ({
        id_receber: d.id_receber,
        novo_total_pago: d.proposta_ia.novo_total_pago,
        novo_desconto: d.proposta_ia.novo_desconto,
        novo_acrescimo: d.proposta_ia.novo_acrescimo
      }));
      
      const res = await fetch(`${API_BASE}/api/parser/commit-baixas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa, 10),
          lote_efetivado: payload
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erro ao efetivar lote");
      
      alert(`Foram baixadas ${data.baixados} parcelas com sucesso no sistema!`);
      // Opcional: Atualizar extrato ou limpar
      setPreviewData(null);
      setViewMode('raw');
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || "Erro fatal ao gravar lote.");
    } finally {
      setIsCommitting(false);
    }
  };

  // Importante: se o backend retornar 0 linhas, ainda mostramos a área de trabalho
  // para o operador ver o feedback (chat/erro) e ajustar o fluxo.
  const showWorkingView =
    isProcessing ||
    extractedData.length > 0 ||
    hasCode ||
    chatHistory.length > 0 ||
    !!errorMsg;

  const extractOverlay =
    extractForceAi || (!pickTemplateId && !selectedEmpresa)
      ? {
          title: 'Extração com IA',
          subtitle: 'Contatando a API Gemini e estruturando os valores…',
        }
      : pickTemplateId
        ? {
            title: 'Extração via Ollama/Template',
            subtitle: 'Enviando documento e Instruções (Padrões Salvos)…',
          }
        : {
            title: 'Extração',
            subtitle:
              'Se a empresa tiver parser padrão, roda o script; sem fallback automático para IA nesta rota.',
          };

  return (
    <div className="space-y-6 animate-in fade-in max-w-[1600px] mx-auto w-full h-full flex flex-col pb-4">
      <div className="flex flex-wrap gap-4 justify-between items-end shrink-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter text-[var(--v-text-bold)] uppercase flex items-center gap-3">
            <Zap className="text-[var(--v-accent-5)]" size={36} /> Importador <span className="text-[var(--v-accent-4)]">Multimodal IA</span>
          </h2>
          <p className="text-sm text-[var(--v-text-muted)] mt-2 uppercase tracking-widest font-bold">Lê contratos, extratos e relatórios (PDF ou fotos) via IA Visão.</p>
          <p className="text-[10px] text-[var(--v-text-faint)] mt-2 uppercase tracking-widest font-bold">API: {API_BASE}</p>
        </div>
        <div className="flex flex-col items-end gap-3">
          <div className="flex bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden p-[2px]">
             {['vendas', 'recebimentos', 'conciliacao'].map(m => (
               <button 
                 key={m}
                 onClick={() => setImportMode(m)}
                 className={`px-4 py-2 text-[10px] uppercase font-bold tracking-widest transition-colors ${importMode === m ? 'bg-[#007aff] text-[var(--v-text-bold)]' : 'text-[var(--v-text-faint)] hover:text-[#bbb]'}`}
               >
                 {m === 'conciliacao' ? 'Conciliação Bancária' : m}
               </button>
             ))}
          </div>
          {hasCode && (
            <button
              type="button"
              onClick={handleDownloadCode}
              className="bg-[var(--v-hover)] border border-[#007aff]/50 text-[var(--v-accent-4)] hover:bg-[#007aff] hover:text-[var(--v-text-bold)] py-2 px-6 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] transition-colors flex items-center gap-2"
            >
              <Download size={14} /> Baixar .py
            </button>
          )}
          {showWorkingView && (
            <button
              type="button"
              onClick={resetSession}
              className="bg-[var(--v-card)] border border-[var(--v-border)] text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)] hover:border-[#555] py-2 px-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] transition-colors"
            >
              Novo PDF
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 items-center bg-[var(--v-card)] border border-[var(--v-border)] p-3 rounded-[var(--v-radius)]">
        <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Modelos salvos</span>
        <select
          value={pickTemplateId}
          onChange={(e) => setPickTemplateId(e.target.value)}
          className="bg-[var(--v-deep)] border border-[var(--v-border)] text-xs text-[var(--v-text-bold)] px-2 py-2 rounded-[var(--v-radius)] min-w-[200px] outline-none focus:border-[#007aff]"
        >
          <option value="">— selecione —</option>
          {savedTemplates.map((t) => (
            <option key={t.id} value={String(t.id)}>
              {t.nome || `Modelo #${t.id}`}
              {t.is_padrao_empresa ? ' ★' : ''}
            </option>
          ))}
        </select>
        {pickTemplateId && (
          <button
            type="button"
            onClick={async () => {
              if(!confirm('Tem certeza que deseja apagar este modelo salvo? Isso não tem como desfazer.')) return;
              try {
                const res = await fetch(`${API_BASE}/api/parser/template/${pickTemplateId}`, { method: 'DELETE' });
                if(!res.ok) throw new Error();
                setPickTemplateId('');
                fetchTemplates();
                alert('Deletado com sucesso.');
              } catch(e) {
                alert('Falha ao deletar o modelo.');
              }
            }}
            className="bg-[var(--v-hover)] border border-[#ff4d00]/40 text-[var(--v-accent)] hover:bg-[var(--v-accent)] hover:text-black p-2 rounded-[var(--v-radius)] transition-colors flex items-center justify-center"
            title="Excluir este modelo"
          >
            <Trash2 size={16} />
          </button>
        )}
        <button
          type="button"
          onClick={handleLoadSavedTemplate}
          disabled={!pickTemplateId}
          className="bg-[var(--v-hover)] border border-[#a259ff]/40 text-[var(--v-accent-5)] hover:bg-[#a259ff] hover:text-black py-2 px-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] disabled:opacity-50 transition-colors"
        >
          Carregar código
        </button>
        <button
          type="button"
          onClick={handleSetPadraoLista}
          disabled={!selectedEmpresa || !pickTemplateId}
          className="bg-[var(--v-hover)] border border-[#34c759]/40 text-[var(--v-accent-3)] hover:bg-[#34c759] hover:text-black py-2 px-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] disabled:opacity-50 transition-colors"
          title="Marca o modelo escolhido como padrão da empresa selecionada no topo do app"
        >
          Definir padrão empresa
        </button>
      </div>

      {errorMsg && (
        <div className="bg-[var(--v-card)] border border-[#ff4d00]/50 p-4 rounded-[var(--v-radius)] text-[var(--v-accent)] text-xs font-bold uppercase tracking-widest">
          {errorMsg}
        </div>
      )}

      {!showWorkingView ? (
        <div className="bg-[var(--v-card)] border border-[var(--v-border)] p-8 rounded-[var(--v-radius)] text-center max-w-2xl mx-auto w-full mt-10 shadow-xl">
          <FileText size={64} className="mx-auto text-[var(--v-accent-4)] mb-6" />
          <h3 className="text-xl font-bold text-[var(--v-text-bold)] mb-2 uppercase tracking-widest">Extrator + Chat de Ajuste</h3>
          <p className="text-[var(--v-text-muted)] text-sm mb-8">Envie o PDF. O sistema extrai os valores, você corrige via chat e depois gera um `.py` para reutilizar nas próximas importações.</p>
          
          <div className="max-w-md mx-auto flex flex-col gap-4">
            <input 
              type="file" 
              accept="application/pdf,image/png,image/jpeg,image/jpg"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
            />
            <button
               onClick={() => fileInputRef.current.click()}
               className="w-full bg-[var(--v-deep)] border border-[var(--v-border)] hover:border-[#007aff] text-[var(--v-text-bold)] py-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-xs transition-colors flex justify-center items-center gap-2"
            >
              <UploadCloud size={16} /> {pdfFile ? pdfFile.name : `Escolher Arquivo de ${importMode.toUpperCase()} (PDF/Imagem)`}
            </button>
            <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[var(--v-text-muted)] cursor-pointer select-none justify-center">
              <input
                type="checkbox"
                checked={extractForceAi}
                onChange={(e) => setExtractForceAi(e.target.checked)}
                className="accent-[#007aff]"
              />
              Só IA (ignorar modelo / padrão da empresa)
            </label>
            <p className="text-[10px] text-[var(--v-text-faint)] text-center leading-relaxed max-w-md mx-auto">
              Com modelo na barra acima (ou padrão da empresa no topo), a extração roda o Python salvo — sem Gemini.
            </p>
            <button 
              onClick={handleExtract}
              disabled={isProcessing || !pdfFile} 
              className="w-full bg-[#007aff] text-[var(--v-text-bold)] py-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] hover:bg-[#005bb5] transition-colors disabled:opacity-50 flex justify-center items-center gap-2 shadow-[0_0_10px_rgba(0,122,255,0.4)]"
            >
              {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
              {isProcessing ? 'Extraindo...' : extractForceAi ? 'Extrair com IA (Gemini)' : 'Extrair PDF'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden relative">
          {isProcessing && (
            <div className="absolute inset-0 bg-[var(--v-deep)]/80 backdrop-blur-md flex flex-col items-center justify-center z-10 rounded-[var(--v-radius)] border border-[var(--v-border)]">
              <Loader2 className="animate-spin text-[var(--v-accent-4)] mb-6" size={48} />
              <h3 className="text-xl font-bold uppercase tracking-widest text-[var(--v-text-bold)] mb-2">{extractOverlay.title}</h3>
              <p className="text-sm font-bold text-[var(--v-text-muted)] tracking-wide text-center max-w-md px-4 leading-relaxed">
                {extractOverlay.subtitle}
              </p>
            </div>
          )}

          {extractedData.length > 0 && (
            <div className={`grid grid-cols-12 gap-6 flex-1 overflow-hidden min-h-[280px] ${isFullscreen ? 'fixed inset-0 z-50 bg-[var(--v-bg)] p-6' : ''}`}>
              <div className={`${isFullscreen ? 'col-span-12' : 'col-span-8'} bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col overflow-hidden shadow-xl`}>
                <div className="p-4 bg-[var(--v-hover)] border-b border-[var(--v-border)] space-y-3">
                  <div className="flex flex-wrap gap-3">
                    <input
                      value={templateNome}
                      onChange={(e) => setTemplateNome(e.target.value)}
                      placeholder="Nome do modelo (ex.: Fatura Fornecedor X)"
                      className="flex-1 min-w-[160px] bg-[var(--v-deep)] border border-[var(--v-border)] p-2 text-[11px] text-[var(--v-text-bold)] outline-none focus:border-[#ffcc00] transition-colors"
                    />
                    <input
                      value={templateDescricao}
                      onChange={(e) => setTemplateDescricao(e.target.value)}
                      placeholder="Descrição (opcional)"
                      className="flex-1 min-w-[160px] bg-[var(--v-deep)] border border-[var(--v-border)] p-2 text-[11px] text-[var(--v-text-bold)] outline-none focus:border-[#ffcc00] transition-colors"
                    />
                    <button
                      onClick={handleGeneratePython}
                      disabled={isSaving}
                      className="bg-[var(--v-hover)] border border-[#ffcc00]/50 text-[var(--v-accent-6)] hover:bg-[#ffcc00] hover:text-black px-6 py-2 font-bold uppercase tracking-widest text-[10px] rounded-[var(--v-radius)] disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
                      title="Força a IA a escrever um manifest Python para toda a abstração acima ficar salva pra sempre"
                    >
                      {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Code size={14} />}
                      {isSaving ? 'Gerando Script...' : 'Salvar Regra .PY'}
                    </button>
                  </div>
                  {selectedEmpresa && (
                    <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[var(--v-text-muted)] cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={definirPadrao}
                        onChange={(e) => setDefinirPadrao(e.target.checked)}
                        className="accent-[#34c759]"
                      />
                      Definir como padrão desta empresa ao gerar .py
                    </label>
                  )}
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="flex bg-[var(--v-deep)] rounded-[var(--v-radius)] p-1 border border-[var(--v-border)]">
                        <button 
                          onClick={() => setViewMode('raw')} 
                          className={`px-4 py-1.5 text-[10px] uppercase font-bold tracking-widest rounded-[var(--v-radius)] transition-colors ${viewMode === 'raw' ? 'bg-[#a259ff] text-[var(--v-text-bold)]' : 'text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)]'}`}
                        >
                          JSON Cru
                        </button>
                        <button 
                          onClick={() => setViewMode('preview')} 
                          className={`px-4 py-1.5 text-[10px] uppercase font-bold tracking-widest rounded-[var(--v-radius)] transition-colors flex items-center gap-2 ${viewMode === 'preview' ? 'bg-[#34c759] text-black' : 'text-[var(--v-text-muted)] hover:text-[var(--v-accent-3)]'}`}
                        >
                          <ShieldAlert size={12}/> {previewData ? 'Lote Conciliado' : 'Simulação'}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {/* Toggle Splink */}
                      <button
                        id="btn-toggle-splink"
                        onClick={() => setUseSplinkMatch(v => !v)}
                        title={useSplinkMatch ? 'Modo: Splink Probabilístico (clique para voltar ao Heurístico)' : 'Modo: Heurístico (clique para usar Splink)'}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded text-[10px] font-black uppercase tracking-widest border transition-all ${
                          useSplinkMatch
                            ? 'bg-[#a259ff]/20 border-[#a259ff]/60 text-[var(--v-accent-5)] shadow-[0_0_10px_rgba(162,89,255,0.3)]'
                            : 'bg-[var(--v-hover)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent-5)] hover:border-[#a259ff]/40'
                        }`}
                      >
                        <Zap size={12} className={useSplinkMatch ? 'text-[var(--v-accent-5)]' : 'text-[var(--v-text-faint)]'}/>
                        {useSplinkMatch ? 'Splink ON' : 'Splink OFF'}
                      </button>
                      <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="bg-[var(--v-hover)] border border-[var(--v-border)] hover:border-[#a259ff] text-[var(--v-text-muted)] hover:text-[#fff] px-3 py-2 rounded transition-colors text-[10px] font-bold uppercase tracking-widest flex items-center gap-2"
                      >
                         {isFullscreen ? <><Minimize size={14}/> Ocultar Expansão</> : <><Maximize size={14}/> Expandir Tabela</>}
                      </button>
                      <button
                        onClick={viewMode === 'raw' ? handlePreviewBaixas : handleCommitBaixas}
                        disabled={viewMode === 'raw' ? isSimulating : isCommitting}
                        className={`px-6 py-3 rounded text-[11px] font-black tracking-widest text-[var(--v-text-bold)] uppercase disabled:opacity-50 transition-all flex items-center gap-2`}
                        style={{
                          background: viewMode === 'raw' 
                            ? 'linear-gradient(90deg, #9333ea, #3b82f6)' 
                            : 'linear-gradient(90deg, #22c55e, #10b981)',
                          boxShadow: viewMode === 'raw' 
                            ? '0 0 20px rgba(147,51,234,0.4)'
                            : '0 0 20px rgba(34,197,94,0.4)',
                        }}
                      >
                        {viewMode === 'raw' ? (
                          <>
                            {isSimulating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Loader2 className="w-4 h-4" />}
                            CONCILIAR COM BANCO
                          </>
                        ) : (
                          <>
                            {isCommitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            EFETIVAR LOTE NO VULCANO
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
                
                {viewMode === 'raw' ? (
                  <div className="flex-1 overflow-auto p-4 bg-black custom-scrollbar">
                    <pre className="text-[11px] font-mono text-[var(--v-text)] leading-relaxed">
                      <code>{JSON.stringify(extractedData.slice(0, 200), null, 2)}</code>
                    </pre>
                    {extractedData.length > 200 && (
                      <div className="mt-4 text-[10px] uppercase tracking-widest font-bold text-[var(--v-text-faint)]">
                        Mostrando apenas 200 primeiras linhas (para não travar o navegador).
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex-1 overflow-auto custom-scrollbar bg-[var(--v-deep)]">
                    {!previewData ? (
                       <div className="h-full flex items-center justify-center p-8 text-[var(--v-text-faint)] text-xs font-bold uppercase tracking-widest text-center">
                         Clique em "Conciliar com Banco" para realizar a busca no banco de dados e bater o Arquivo contra o Contas a Receber da empresa selecionada.
                       </div>
                    ) : (
                       <table className="w-full text-left border-collapse text-xs">
                         <thead>
                           <tr className="bg-[var(--v-deep)] sticky top-0 border-b border-[var(--v-border)]">
                             <th className="p-3 text-[10px] uppercase tracking-widest text-[var(--v-text-muted)]">Linha PDF</th>
                             <th className="p-3 text-[10px] uppercase tracking-widest text-[var(--v-text-muted)]">Match Vulcano</th>
                             <th className="p-3 text-[10px] uppercase tracking-widest text-right text-[var(--v-text-muted)]">Valor PDF</th>
                             <th className="p-3 text-[10px] uppercase tracking-widest text-right text-[var(--v-text-muted)]">Valor Guiado</th>
                             <th className="p-3 text-[10px] uppercase tracking-widest text-center text-[var(--v-text-muted)]">Ação Prevista</th>
                           </tr>
                         </thead>
                         <tbody>
                           {previewData.map((d, i) => {
                             const isProjetada = d.status === 'PROJETADA_NOVA_LINHA';
                             const isJaPago = d.status === 'ALERTA_JA_PAGO';
                             const isAcessorio = d.status !== 'MATCH_PERFEITO' && !isProjetada && !isJaPago && (d.row.total_pago < 300 || d.row.valor_raiz === 0);
                             const isExpanded = expandedRowIndex === i;
                             return (
                             <React.Fragment key={i}>
                               <tr className={`border-b border-[var(--v-border)] ${d.status === 'MATCH_PERFEITO' ? 'hover:bg-[#34c759]/5' : isProjetada ? 'hover:bg-[#007aff]/10 bg-[#007aff]/5' : isJaPago ? 'hover:bg-[#ff9500]/5 bg-[#ff9500]/10' : isAcessorio ? 'hover:bg-[#333]/30 bg-[var(--v-deep)]' : 'hover:bg-[var(--v-accent)]/5 bg-[var(--v-accent)]/10'}`}>
                                 <td className="p-3 text-[var(--v-text)] align-top max-w-[300px]">
                                    <div className="font-bold text-[var(--v-text)] mb-2">{d.row.comprador || d.row.cpf_cnpj || '---'}</div>
                                    <div className="flex flex-wrap gap-1.5">
                                      {Object.entries(d.row).filter(([k,v]) => v !== null && v !== '').map(([k, v]) => (
                                        <div key={k} className="bg-[var(--v-hover)] border border-[var(--v-border)] px-1.5 py-0.5 rounded-[var(--v-radius)] text-[9px] uppercase tracking-widest flex items-center gap-1 shadow-sm">
                                          <span className="text-[var(--v-accent-5)] font-bold">{k}:</span>
                                          <span className="text-[#fff]">{String(v)}</span>
                                        </div>
                                      ))}
                                    </div>
                                 </td>
                                 <td className="p-3 align-top min-w-[200px]">
                                    {d.status === 'MATCH_PERFEITO' ? (
                                      <>
                                        <div className="font-bold text-[var(--v-accent-3)] flex items-center gap-1"><CheckCircle2 size={12}/> ID: {d.id_receber} - Encontrado</div>
                                        <div className="text-[10px] text-[var(--v-text-muted)] mt-1">Vencimento: {d.db_estado_atual.vencimento} (Parc {d.db_estado_atual.parcela})</div>
                                        <div className="text-[10px] text-[var(--v-text-muted)]">Status Banco: {d.db_estado_atual.pago_hoje > 0 ? `Pago ${formatCurrency(d.db_estado_atual.pago_hoje)}` : 'Aberto'}</div>
                                        {d.match_engine && (
                                          <div className="mt-1.5 flex items-center gap-1.5">
                                            <span className={`text-[9px] font-black px-1.5 py-0.5 rounded uppercase ${d.match_engine === 'splink' ? 'bg-[#a259ff]/20 text-[var(--v-accent-5)] border border-[#a259ff]/30' : 'bg-[var(--v-hover)] text-[var(--v-text-faint)] border border-[var(--v-border)]'}`}>
                                              {d.match_engine === 'splink' ? 'Splink' : 'Heuristico'}
                                            </span>
                                            {d.match_probability != null && <span className="text-[9px] font-mono text-[var(--v-text-faint)]">P={Math.round(d.match_probability*100)}%</span>}
                                          </div>
                                        )}
                                      </>
                                    ) : isJaPago ? (
                                      <>
                                        <div className="font-bold text-[#ff9500] flex items-center gap-1"><Lock size={12}/> ID: {d.id_receber || '—'} — JÁ QUITADA</div>
                                        <div className="text-[10px] text-[var(--v-text-muted)] mt-1">Vencimento: {d.db_estado_atual?.vencimento} (Parc {d.db_estado_atual?.parcela})</div>
                                        <div className="text-[10px] text-[#ff9500] mt-1 bg-[#ff9500]/10 px-1 inline-block border border-[#ff9500]/30 rounded">
                                          Pago no ERP: {formatCurrency(d.db_estado_atual?.pago_hoje)}
                                        </div>
                                      </>
                                    ) : isProjetada ? (
                                      <>
                                        <div className="font-bold text-[var(--v-accent-4)] flex items-center gap-1"><Sparkles size={12}/> ⚡ FUTURA (SERÁ GERADA)</div>
                                        <div className="text-[10px] text-[var(--v-text-muted)] mt-1">Previsto: {d.db_estado_atual.vencimento} - {d.db_estado_atual.parcela}</div>
                                        <div className="text-[10px] text-[var(--v-accent-4)] mt-1 bg-[#007aff]/10 px-1 inline-block border border-[#007aff]/30 rounded">Linha será induzida no RECEBER</div>
                                      </>
                                    ) : (
                                      <>
                                        <div className={`font-bold text-[10px] uppercase ${isAcessorio ? 'text-[var(--v-accent-6)]' : 'text-[var(--v-accent)]'}`}>
                                          {isAcessorio ? (
                                             <span className="flex items-center gap-1"><AlertCircle size={10} /> Dado Avulso (Multa/Desconto?)</span>
                                          ) : 'Não Localizado / Divergente'}
                                        </div>
                                        {isAcessorio && <div className="text-[9px] text-[var(--v-text-muted)] mt-1">Lançamento sem parcela raiz associada.</div>}
                                      </>
                                    )}
                                 </td>
                                 <td className="p-3 align-top text-right text-[var(--v-text-bold)] font-mono">{formatCurrency(d.row.total_pago)}</td>
                                 <td className="p-3 align-top text-right text-[var(--v-text-muted)] font-mono">{d.db_estado_atual ? formatCurrency(d.db_estado_atual.valor_parcela) : '-'}</td>
                                 <td className="p-3 align-top flex flex-col items-center gap-2">
                                   {d.status === 'MATCH_PERFEITO' || isProjetada ? (
                                     <span className={`${isProjetada ? 'bg-[#007aff] hover:bg-[#005bb5]' : 'bg-[#34c759] hover:bg-[#2da94f]'} text-${isProjetada ? 'white' : 'black'} px-2 py-1 rounded-[var(--v-radius)] tracking-widest shadow-sm text-[10px] font-bold uppercase w-full text-center transition-colors`}>
                                       {isProjetada ? 'PROJETAR + BAIXAR' : 'BAIXAR'}
                                     </span>
                                   ) : isJaPago ? (
                                     <span className="bg-[#ff9500] text-black px-2 py-1 rounded-[var(--v-radius)] tracking-widest shadow-sm text-[10px] font-bold uppercase w-full text-center flex items-center justify-center gap-1">
                                       <Lock size={10}/> JÁ PAGO
                                     </span>
                                   ) : (
                                     <span className={`${isAcessorio ? 'bg-[#333] text-[#fff]' : 'bg-[var(--v-accent)] text-black'} px-2 py-1 rounded-[var(--v-radius)] tracking-widest shadow-sm text-[10px] font-bold uppercase w-full text-center`}>
                                       IGNORAR
                                     </span>
                                   )}
                                   <button 
                                     onClick={() => setExpandedRowIndex(isExpanded ? null : i)}
                                     className="mt-1 flex items-center gap-1 text-[9px] uppercase tracking-widest font-bold text-[var(--v-text-muted)] hover:text-[#fff] transition-colors"
                                   >
                                     {isExpanded ? <><ChevronUp size={12} /> Ocultar</> : <><ChevronDown size={12} /> Detalhes</>}
                                   </button>
                                 </td>
                               </tr>
                               {isExpanded && (
                                 <tr className="bg-[var(--v-deep)] border-b border-[var(--v-border)]">
                                   <td colSpan="5" className="p-4">
                                      <div className="border border-[var(--v-border)] rounded overflow-hidden">
                                        <table className="w-full text-left text-[10px] font-mono">
                                          <thead className="bg-[var(--v-hover)]">
                                            <tr>
                                              <th className="p-2 border-b border-[var(--v-border)] text-[var(--v-accent-6)] uppercase tracking-widest font-bold w-1/2">Extraído do PDF (Importado)</th>
                                              <th className="p-2 border-b border-[var(--v-border)] text-[var(--v-accent-4)] uppercase tracking-widest font-bold w-1/2">Parcela ERP (Em Aberto no Vulcano)</th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            <tr>
                                              <td className="p-3 border-r border-[var(--v-border)] align-top bg-[var(--v-deep)]">
                                                {Object.entries(d.row).map(([k,v]) => (
                                                  <div key={k} className="flex justify-between border-b border-[var(--v-border)] py-1">
                                                    <span className="text-[var(--v-text-muted)]">{k}</span>
                                                    <span className="text-[var(--v-text-bold)] text-right max-w-[200px] break-all">{String(v)}</span>
                                                  </div>
                                                ))}
                                              </td>
                                              <td className="p-3 align-top bg-[var(--v-deep)]">
                                                {d.db_estado_atual ? Object.entries(d.db_estado_atual).map(([k,v]) => (
                                                  <div key={k} className="flex justify-between border-b border-[var(--v-border)] py-1">
                                                    <span className="text-[var(--v-text-muted)]">{k}</span>
                                                    <span className="text-[var(--v-text-bold)] text-right max-w-[200px] break-all">{String(v)}</span>
                                                  </div>
                                                )) : (
                                                  <div className="text-[var(--v-text-faint)] italic mt-2 text-center text-xs">Parcela não localizada para exibir deparamente.</div>
                                                )}
                                              </td>
                                            </tr>
                                          </tbody>
                                        </table>
                                      </div>
                                   </td>
                                 </tr>
                               )}
                             </React.Fragment>
                             )
                           })}
                         </tbody>
                       </table>
                    )}
                  </div>
                )}
              </div>

              {!isFullscreen && (
                <div className="col-span-4 bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col overflow-hidden shadow-xl">
                  {/* TAB HEADER */}
                  <div className="flex border-b border-[var(--v-border)] shrink-0">
                    <button
                      onClick={() => setChatTab('chat')}
                      className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-widest text-center transition-colors border-r border-[var(--v-border)] flex items-center justify-center gap-2 ${chatTab === 'chat' ? 'bg-[var(--v-hover)] text-[var(--v-accent-5)] border-t-2 border-t-[#a259ff]' : 'bg-[var(--v-deep)] text-[var(--v-text-muted)] hover:bg-[var(--v-hover)] border-t-2 border-transparent'}`}
                    >
                      <MessageSquare size={14}/> Chat de Ajustes
                    </button>
                    <button
                      onClick={() => setChatTab('pdf_samples')}
                      className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-widest text-center transition-colors flex items-center justify-center gap-2 ${chatTab === 'pdf_samples' ? 'bg-[var(--v-hover)] text-[var(--v-accent-4)] border-t-2 border-t-[#007aff]' : 'bg-[var(--v-deep)] text-[var(--v-text-muted)] hover:bg-[var(--v-hover)] border-t-2 border-transparent'}`}
                    >
                      <FileText size={14}/> Amostras Limpas
                      {selectedRawLines.length > 0 && (
                        <span className="bg-[#007aff] text-[var(--v-text-bold)] px-1.5 py-0.5 rounded-[var(--v-radius)] text-[9px] leading-none ml-1">{selectedRawLines.length}</span>
                      )}
                    </button>
                  </div>

                  {chatTab === 'chat' ? (
                    <>
                      <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)] flex items-center justify-between shrink-0">
                        <div className="text-[9px] uppercase tracking-widest font-bold text-[var(--v-text-muted)]">
                          Status: <span className={isChatting ? 'text-[var(--v-accent-6)]' : 'text-[var(--v-accent-3)]'}>{isChatting ? 'processando...' : 'pronto'}</span>
                        </div>
                      </div>
                      <div className="flex-1 overflow-y-auto p-4 bg-[var(--v-deep)] custom-scrollbar space-y-3 min-h-0">
                        {chatHistory.map((m, idx) => (
                          <div key={idx} className={`text-xs leading-relaxed ${m.role === 'user' ? 'text-[var(--v-text-bold)]' : 'text-[var(--v-text-muted)]'}`}>
                            <span className={`text-[10px] font-bold uppercase tracking-widest ${m.role === 'user' ? 'text-[var(--v-accent-6)]' : 'text-[var(--v-accent-5)]'}`}>
                              {m.role === 'user' ? 'Você' : 'IA'}
                            </span>
                            <div className="mt-1 whitespace-pre-wrap break-words">{m.content}</div>
                          </div>
                        ))}
                        {chatHistory.length === 0 && (
                          <div className="text-[10px] uppercase tracking-widest font-bold text-[var(--v-text-faint)]">
                            Ex.: “Remover linhas sem data”, “Corrigir parcela 01/10A para 01/10”, “Trocar vírgula por ponto em valor_parcela”.
                          </div>
                        )}
                      </div>
                      <div className="p-4 border-t border-[var(--v-border)] bg-[var(--v-deep)] shrink-0">
                        <div className="flex gap-2">
                          <input
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChatAdjust(); } }}
                            placeholder="Diga como corrigir os dados..."
                            className="flex-1 bg-[var(--v-deep)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#a259ff]"
                            disabled={isChatting}
                          />
                          <button
                            onClick={handleChatAdjust}
                            disabled={isChatting || !chatInput.trim()}
                            className="bg-[#a259ff] text-black px-3 py-2 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] disabled:opacity-60 flex items-center gap-2"
                          >
                            {isChatting ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                            Enviar
                          </button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)] flex items-center justify-between shrink-0">
                        <div className="text-[9px] uppercase tracking-widest font-bold text-[var(--v-text-muted)]">
                          Marque as linhas onde a IA errou (Máx: 5)
                        </div>
                        <div className="text-[9px] uppercase tracking-widest font-bold text-[var(--v-accent-4)]">
                          {selectedRawLines.length}/5
                        </div>
                      </div>
                      <div className="flex-1 overflow-y-auto bg-[var(--v-deep)] custom-scrollbar min-h-0">
                        {rawPdfLines.length === 0 ? (
                          <div className="p-8 text-[var(--v-text-faint)] text-xs uppercase text-center font-bold tracking-widest">Nenhuma amostra carregada. Extraia um PDF primeiro.</div>
                        ) : (
                          <div className="p-2 space-y-1">
                            {rawPdfLines.map((line, idx) => {
                              const isSelected = selectedRawLines.includes(idx);
                              return (
                                <label key={idx} className={`block p-2 text-[10px] font-mono whitespace-pre-wrap break-all border rounded cursor-pointer transition-colors ${isSelected ? 'bg-[#007aff]/10 border-[#007aff] text-[var(--v-text-bold)]' : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-muted)] hover:bg-[var(--v-hover)]'}`}>
                                  <div className="flex items-start gap-2">
                                    <input type="checkbox" className="mt-0.5 accent-[#007aff]" checked={isSelected}
                                      onChange={(e) => {
                                        if (e.target.checked) {
                                          if (selectedRawLines.length >= 5) { alert('Máximo de 5 linhas para não sobrecarregar a memória da IA!'); return; }
                                          setSelectedRawLines([...selectedRawLines, idx]);
                                        } else {
                                          setSelectedRawLines(selectedRawLines.filter(x => x !== idx));
                                        }
                                      }}
                                    />
                                    <span>{line}</span>
                                  </div>
                                </label>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {hasCode && (
            <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col shadow-xl overflow-hidden mt-4 max-h-[min(480px,50vh)]">
               <div className="p-4 bg-[var(--v-hover)] border-b border-[var(--v-border)] flex flex-wrap items-center justify-between gap-2 shadow-xl z-10">
                 <div className="flex items-center gap-3">
                   <Code size={18} className="text-[var(--v-accent-3)]" />
                   <h3 className="text-xs font-bold text-[var(--v-text-bold)] uppercase tracking-widest leading-none">Script gerado (preview)</h3>
                 </div>
                 <div className="text-[10px] uppercase font-bold tracking-widest text-[var(--v-text-faint)] flex flex-wrap items-center gap-2">
                   <CheckCircle2 size={14} className="text-[var(--v-accent-3)]" />
                   {lastTemplateId != null && <span>Registro #{lastTemplateId}</span>}
                   <span>{codeStats.lines} linhas · {codeStats.chars.toLocaleString('pt-BR')} caracteres</span>
                 </div>
               </div>
               <div className="flex-1 overflow-auto p-6 custom-scrollbar bg-black min-h-0">
                 <pre className="text-[11px] font-mono text-[var(--v-accent-5)] leading-relaxed whitespace-pre-wrap break-words">
                   <code>{codePreview}</code>
                 </pre>
               </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
