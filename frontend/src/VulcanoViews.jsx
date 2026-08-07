import React, { useState, useEffect, useMemo, useRef } from 'react';
import { createPortal } from 'react-dom';
import { 
    Download, RefreshCw, Upload, Play, CheckCircle2, CheckCircle, ChevronDown, ChevronLeft, ChevronRight, Layers, Activity,
    Database, TableProperties, Fingerprint, TrendingUp, Search, X, Maximize2, RotateCcw,
    Zap, Link as LinkIcon, Cpu, AlertCircle, FileText, CheckSquare, MessageSquare, Plus, PlusCircle, PenTool, Hash, Filter,
    LayoutGrid, History, ListFilter, ShoppingCart, Users, DollarSign, Building2, Loader2, ShieldAlert,
    UploadCloud, Send, Save, Trash2, Code, FileSpreadsheet, Minimize, Maximize, Sparkles, ChevronUp, Lock, Pencil
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { API_BASE } from './apiBase';
import * as XLSX from 'xlsx';




const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const DashboardMeta = ({ selectedEmpresa }) => {
    const [data, setData] = useState(null);
    const [lancamentos, setLancamentos] = useState(null);
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
        Promise.all([
            fetch(`${API_BASE}/api/receitas-caixa?empresa_id=${selectedEmpresa}${dataIniFilter ? `&data_ini=${dataIniFilter}` : ''}${dataFimFilter ? `&data_fim=${dataFimFilter}` : ''}`).then(res => res.json()),
            fetch(`${API_BASE}/api/vulcano/dashboard-lancamentos?empresa_id=${selectedEmpresa}`).then(res => res.json()).catch((err) => ({ error: err.message }))
        ])
        .then(([caixaJson, lancJson]) => {
            setData(caixaJson);
            setLancamentos(lancJson);
            setLoading(false);
        })
        .catch(err => {
            console.error("Dashboard Fetch Error:", err);
            setError(err.message);
            setLoading(false);
        });
    }, [selectedEmpresa, fetchTrigger, dataIniFilter, dataFimFilter]);

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
                            className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono pl-9 py-1.5 rounded outline-none placeholder-[#444] transition-colors"
                        />
                    </div>
                </div>
                <div>
                    <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Mês Inicial</label>
                    <input type="month" value={dataIniFilter} onChange={(e) => setDataIniFilter(e.target.value)} className="min-w-[140px] bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono px-3 py-1.5 rounded outline-none transition-colors dark-calendar" />
                </div>
                <div>
                    <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Mês Final</label>
                    <input type="month" value={dataFimFilter} onChange={(e) => setDataFimFilter(e.target.value)} className="min-w-[140px] bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-3)] text-white text-[11px] font-mono px-3 py-1.5 rounded outline-none transition-colors dark-calendar" />
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

            {/* Marcadores de Delay da Escrituração */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 mb-6">
                {!lancamentos ? (
                    <div className="col-span-2 magma-card p-6 flex items-center justify-center text-[var(--v-text-muted)] animate-pulse">
                        <RefreshCw className="animate-spin mr-3" size={16} /> 
                        <span className="text-[10px] uppercase font-bold tracking-widest">Carregando indicadores de escrituração...</span>
                    </div>
                ) : (
                    (() => {
                        if (lancamentos.error) {
                            return (
                                <div className="col-span-2 magma-card p-6 flex items-center justify-center text-[var(--v-error)]">
                                    <AlertCircle className="mr-3" size={16} /> 
                                    <span className="text-[10px] uppercase font-bold tracking-widest">Erro na busca: {lancamentos.error}</span>
                                </div>
                            );
                        }
                        
                        const renderDelayMarker = (items, label, icon) => {
                            if (!items || items.length === 0) return (
                                <div className="magma-card p-4 flex items-center gap-4">
                                    <div className="p-3 bg-[var(--v-surface-container)] rounded-full text-[var(--v-text-muted)]">
                                        {icon}
                                    </div>
                                    <div>
                                        <h4 className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-faint)]">{label}</h4>
                                        <p className="text-sm font-bold text-[var(--v-error)]">Sem resposta do servidor</p>
                                    </div>
                                </div>
                            );
                            
                            const lastDateStr = items[0].data; // DD/MM/YYYY
                            const [d, m, y] = lastDateStr.split('/');
                            const lastDate = new Date(y, m - 1, d);
                            const now = new Date();
                            const diffTime = Math.abs(now - lastDate);
                            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                            const diffMonths = (now.getFullYear() - lastDate.getFullYear()) * 12 + (now.getMonth() - lastDate.getMonth());
                            
                            let statusColor = "var(--v-accent-3)";
                            let statusText = "Em Dia";
                            
                            if (diffMonths > 1) {
                                statusColor = "var(--v-error)";
                                statusText = `Atraso (${diffMonths} meses)`;
                            } else if (diffDays > 15) {
                                statusColor = "var(--v-accent-2)";
                                statusText = `Atenção (${diffDays} dias)`;
                            }

                            return (
                                <div className="magma-card p-4 flex items-center gap-4 border-l-[3px]" style={{ borderLeftColor: statusColor }}>
                                    <div className="p-3 bg-[var(--v-surface-container)] rounded-full" style={{ color: statusColor }}>
                                        {icon}
                                    </div>
                                    <div className="flex-1">
                                        <h4 className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)]">{label}</h4>
                                        <div className="flex justify-between items-end mt-1">
                                            <span className="text-xl font-black text-[var(--v-text-bold)]">{lastDateStr}</span>
                                            <span className="text-[9px] uppercase font-black tracking-widest px-2 py-1 rounded" style={{ backgroundColor: `${statusColor}22`, color: statusColor }}>
                                                {statusText}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        };

                        return (
                            <>
                                {renderDelayMarker(lancamentos.vendas, 'Status Escrituração de Vendas', <ShoppingCart size={20} />)}
                                {renderDelayMarker(lancamentos.recebimentos, 'Status Contas a Receber (Baixas)', <Database size={20} />)}
                            </>
                        );
                    })()
                )}
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

// Tipos de condicao aceitos pelo backend (POST /api/vulcano/vendas -> VENDAFORMAPAGTO)
const TIPOS_CONDICAO = ['SINAL', 'MENSAL', 'SEMESTRAL', 'ANUAL', 'REFORCO', 'INTERMEDIARIA', 'CHAVES', 'FINANCIAMENTO'];
const TIPOS_PARCELA_UNICA = ['SINAL', 'INTERMEDIARIA', 'CHAVES', 'FINANCIAMENTO'];

// Data local (nao UTC): toISOString() vira "amanha" entre 21h e 0h no Brasil
const hojeLocal = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const NovaVendaModal = ({ selectedEmpresa, empreendimentosList, onClose, onSaved }) => {
  const inputStyle = { background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' };
  const labelCls = "text-[10px] uppercase font-bold mb-2 block";
  const labelStyle = { color: '#8a7a68' };

  const [vendaForm, setVendaForm] = useState({ id_empreendimento: '', data: '', total: '', permuta: 'N', conta_permuta: '', num_contrato: '' });
  const [filtroEmp, setFiltroEmp] = useState('');
  const [filtroUnidade, setFiltroUnidade] = useState('');
  const [compradores, setCompradores] = useState([{ nome: '', cpf_cnpj: '', percentual: 100 }]);

  // divisao igualitaria do contrato entre N compradores (ultimo absorve o arredondamento)
  const redistribuirPercentuais = (lista) => {
    const n = lista.length || 1;
    const base = Math.floor(10000 / n) / 100;
    return lista.map((c, i) => ({ ...c, percentual: i === n - 1 ? Math.round((100 - base * (n - 1)) * 100) / 100 : base }));
  };
  const somaPercentuais = compradores.reduce((acc, c) => acc + (parseFloat(c.percentual) || 0), 0);
  const [condicoes, setCondicoes] = useState([]);
  const [unidadesDisp, setUnidadesDisp] = useState([]);
  const [blocosById, setBlocosById] = useState({});
  const [unidadesSel, setUnidadesSel] = useState([]);
  const [loadingUnidades, setLoadingUnidades] = useState(false);
  const [saving, setSaving] = useState(false);

  const detalhesReqRef = useRef(0);
  const handleSelectEmpreendimento = async (empId) => {
    const reqId = ++detalhesReqRef.current;
    setVendaForm(f => ({ ...f, id_empreendimento: empId }));
    setUnidadesSel([]);
    setUnidadesDisp([]);
    if (!empId) return;
    setLoadingUnidades(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/empreendimentos/${empId}/detalhes`);
      const d = await res.json();
      if (reqId !== detalhesReqRef.current) return; // resposta stale: usuario ja trocou de empreendimento
      const blocos = {};
      (Array.isArray(d?.blocos) ? d.blocos : []).forEach(b => { blocos[b.id] = b.nome; });
      setBlocosById(blocos);
      setUnidadesDisp(Array.isArray(d?.unidades) ? d.unidades : []);
    } catch (e) {
      console.error(e);
    } finally {
      if (reqId === detalhesReqRef.current) setLoadingUnidades(false);
    }
  };

  const toggleUnidade = (uid) => {
    setUnidadesSel(sel => sel.includes(uid) ? sel.filter(i => i !== uid) : [...sel, uid]);
  };

  const buscarClientePorDoc = async (idx) => {
    const doc = (compradores[idx]?.cpf_cnpj || '').replace(/\D/g, '');
    if (!doc || compradores[idx]?.nome) return;
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/clientes/search?cpf_cnpj=${doc}`);
      const d = await res.json();
      const nome = d?.cliente?.nome || d?.nome;
      if (nome) setCompradores(cs => cs.map((c, i) => i === idx ? { ...c, nome } : c));
    } catch (e) { /* lookup opcional */ }
  };

  const setComprador = (idx, patch) => setCompradores(cs => cs.map((c, i) => i === idx ? { ...c, ...patch } : c));
  const setCondicao = (idx, patch) => setCondicoes(cs => cs.map((c, i) => {
    if (i !== idx) return c;
    const novo = { ...c, ...patch };
    if (patch.tipo && TIPOS_PARCELA_UNICA.includes(patch.tipo)) novo.quantidade = 1;
    return novo;
  }));

  const somaCondicoes = condicoes.reduce((acc, c) => acc + (parseFloat(c.valor || 0) * parseInt(c.quantidade || 1)), 0);
  const totalNum = parseFloat(vendaForm.total || 0);
  const divergente = condicoes.length > 0 && Math.abs(somaCondicoes - totalNum) > 0.01;

  const descricaoUnidades = unidadesDisp
    .filter(u => unidadesSel.includes(u.id))
    .map(u => `${blocosById[u.id_bloco] || ''} - ${u.descricao}`.replace(/^ - /, ''))
    .join(' / ');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!vendaForm.id_empreendimento) { alert('Selecione o empreendimento.'); return; }
    if (!vendaForm.data || vendaForm.data < '1990-01-01') {
      alert(`Data da venda inválida (${vendaForm.data || 'vazia'}) — confira o ano (ex.: 2026).`);
      return;
    }
    if (!(compradores[0]?.nome && compradores[0]?.cpf_cnpj)) {
      alert('O 1º comprador (titular da venda) precisa de nome e CPF/CNPJ.');
      return;
    }
    const incompletos = compradores.filter(c => (c.nome || c.cpf_cnpj) && !(c.nome && c.cpf_cnpj));
    if (incompletos.length) {
      alert('Há comprador com nome ou CPF/CNPJ faltando — complete ou remova a linha.');
      return;
    }
    if (compradores.length > 1 && Math.abs(somaPercentuais - 100) > 0.05) {
      alert(`Os percentuais dos compradores somam ${somaPercentuais.toFixed(2)}% — ajuste para fechar 100% (a divisão define o valor de cada CPF na DIMOB/EFD).`);
      return;
    }
    const condSemVenc = condicoes.filter(c => parseFloat(c.valor || 0) > 0 && !c.vencimento);
    if (condSemVenc.length) {
      alert('Há condição de pagamento com valor mas sem 1º vencimento — preencha a data ou remova a linha.');
      return;
    }
    setSaving(true);
    const payload = {
      empresa_id: parseInt(selectedEmpresa),
      id_empreendimento: parseInt(vendaForm.id_empreendimento),
      unidade: descricaoUnidades,
      unidades_selecionadas: unidadesSel,
      data: vendaForm.data,
      total: totalNum,
      permuta: vendaForm.permuta,
      conta_permuta: vendaForm.permuta === 'S' && vendaForm.conta_permuta ? parseInt(vendaForm.conta_permuta) : null,
      num_contrato: vendaForm.num_contrato.trim() || null,
      compradores: compradores.filter(c => c.nome && c.cpf_cnpj).map((c, i) => ({ nome: c.nome, cpf_cnpj: c.cpf_cnpj, percentual: parseFloat(c.percentual) || 0, principal: i === 0 })),
      condicoes: condicoes
        .filter(c => parseFloat(c.valor || 0) > 0 && c.vencimento)
        .map(c => ({ tipo: c.tipo, quantidade: parseInt(c.quantidade || 1), valor: parseFloat(c.valor), vencimento: c.vencimento })),
    };
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      onSaved();
    } catch (err) {
      alert('Erro ao cadastrar venda: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] animate-in fade-in p-6">
      <div className="w-full max-w-5xl rounded-xl shadow-2xl flex flex-col max-h-[92vh]" style={{ background: '#0c0908', border: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="p-6 border-b flex justify-between items-center shrink-0" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
          <h3 className="text-lg font-black uppercase tracking-widest flex items-center gap-3" style={{ color: '#f0e6d8' }}><Plus size={20} color="#ff7a1a"/> Cadastrar Nova Venda</h3>
          <button onClick={onClose} style={{ color: '#8a7a68' }}><X size={20}/></button>
        </div>
        <div className="p-6 overflow-y-auto custom-scrollbar">
          <form className="flex flex-col gap-6" onSubmit={handleSubmit}>

            {/* EMPREENDIMENTO + UNIDADES */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls} style={labelStyle}>Empreendimento</label>
                <input value={filtroEmp} onChange={(e) => setFiltroEmp(e.target.value)} placeholder="Filtrar por nº ou nome..." className="w-full p-2 mb-1.5 rounded text-[11px] outline-none" style={inputStyle} />
                <select value={vendaForm.id_empreendimento} onChange={(e) => handleSelectEmpreendimento(e.target.value)} required size={6} className="w-full p-1 rounded text-[11px] outline-none" style={inputStyle}>
                  {empreendimentosList
                    .filter(emp => !filtroEmp.trim() || `${emp.id} ${emp.nome}`.toLowerCase().includes(filtroEmp.trim().toLowerCase()))
                    .map(emp => <option key={emp.id} value={emp.id} className="py-1">{emp.id} — {emp.nome}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls} style={labelStyle}>Unidades disponíveis {loadingUnidades && '(carregando...)'} {unidadesSel.length > 0 && `· ${unidadesSel.length} selecionada(s)`}</label>
                <input value={filtroUnidade} onChange={(e) => setFiltroUnidade(e.target.value)} placeholder="Filtrar unidade (ex.: 1002, bloco B)..." className="w-full p-2 mb-1.5 rounded text-[11px] outline-none" style={inputStyle} />
                <div className="max-h-36 overflow-y-auto rounded custom-scrollbar p-1" style={inputStyle}>
                  {!vendaForm.id_empreendimento ? (
                    <div className="p-2 text-[10px] uppercase" style={{ color: '#5a4e42' }}>Selecione o empreendimento</div>
                  ) : !unidadesDisp.length && !loadingUnidades ? (
                    <div className="p-2 text-[10px] uppercase" style={{ color: '#5a4e42' }}>Sem unidades livres (vendidas ou sem estrutura)</div>
                  ) : (
                    unidadesDisp
                      .filter(u => {
                        const q = filtroUnidade.trim().toLowerCase();
                        if (!q) return true;
                        return `${blocosById[u.id_bloco] || ''} ${u.descricao}`.toLowerCase().includes(q) || unidadesSel.includes(u.id);
                      })
                      .map(u => (
                      <label key={u.id} className="flex items-center gap-2 px-2 py-1.5 text-[11px] cursor-pointer hover:bg-white/5 rounded" style={{ color: '#f0e6d8' }}>
                        <input type="checkbox" checked={unidadesSel.includes(u.id)} onChange={() => toggleUnidade(u.id)} />
                        <span>{blocosById[u.id_bloco] ? `${blocosById[u.id_bloco]} — ` : ''}{u.descricao}</span>
                        <span className="ml-auto font-mono text-[10px]" style={{ color: '#8a7a68' }}>{u.metragem ? `${u.metragem} m²` : ''}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* DATA / TOTAL / CONTRATO / PERMUTA */}
            <div className="grid grid-cols-4 gap-4">
              <div><label className={labelCls} style={labelStyle}>Data Venda</label><input type="date" min="1990-01-01" value={vendaForm.data} onChange={(e) => setVendaForm({ ...vendaForm, data: e.target.value })} required className="w-full p-3 rounded text-[11px] outline-none dark-calendar" style={inputStyle} /></div>
              <div><label className={labelCls} style={labelStyle}>Total Venda</label><input type="number" step="0.01" value={vendaForm.total} onChange={(e) => setVendaForm({ ...vendaForm, total: e.target.value })} required className="w-full p-3 rounded text-[11px] outline-none" style={inputStyle} /></div>
              <div><label className={labelCls} style={labelStyle}>Nº Contrato <span className="normal-case font-normal" title="Precisa ser único por venda: a DIMOB rejeita duas vendas do mesmo CPF com o mesmo contrato">(vazio = nº da venda)</span></label><input value={vendaForm.num_contrato} onChange={(e) => setVendaForm({ ...vendaForm, num_contrato: e.target.value })} placeholder="automático" className="w-full p-3 rounded text-[11px] outline-none font-mono" style={inputStyle} /></div>
              <div>
                <label className={labelCls} style={labelStyle}>Imóvel Permutado?</label>
                <select value={vendaForm.permuta} onChange={(e) => setVendaForm({ ...vendaForm, permuta: e.target.value })} className="w-full p-3 rounded text-[11px] outline-none" style={inputStyle}>
                  <option value="N">Não</option>
                  <option value="S">Sim</option>
                </select>
              </div>
              {vendaForm.permuta === 'S' && (
                <div><label className={labelCls} style={labelStyle}>Conta Permuta (Questor)</label><input type="number" value={vendaForm.conta_permuta} onChange={(e) => setVendaForm({ ...vendaForm, conta_permuta: e.target.value })} placeholder="opcional" className="w-full p-3 rounded text-[11px] outline-none" style={inputStyle} /></div>
              )}
            </div>

            {/* COMPRADORES */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={labelCls + ' mb-0'} style={labelStyle}>Compradores {compradores.length > 1 && `(${compradores.length})`}</label>
                <button type="button" onClick={() => setCompradores(cs => redistribuirPercentuais([...cs, { nome: '', cpf_cnpj: '' }]))} className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-bold" style={{ background: 'rgba(255, 160, 80, 0.1)', color: '#ff7a1a' }}>
                  <Plus size={11}/> Adicionar comprador
                </button>
              </div>
              <div className="flex flex-col gap-2">
                {compradores.map((c, idx) => {
                  const cota = totalNum > 0 ? totalNum * (parseFloat(c.percentual) || 0) / 100 : 0;
                  return (
                  <div key={idx} className="grid grid-cols-[24px_1fr_190px_75px_110px_28px] items-center gap-2">
                    <span className="text-[9px] font-mono text-center" style={{ color: idx === 0 ? '#ff7a1a' : '#5a4e42' }} title={idx === 0 ? 'Comprador principal' : 'Comprador vinculado'}>{idx === 0 ? '1º' : `${idx + 1}º`}</span>
                    <input value={c.nome} onChange={(e) => setComprador(idx, { nome: e.target.value })} placeholder="Nome completo" className="p-3 rounded text-[11px] outline-none" style={inputStyle} />
                    <input value={c.cpf_cnpj} onChange={(e) => setComprador(idx, { cpf_cnpj: e.target.value })} onBlur={() => buscarClientePorDoc(idx)} placeholder="CPF/CNPJ" className="p-3 rounded text-[11px] outline-none font-mono" style={inputStyle} />
                    <input type="number" step="0.01" min="0" max="100" value={c.percentual} disabled={compradores.length === 1} onChange={(e) => setComprador(idx, { percentual: e.target.value })} title="% do contrato deste comprador (DIMOB/EFD)" className="p-3 rounded text-[11px] outline-none font-mono text-right disabled:opacity-40" style={inputStyle} />
                    <span className="font-mono text-[10px] text-right" style={{ color: '#8a7a68' }} title="Cota deste CPF no contrato">{compradores.length > 1 ? formatCurrency(cota) : '—'}</span>
                    <button type="button" disabled={compradores.length === 1} onClick={() => setCompradores(cs => redistribuirPercentuais(cs.filter((_, i) => i !== idx)))} className="p-1.5 rounded hover:bg-red-900/30 disabled:opacity-20" style={{ color: '#8a7a68' }}><Trash2 size={13}/></button>
                  </div>
                  );
                })}
              </div>
              {compradores.length > 1 && (
                <p className="mt-1 text-[9.5px]" style={{ color: Math.abs(somaPercentuais - 100) > 0.05 ? '#ff7a1a' : '#5a4e42' }}>
                  O contrato é RATEADO entre os CPFs conforme os percentuais (vale para DIMOB e EFD-Contribuições). Soma atual: {somaPercentuais.toFixed(2)}%{Math.abs(somaPercentuais - 100) > 0.05 ? ' ⚠ precisa fechar 100%' : ' ✓'}. O 1º comprador é o titular; os demais entram como vendas vinculadas com a sua cota.
                </p>
              )}
            </div>

            {/* CONDICOES DE PAGAMENTO */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={labelCls + ' mb-0'} style={labelStyle}>Condições de Pagamento</label>
                <button type="button" onClick={() => setCondicoes(cs => [...cs, { tipo: 'MENSAL', quantidade: 1, valor: '', vencimento: '' }])} className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-bold" style={{ background: 'rgba(255, 160, 80, 0.1)', color: '#ff7a1a' }}>
                  <Plus size={11}/> Adicionar condição
                </button>
              </div>
              {!condicoes.length ? (
                <div className="p-3 rounded text-[10px] uppercase" style={{ ...inputStyle, color: '#5a4e42' }}>Sem condições — a venda será gravada sem parcelas geradas.</div>
              ) : (
                <div className="flex flex-col gap-2">
                  <div className="grid grid-cols-[150px_90px_1fr_150px_28px] gap-2 text-[9px] uppercase font-bold px-1" style={{ color: '#5a4e42' }}>
                    <span>Tipo</span><span>Qtd parcelas</span><span>Valor da parcela</span><span>1º vencimento</span><span></span>
                  </div>
                  {condicoes.map((c, idx) => (
                    <div key={idx} className="grid grid-cols-[150px_90px_1fr_150px_28px] items-center gap-2">
                      <select value={c.tipo} onChange={(e) => setCondicao(idx, { tipo: e.target.value })} className="p-2.5 rounded text-[11px] outline-none" style={inputStyle}>
                        {TIPOS_CONDICAO.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                      <input type="number" min="1" value={c.quantidade} disabled={TIPOS_PARCELA_UNICA.includes(c.tipo)} onChange={(e) => setCondicao(idx, { quantidade: e.target.value })} className="p-2.5 rounded text-[11px] outline-none disabled:opacity-40" style={inputStyle} />
                      <input type="number" step="0.01" value={c.valor} onChange={(e) => setCondicao(idx, { valor: e.target.value })} placeholder="0,00" className="p-2.5 rounded text-[11px] outline-none" style={inputStyle} />
                      <input type="date" value={c.vencimento} onChange={(e) => setCondicao(idx, { vencimento: e.target.value })} className="p-2.5 rounded text-[11px] outline-none dark-calendar" style={inputStyle} />
                      <button type="button" onClick={() => setCondicoes(cs => cs.filter((_, i) => i !== idx))} className="p-1.5 rounded hover:bg-red-900/30" style={{ color: '#8a7a68' }}><Trash2 size={13}/></button>
                    </div>
                  ))}
                  <div className="flex justify-end gap-4 text-[11px] font-mono px-1" style={{ color: divergente ? '#ff7a1a' : '#8a7a68' }}>
                    <span>Σ condições: {formatCurrency(somaCondicoes)}</span>
                    <span>Total: {formatCurrency(totalNum)}</span>
                    {divergente && <span className="font-bold">⚠ divergência {formatCurrency(somaCondicoes - totalNum)}</span>}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t mt-2" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
              <button type="submit" disabled={saving} className="px-8 py-3 rounded text-[11px] font-bold uppercase tracking-widest disabled:opacity-50" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                {saving ? 'Gravando...' : 'Registrar Venda'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export const VendasView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [empreendimentosList, setEmpreendimentosList] = useState([]);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('TODOS');
  const [dataIniFilter, setDataIniFilter] = useState('');
  const [dataFimFilter, setDataFimFilter] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  
  const [selectedVenda, setSelectedVenda] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [distratoModal, setDistratoModal] = useState(null);
  const [condicoesLoading, setCondicoesLoading] = useState(false);
  const [condicoesData, setCondicoesData] = useState(null);
  const [estruturaAberta, setEstruturaAberta] = useState(false);
  const [parcelaManualModal, setParcelaManualModal] = useState(null);
  const [salvandoParcela, setSalvandoParcela] = useState(false);
  const [editVendaModal, setEditVendaModal] = useState(null);
  const [salvandoEdicao, setSalvandoEdicao] = useState(false);
  const [selecao, setSelecao] = useState(new Set());
  const [excluirModal, setExcluirModal] = useState(null);
  const [excluindo, setExcluindo] = useState(false);

  const toggleSelecao = (id) => setSelecao(s => {
    const n = new Set(s);
    n.has(id) ? n.delete(id) : n.add(id);
    return n;
  });

  const prepararExclusao = async (ids) => {
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/excluir`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids, empresa_id: parseInt(selectedEmpresa, 10), dry_run: true })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      setExcluirModal({ ids, preview: data, forcar: false });
    } catch (e) { alert('Falha na prévia de exclusão: ' + e.message); }
  };

  const confirmarExclusao = async () => {
    const m = excluirModal;
    if (!m) return;
    const total = (m.preview.excluiveis?.length || 0) + (m.forcar ? (m.preview.bloqueadas?.length || 0) : 0);
    if (!window.confirm(`EXCLUSÃO DEFINITIVA (sem distrato) de ${total} venda(s) e toda a cascata. Não há desfazer. Continuar?`)) return;
    setExcluindo(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/excluir`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: m.ids, empresa_id: parseInt(selectedEmpresa, 10), dry_run: false, forcar: m.forcar })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      alert(data.message || 'Excluídas.');
      setExcluirModal(null);
      setSelecao(new Set());
      setSelectedVenda(null);
      handleSearch();
    } catch (e) { alert('Falha na exclusão: ' + e.message); }
    finally { setExcluindo(false); }
  };

  const abrirEdicaoVenda = (v) => setEditVendaModal({
    venda: v, data: v.data_iso || '', num_contrato: v.num_contrato || '',
    total: v.total != null ? String(v.total) : '', permuta: v.permuta === 'S' ? 'S' : 'N'
  });

  const salvarEdicaoVenda = async () => {
    const m = editVendaModal;
    if (!m) return;
    if (m.data && m.data < '1990-01-01') { alert('Data inválida.'); return; }
    if (m.total !== '' && !(parseFloat(m.total) > 0)) { alert('Valor total deve ser maior que zero.'); return; }
    setSalvandoEdicao(true);
    try {
      const payload = { permuta: m.permuta };
      if (m.data) payload.data = m.data;
      if (m.num_contrato !== (m.venda.num_contrato || '')) payload.num_contrato = m.num_contrato;
      if (m.total !== '' && parseFloat(m.total) !== m.venda.total) payload.total = parseFloat(m.total);
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${m.venda.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setEditVendaModal(null);
      setSelectedVenda(null);
      handleSearch();
    } catch (e) { alert('Falha ao salvar edição: ' + e.message); }
    finally { setSalvandoEdicao(false); }
  };

  const salvarParcelaManual = async () => {
    const m = parcelaManualModal;
    if (!m) return;
    if (!m.data || m.data < '1990-01-01') { alert('Data inválida.'); return; }
    if (!(parseFloat(m.valor) > 0)) { alert('Informe o valor da parcela.'); return; }
    setSalvandoParcela(true);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${m.venda.id}/parcelas`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: m.data, valor: parseFloat(m.valor), referencia: m.referencia })
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      alert(body.message || 'Parcela lançada.');
      setParcelaManualModal(null);
      // recarrega as condições da venda aberta (sem des-selecionar)
      setCondicoesLoading(true);
      fetch(`${API_BASE}/api/vulcano/vendas/${m.venda.id}/condicoes`)
        .then(r => r.json()).then(j => setCondicoesData(j))
        .catch(() => {})
        .finally(() => setCondicoesLoading(false));
    } catch (e) { alert('Falha ao lançar parcela: ' + e.message); }
    finally { setSalvandoParcela(false); }
  };

  useEffect(() => {
    if (!selectedEmpresa) return;
    fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => setEmpreendimentosList(d))
      .catch(err => console.error(err));
  }, [selectedEmpresa]);

  const handleSearch = () => {
    if (!selectedEmpresa) return;
    if (!empreendimentoFilter || !dataIniFilter || !dataFimFilter) {
      alert("Por favor, selecione um empreendimento e um período de datas antes de buscar.");
      return;
    }
    setLoading(true);
    setHasSearched(true);
    
    let url = `${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`;
    if (empreendimentoFilter) url += `&empreendimento_id=${empreendimentoFilter}`;
    if (dataIniFilter) url += `&data_ini=${dataIniFilter}`;
    if (dataFimFilter) url += `&data_fim=${dataFimFilter}`;

    fetch(url)
      .then(res => res.json())
      .then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  };

  const handleSelectVenda = async (v) => {
    if (selectedVenda?.id === v.id) { setSelectedVenda(null); return; }
    setSelectedVenda(v);
    setCondicoesLoading(true); setCondicoesData(null);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${encodeURIComponent(v.id)}/condicoes`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP`);
      setCondicoesData(json);
    } catch (e) {
      setCondicoesData({ error: 'Falha ao carregar fluxo financeiro.' });
    } finally { setCondicoesLoading(false); }
  };

  const filtered = data.filter(v => {
    let ok = true;
    if (empreendimentoFilter && v.empreendimento_id && v.empreendimento_id.toString() !== empreendimentoFilter.toString()) ok = false;
    if (statusFilter !== 'TODOS') {
        if (statusFilter === 'DISTRATADA' && v.distrato !== 'S') ok = false;
        if (statusFilter === 'ATIVA' && v.distrato === 'S') ok = false;
    }
    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const str = `${v.cliente_nome} ${v.cliente_cnpj} ${v.descricao} ${v.id}`.toLowerCase();
        if (!str.includes(query)) ok = false;
    }
    return ok;
  });

  const groupedVendas = { 'HOJE': [], 'ONTEM': [], 'ESTA SEMANA': [], 'ESTE MÊS': [], 'ANTERIORES': [] };
  const today = new Date(); today.setHours(0,0,0,0);
  
  filtered.forEach(v => {
    if (!v.data || !v.data.includes('/')) { groupedVendas['ANTERIORES'].push(v); return; }
    const [d, m, y] = v.data.split('/');
    const vDate = new Date(y, m - 1, d);
    const diffTime = Math.abs(today - vDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) groupedVendas['HOJE'].push(v);
    else if (diffDays === 1) groupedVendas['ONTEM'].push(v);
    else if (diffDays <= 7) groupedVendas['ESTA SEMANA'].push(v);
    else if (vDate.getMonth() === today.getMonth() && vDate.getFullYear() === today.getFullYear()) groupedVendas['ESTE MÊS'].push(v);
    else groupedVendas['ANTERIORES'].push(v);
  });

  const handleVendaSalva = () => {
    setShowForm(false);
    if (hasSearched) handleSearch();
  };

  const handleExportXLSX = () => {
    if (!filtered.length) return;
    const rows = filtered.map(v => ({
      'ID': v.id,
      'Data': v.data,
      'Empreendimento': v.empreendimento,
      'Unidade': v.descricao,
      'Comprador Principal': v.cliente_nome,
      'CPF/CNPJ': v.cliente_cnpj,
      'Compradores': (v.compradores || []).map(c => c.valor != null ? `${c.nome} (${formatCurrency(c.valor)})` : c.nome).join(' / ') || v.cliente_nome,
      'Total Venda': v.total,
      'Permuta': v.permuta === 'S' ? 'SIM' : 'NÃO',
      'Status': v.distrato === 'S' ? 'DISTRATADA' : 'ATIVA',
      'Data Distrato': v.data_distrato || ''
    }));
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Vendas');
    XLSX.writeFile(wb, `vendas_emp${empreendimentoFilter || selectedEmpresa}_${dataIniFilter}_a_${dataFimFilter}.xlsx`);
  };

  const totalGeral = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);

  return (
    <div className="flex flex-col h-full animate-in fade-in" style={{ background: '#0c0908' }}>
      {/* HEADER PODEROSO */}
      <div className="px-6 py-4 flex flex-col gap-4 shrink-0 z-20" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex justify-between items-end">
            <div className="flex items-baseline gap-3">
                <h2 className="text-[24px] font-black tracking-tighter" style={{ color: '#f0e6d8' }}>VENDAS</h2>
                <span className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>· {filtered.length}</span>
            </div>
            
            <div className="flex gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                    <Search size={12}/>
                    <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Buscar venda..." className="bg-transparent border-none outline-none text-[12px] w-48 placeholder-[#5a4e42]" style={{ color: '#f0e6d8' }} />
                    <kbd className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>/</kbd>
                </div>
                
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-bold" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.18)', color: '#f0e6d8' }}>
                    <Filter size={12}/> Comandos <kbd className="ml-1 text-[10px]" style={{ color: '#8a7a68' }}>⌘K</kbd>
                </button>
                <button onClick={handleExportXLSX} disabled={!filtered.length} title={filtered.length ? 'Exportar a lista filtrada para Excel' : 'Busque vendas primeiro'} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-bold disabled:opacity-40" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.18)', color: '#f0e6d8' }}>
                    <FileSpreadsheet size={12}/> Excel
                </button>
                {filtered.length > 0 && (
                    selecao.size < filtered.length ? (
                        <button onClick={() => setSelecao(new Set(filtered.map(v => v.id)))} title="Marca todas as vendas da lista filtrada" className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-bold" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.18)', color: '#f0e6d8' }}>
                            <CheckSquare size={12}/> Selecionar todas ({filtered.length})
                        </button>
                    ) : (
                        <button onClick={() => setSelecao(new Set())} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-bold" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.18)', color: '#8a7a68' }}>
                            <X size={12}/> Limpar seleção
                        </button>
                    )
                )}
                {selecao.size > 0 && (
                    <button onClick={() => prepararExclusao([...selecao])} title="Utilitário de exclusão de registros (sem distrato) — abre prévia antes de confirmar" className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-bold" style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#ef4444' }}>
                        <Trash2 size={12}/> Excluir {selecao.size} selecionada(s)
                    </button>
                )}
                <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-[12px] font-bold shadow-lg" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                    <Plus size={12}/> Nova venda <kbd className="ml-1 text-[10px] bg-black/20 border border-black/30 px-1 rounded" style={{ color: '#3a1606' }}>⇧⌘N</kbd>
                </button>
            </div>
        </div>
        
        <div className="flex gap-3">
            <select value={empreendimentoFilter} onChange={(e) => setEmpreendimentoFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="">Selecione Empreendimento</option>
                {empreendimentosList.map((emp) => <option key={emp.id} value={emp.id}>{emp.nome}</option>)}
            </select>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <span className="text-[11px] font-mono">De</span>
                <input type="date" value={dataIniFilter} onChange={(e) => setDataIniFilter(e.target.value)} className="bg-transparent border-none outline-none text-[11px] font-mono dark-calendar" style={{ color: '#f0e6d8' }} />
                <span className="text-[11px] font-mono">Até</span>
                <input type="date" value={dataFimFilter} onChange={(e) => setDataFimFilter(e.target.value)} className="bg-transparent border-none outline-none text-[11px] font-mono dark-calendar" style={{ color: '#f0e6d8' }} />
            </div>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="TODOS">Status</option>
                <option value="ATIVA">ATIVA</option>
                <option value="DISTRATADA">DISTRATADA</option>
            </select>
            <button onClick={handleSearch} className="px-4 py-1.5 rounded-lg text-[12px] font-bold transition-colors hover:bg-white/10" style={{ background: 'rgba(255, 160, 80, 0.1)', border: '1px solid rgba(255, 160, 80, 0.2)', color: '#ff7a1a' }}>
                Buscar
            </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* LISTA CENTRAL */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
            {loading ? (
                <div className="flex justify-center items-center h-full text-[#8a7a68] animate-pulse text-[12px]">Carregando carteira de vendas...</div>
            ) : !hasSearched ? (
                <div className="flex justify-center items-center h-full text-[#5a4e42] uppercase text-[10px] tracking-widest font-bold">Selecione empreendimento e período para buscar.</div>
            ) : filtered.length === 0 ? (
                <div className="flex justify-center items-center h-full text-[#5a4e42] uppercase text-[10px] tracking-widest font-bold">Nenhum registro.</div>
            ) : (
                <div className="flex flex-col">
                    {Object.entries(groupedVendas).filter(([_, items]) => items.length > 0).map(([groupName, items]) => (
                        <div key={groupName} className="mb-4">
                            <div className="px-6 py-2 flex items-center gap-3 sticky top-0 z-10" style={{ background: '#0c0908' }}>
                                <span className="font-mono text-[9.5px] font-bold tracking-[0.28em]" style={{ color: '#5a4e42' }}>{groupName}</span>
                                <div className="flex-1 h-[1px]" style={{ background: 'rgba(255, 160, 80, 0.08)' }}></div>
                                <span className="font-mono text-[9.5px]" style={{ color: '#5a4e42' }}>{items.length}</span>
                            </div>
                            <div className="flex flex-col">
                                {items.map(v => {
                                    const isSelected = selectedVenda?.id === v.id;
                                    const isDistratada = v.distrato === 'S';
                                    return (
                                        <div 
                                            key={v.id} 
                                            onClick={() => handleSelectVenda(v)}
                                            className="grid grid-cols-[20px_60px_40px_1fr_200px_120px_100px_80px_30px] items-center gap-3 px-6 py-3 cursor-pointer transition-colors group/row"
                                            style={{
                                                background: isSelected ? 'rgba(255, 122, 26, 0.05)' : 'transparent',
                                                borderBottom: '1px solid rgba(255, 160, 80, 0.08)'
                                            }}
                                        >
                                            <input type="checkbox" checked={selecao.has(v.id)}
                                                onChange={() => toggleSelecao(v.id)}
                                                onClick={(e) => e.stopPropagation()}
                                                title="Selecionar para exclusão"
                                                className="accent-[#ef4444] cursor-pointer" />

                                            <span className="font-mono text-[10.5px]" style={{ color: isSelected ? '#ff7a1a' : '#5a4e42' }}>#{v.id}</span>

                                            <div className="w-[30px] h-[22px] rounded flex items-center justify-center font-mono text-[9.5px] font-bold"
                                                 style={{ background: 'linear-gradient(135deg, rgba(255, 122, 26, 0.25), rgba(201, 58, 18, 0.15))', border: '1px solid rgba(255, 140, 42, 0.25)', color: '#ffd28a' }}>
                                                {(v.empreendimento || 'EMP').substring(0,3).toUpperCase()}
                                            </div>
                                            
                                            <div className="min-w-0">
                                                <div className="font-medium text-[13.5px] truncate flex items-center gap-2" style={{ color: '#f0e6d8' }}>
                                                    {v.cliente_nome}
                                                    {(v.qtd_compradores || 1) > 1 && (
                                                        <span title={(v.compradores || []).map(c => c.valor != null ? `${c.nome} — ${formatCurrency(c.valor)}` : c.nome).join('\n')} className="px-1.5 py-0.5 rounded font-mono text-[9px] font-bold shrink-0" style={{ background: 'rgba(255, 122, 26, 0.15)', border: '1px solid rgba(255, 140, 42, 0.25)', color: '#ffd28a' }}>
                                                            +{v.qtd_compradores - 1}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="font-mono text-[10.5px] mt-1" style={{ color: '#8a7a68' }}>
                                                    {v.descricao} · <span style={{ color: '#5a4e42' }}>{v.cliente_cnpj}</span>
                                                </div>
                                            </div>
                                            
                                            <div className="font-mono text-[11px]" style={{ color: '#8a7a68' }}>{v.empreendimento}</div>
                                            
                                            <div className="font-medium text-[13.5px]" style={{ color: '#f0e6d8' }}>{formatCurrency(v.total)}</div>
                                            
                                            <div className="flex items-center gap-2">
                                                {isDistratada ? (
                                                    <><span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_6px_red]"></span><span className="font-mono text-[9.5px] tracking-[0.16em] text-red-500">DISTRATADA</span></>
                                                ) : (
                                                    <><span className="w-1.5 h-1.5 rounded-full" style={{ background: '#ffc247', boxShadow: '0 0 6px #ffc247' }}></span><span className="font-mono text-[9.5px] tracking-[0.16em]" style={{ color: '#ffc247' }}>ATIVA</span></>
                                                )}
                                            </div>
                                            
                                            <div className="font-mono text-[10px] text-right" style={{ color: '#5a4e42' }}>{v.data}</div>

                                            <button
                                                onClick={(e) => { e.stopPropagation(); abrirEdicaoVenda(v); }}
                                                title="Editar venda"
                                                className="p-1 rounded opacity-40 group-hover/row:opacity-100 hover:bg-white/10 transition-all"
                                                style={{ color: '#ffc247' }}>
                                                <Pencil size={13}/>
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>

        {/* RIGHT PANEL (DETALHES DA VENDA) */}
        {selectedVenda && (
            <div className="w-[450px] flex flex-col shrink-0 animate-in slide-in-from-right-8 duration-300 z-10" style={{ background: '#0c0908', borderLeft: '1px solid rgba(255, 160, 80, 0.08)' }}>
                <div className="p-5 flex justify-between items-start" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-[10px] font-bold" style={{ color: '#ff7a1a' }}>#{selectedVenda.id}</span>
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-mono tracking-widest" style={{ background: 'rgba(255, 194, 71, 0.1)', color: '#ffc247' }}>ATIVA</span>
                        </div>
                        <h3 className="text-[16px] font-bold" style={{ color: '#f0e6d8' }}>{selectedVenda.cliente_nome}</h3>
                        <p className="font-mono text-[11px] mt-1" style={{ color: '#8a7a68' }}>{selectedVenda.cliente_cnpj}</p>
                    </div>
                    <button onClick={() => setSelectedVenda(null)} className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/5 transition-colors" style={{ color: '#8a7a68' }}><X size={14}/></button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {/* INFO GRID */}
                    <div className="px-5 py-4" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <div className="flex justify-between py-1.5 border-b border-dashed" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <span className="font-mono text-[10px] tracking-[0.18em]" style={{ color: '#5a4e42' }}>UNIDADE</span>
                            <span className="text-[12.5px]" style={{ color: '#f0e6d8' }}>{selectedVenda.descricao}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-dashed" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <span className="font-mono text-[10px] tracking-[0.18em]" style={{ color: '#5a4e42' }}>OBRA</span>
                            <span className="text-[12.5px]" style={{ color: '#f0e6d8' }}>{selectedVenda.empreendimento}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-dashed" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <span className="font-mono text-[10px] tracking-[0.18em]" style={{ color: '#5a4e42' }}>ASSINADO</span>
                            <span className="text-[12.5px]" style={{ color: '#f0e6d8' }}>{selectedVenda.data}</span>
                        </div>
                    </div>

                    {/* KPIs — dados REAIS das condições/parcelas (nada estimado) */}
                    {(() => {
                        const parcelas = condicoesData?.parcelas || [];
                        const formas = condicoesData?.formas_pagto || condicoesData?.formas || [];
                        const entradaForma = formas.find(f => /SINAL|ATO|ENTRADA/i.test(f.descricao || ''));
                        const recebido = parcelas.reduce((s, p) => s + (p.total_pago || 0), 0);
                        return (
                    <div className="p-5" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>VALOR DA VENDA</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{formatCurrency(selectedVenda.total)}</div>
                            </div>
                            <div>
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>PARCELAS</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{condicoesLoading ? '...' : (parcelas.length ? parcelas.length + 'x' : '—')}</div>
                            </div>
                            <div className="mt-2">
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>ENTRADA (SINAL/ATO)</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{condicoesLoading ? '...' : (entradaForma ? formatCurrency(entradaForma.valor) : '—')}</div>
                            </div>
                            <div className="mt-2">
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>RECEBIDO</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#22c55e' }}>{condicoesLoading ? '...' : formatCurrency(recebido)}</div>
                            </div>
                        </div>
                        {!condicoesLoading && !formas.length && !parcelas.length && (
                            <p className="mt-3 text-[9.5px] uppercase tracking-widest" style={{ color: '#8a7a68' }}>Venda sem condições de pagamento cadastradas — use "Lançar parcela manual" ou recadastre com condições.</p>
                        )}
                    </div>
                        );
                    })()}

                    {/* Cronograma — próximas parcelas reais */}
                    <div className="p-5" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <div className="font-mono text-[9.5px] tracking-[0.22em] mb-3" style={{ color: '#5a4e42' }}>CRONOGRAMA · PRÓXIMAS 12</div>
                        <div className="h-12 flex items-end justify-center">
                            {condicoesLoading ? (
                                <Loader2 className="animate-spin" size={16} style={{ color: '#5a4e42' }}/>
                            ) : (condicoesData?.parcelas || []).length ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={(condicoesData.parcelas.filter(p => !p.total_pago).slice(0, 12)).map(p => ({ name: (p.data || '').substring(5, 7), val: p.valor_parcela }))}>
                                        <RechartsTooltip cursor={{fill: 'rgba(255, 160, 80, 0.08)'}} contentStyle={{backgroundColor: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', fontSize: '10px'}} />
                                        <Bar dataKey="val" fill="url(#colorUv)" radius={[1, 1, 0, 0]} />
                                        <defs>
                                            <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#ff9a4a" stopOpacity={1}/>
                                                <stop offset="100%" stopColor="#c93a12" stopOpacity={1}/>
                                            </linearGradient>
                                        </defs>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <span className="text-[9px] uppercase" style={{ color: '#5a4e42' }}>Sem parcelas em aberto</span>
                            )}
                        </div>
                    </div>

                    {/* Estrutura financeira (parcelas reais) */}
                    {estruturaAberta && (
                        <div className="p-5" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                            <div className="font-mono text-[9.5px] tracking-[0.22em] mb-3" style={{ color: '#5a4e42' }}>ESTRUTURA FINANCEIRA · {(condicoesData?.parcelas || []).length} PARCELAS</div>
                            <div className="max-h-56 overflow-y-auto custom-scrollbar">
                                <table className="w-full text-[10.5px]">
                                    <tbody>
                                        {(condicoesData?.parcelas || []).map(p => (
                                            <tr key={p.id} className="border-b" style={{ borderColor: 'rgba(255, 160, 80, 0.06)' }}>
                                                <td className="py-1 pr-2 font-mono" style={{ color: '#8a7a68' }}>{p.parcela || '—'}</td>
                                                <td className="py-1 pr-2 font-mono" style={{ color: '#8a7a68' }}>{p.data}</td>
                                                <td className="py-1 pr-2 font-mono text-right" style={{ color: '#f0e6d8' }}>{formatCurrency(p.valor_parcela)}</td>
                                                <td className="py-1 font-mono text-right" style={{ color: p.total_pago > 0 ? '#22c55e' : '#5a4e42' }}>{p.total_pago > 0 ? formatCurrency(p.total_pago) : 'aberta'}</td>
                                            </tr>
                                        ))}
                                        {!(condicoesData?.parcelas || []).length && (
                                            <tr><td className="py-2 text-[10px] uppercase" style={{ color: '#5a4e42' }}>Sem parcelas — lance manualmente abaixo.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="p-5">
                        <div className="font-mono text-[9.5px] tracking-[0.22em] mb-3" style={{ color: '#5a4e42' }}>AÇÕES</div>
                        <div className="flex flex-col gap-1.5">
                            <button onClick={() => setEstruturaAberta(v => !v)} className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><Layers size={14} style={{ color: '#8a7a68' }}/> {estruturaAberta ? 'Ocultar' : 'Abrir'} estrutura financeira</span>
                            </button>
                            <button onClick={() => setParcelaManualModal({ venda: selectedVenda, data: hojeLocal(), valor: '', referencia: '' })} className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><DollarSign size={14} style={{ color: '#8a7a68' }}/> Lançar parcela manual</span>
                            </button>
                            <button onClick={() => abrirEdicaoVenda(selectedVenda)} className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><Pencil size={14} style={{ color: '#8a7a68' }}/> Editar venda</span>
                            </button>
                            <button onClick={() => prepararExclusao([selectedVenda.id])} title="Exclusão definitiva do registro (com prévia) — para registro errado/teste; distrato é outra ação" className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-red-950/30" style={{ color: '#ef4444' }}>
                                <span className="flex items-center gap-3"><Trash2 size={14} className="text-red-500/70"/> Excluir registro (sem distrato)</span>
                            </button>
                            {selectedVenda.distrato !== 'S' && (
                                <button onClick={() => setDistratoModal(selectedVenda)} className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium mt-2 transition-colors hover:bg-red-950/30" style={{ color: '#ef4444' }}>
                                    <span className="flex items-center gap-3"><AlertCircle size={14} className="text-red-500/70"/> Distratar contrato</span>
                                    <span className="font-mono text-[10px] bg-red-950/50 px-1.5 rounded text-red-900 border border-red-900/30">⇧⌘D</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        )}
      </div>

      <div className="px-6 py-2 flex justify-between items-center shrink-0 z-20" style={{ background: '#0c0908', borderTop: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex gap-4 font-mono text-[9px] font-bold tracking-[0.16em]" style={{ color: '#5a4e42' }}>
            <span>↑ ↓ NAVEGAR</span>
            <span>↵ AÇÃO</span>
            <span>/ BUSCAR</span>
            <span>⌘K COMANDOS</span>
            <span>⇧⌘N NOVA VENDA</span>
        </div>
        <div className="font-mono text-[9.5px] font-bold tracking-[0.2em]" style={{ color: '#8a7a68' }}>
            EXIBINDO {filtered.length} · TOTAL {formatCurrency(totalGeral)}
        </div>
      </div>
      
      {/* MODAL NOVA VENDA */}
      {showForm && (
        <NovaVendaModal
          selectedEmpresa={selectedEmpresa}
          empreendimentosList={empreendimentosList}
          onClose={() => setShowForm(false)}
          onSaved={handleVendaSalva}
        />
      )}

      {/* MODAL PARCELA MANUAL */}
      {parcelaManualModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[110] animate-in fade-in p-6">
            <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6" style={{ background: '#0c0908', border: '1px solid rgba(255, 160, 80, 0.18)' }}>
                <h3 className="text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-1" style={{ color: '#f0e6d8' }}>
                    <DollarSign size={20} color="#ff7a1a"/> Lançar Parcela Manual
                </h3>
                <p className="text-[11px] mb-5" style={{ color: '#8a7a68' }}>Venda <b style={{ color: '#f0e6d8' }}>#{parcelaManualModal.venda.id}</b> — {parcelaManualModal.venda.cliente_nome}. A parcela entra como prevista (em aberto) e pode ser baixada normalmente.</p>
                <div className="grid grid-cols-3 gap-3 mb-6">
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Vencimento</label>
                        <input type="date" min="1990-01-01" value={parcelaManualModal.data} onChange={(e) => setParcelaManualModal({ ...parcelaManualModal, data: e.target.value })} className="w-full p-2.5 rounded text-[11px] outline-none dark-calendar" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Valor</label>
                        <input type="number" step="0.01" value={parcelaManualModal.valor} onChange={(e) => setParcelaManualModal({ ...parcelaManualModal, valor: e.target.value })} placeholder="0,00" className="w-full p-2.5 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Referência</label>
                        <input value={parcelaManualModal.referencia} onChange={(e) => setParcelaManualModal({ ...parcelaManualModal, referencia: e.target.value })} placeholder="ex.: 95/240" className="w-full p-2.5 rounded text-[11px] outline-none font-mono" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                </div>
                <div className="flex justify-end gap-3">
                    <button onClick={() => setParcelaManualModal(null)} className="px-4 py-2 hover:bg-white/5 transition-colors text-[11px] font-bold uppercase tracking-widest rounded" style={{ color: '#8a7a68' }}>Cancelar</button>
                    <button onClick={salvarParcelaManual} disabled={salvandoParcela} className="px-6 py-2 rounded text-[11px] font-bold uppercase tracking-widest disabled:opacity-50" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                        {salvandoParcela ? 'Gravando...' : 'Lançar Parcela'}
                    </button>
                </div>
            </div>
        </div>
      )}

      {/* MODAL EXCLUIR REGISTROS (SEM DISTRATO) */}
      {excluirModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[120] animate-in fade-in p-6">
            <div className="w-full max-w-lg rounded-xl shadow-2xl flex flex-col p-6" style={{ background: '#0c0908', border: '1px solid rgba(239, 68, 68, 0.35)' }}>
                <h3 className="text-red-500 text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-1">
                    <Trash2 size={20}/> Excluir registros — sem distrato
                </h3>
                <p className="text-[11px] mb-4" style={{ color: '#8a7a68' }}>
                    Exclusão <b className="text-red-500">DEFINITIVA</b> do banco (para registros errados ou de teste). Diferente do distrato, não deixa histórico e <b>não há desfazer</b>.
                </p>
                <div className="rounded p-3 mb-3 text-[11px] space-y-1" style={{ background: 'rgba(239, 68, 68, 0.06)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#f0e6d8' }}>
                    <p className="font-black uppercase text-[10px]" style={{ color: '#8a7a68' }}>O que será removido</p>
                    <p>• <b>{excluirModal.preview.cascata?.vendas ?? 0}</b> venda(s) {excluirModal.preview.cascata?.vinculadas > 0 && <> + <b>{excluirModal.preview.cascata.vinculadas}</b> vinculada(s) de multi-comprador</>}</p>
                    <p>• {excluirModal.preview.cascata?.parcelas_receber ?? 0} parcela(s) do contas a receber · {excluirModal.preview.cascata?.parcelas_cronograma ?? 0} do cronograma · {excluirModal.preview.cascata?.formas_pagto ?? 0} forma(s) de pagto</p>
                    <p>• {excluirModal.preview.cascata?.unidades_vendidas ?? 0} vínculo(s) de unidade (a unidade volta a ficar disponível) · {excluirModal.preview.cascata?.reparcelamentos ?? 0} reparcelamento(s) · {excluirModal.preview.cascata?.baixas_locais ?? 0} baixa(s) local(is)</p>
                </div>
                {(excluirModal.preview.bloqueadas || []).length > 0 && (
                    <div className="rounded p-3 mb-3 text-[10.5px] space-y-1" style={{ background: 'rgba(255, 149, 0, 0.08)', border: '1px solid rgba(255, 149, 0, 0.3)', color: '#f0e6d8' }}>
                        <p className="font-black uppercase text-[#ff9500]">{excluirModal.preview.bloqueadas.length} venda(s) com pagamento — fora da exclusão por padrão:</p>
                        {excluirModal.preview.bloqueadas.slice(0, 8).map(b => (
                            <p key={b.id}>• #{b.id} {b.cliente} — {b.motivo}</p>
                        ))}
                        {excluirModal.preview.bloqueadas.length > 8 && <p>… e mais {excluirModal.preview.bloqueadas.length - 8}</p>}
                        <label className="flex items-center gap-2 mt-2 cursor-pointer" style={{ color: '#ff9500' }}>
                            <input type="checkbox" checked={excluirModal.forcar} onChange={(e) => setExcluirModal({ ...excluirModal, forcar: e.target.checked })} className="accent-[#ff9500]" />
                            Incluir também as vendas com pagamento (as baixas locais serão removidas)
                        </label>
                    </div>
                )}
                <div className="flex justify-end gap-3">
                    <button onClick={() => setExcluirModal(null)} className="px-4 py-2 hover:bg-white/5 transition-colors text-[11px] font-bold uppercase tracking-widest rounded" style={{ color: '#8a7a68' }}>Cancelar</button>
                    <button onClick={confirmarExclusao} disabled={excluindo || (!excluirModal.preview.excluiveis?.length && !excluirModal.forcar)}
                        className="px-6 py-2 rounded text-[11px] font-bold uppercase tracking-widest disabled:opacity-50 bg-red-600/80 hover:bg-red-600 text-white">
                        {excluindo ? 'Excluindo…' : `Excluir definitivamente`}
                    </button>
                </div>
            </div>
        </div>
      )}

      {/* MODAL EDITAR VENDA */}
      {editVendaModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[110] animate-in fade-in p-6">
            <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6" style={{ background: '#0c0908', border: '1px solid rgba(255, 160, 80, 0.18)' }}>
                <h3 className="text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-1" style={{ color: '#f0e6d8' }}>
                    <Pencil size={18} color="#ff7a1a"/> Editar Venda
                </h3>
                <p className="text-[11px] mb-5" style={{ color: '#8a7a68' }}>
                    Venda <b style={{ color: '#f0e6d8' }}>#{editVendaModal.venda.id}</b> — {editVendaModal.venda.cliente_nome}.
                    {(editVendaModal.venda.qtd_compradores || 1) > 1 && (
                        <> Contrato com <b style={{ color: '#ffd28a' }}>{editVendaModal.venda.qtd_compradores} compradores</b>: alterar o valor total redistribui as cotas na mesma proporção.</>
                    )}
                </p>
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Data da venda</label>
                        <input type="date" min="1990-01-01" value={editVendaModal.data} onChange={(e) => setEditVendaModal({ ...editVendaModal, data: e.target.value })} className="w-full p-2.5 rounded text-[11px] outline-none dark-calendar" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Valor total do contrato</label>
                        <input type="number" step="0.01" value={editVendaModal.total} onChange={(e) => setEditVendaModal({ ...editVendaModal, total: e.target.value })} placeholder="0,00" className="w-full p-2.5 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Nº contrato</label>
                        <input value={editVendaModal.num_contrato} onChange={(e) => setEditVendaModal({ ...editVendaModal, num_contrato: e.target.value })} placeholder="default: id da venda" className="w-full p-2.5 rounded text-[11px] outline-none font-mono" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Permuta</label>
                        <select value={editVendaModal.permuta} onChange={(e) => setEditVendaModal({ ...editVendaModal, permuta: e.target.value })} className="w-full p-2.5 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }}>
                            <option value="N">Não</option>
                            <option value="S">Sim</option>
                        </select>
                    </div>
                </div>
                <div className="flex justify-end gap-3">
                    <button onClick={() => setEditVendaModal(null)} className="px-4 py-2 hover:bg-white/5 transition-colors text-[11px] font-bold uppercase tracking-widest rounded" style={{ color: '#8a7a68' }}>Cancelar</button>
                    <button onClick={salvarEdicaoVenda} disabled={salvandoEdicao} className="px-6 py-2 rounded text-[11px] font-bold uppercase tracking-widest disabled:opacity-50" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                        {salvandoEdicao ? 'Gravando...' : 'Salvar'}
                    </button>
                </div>
            </div>
        </div>
      )}

      {/* MODAL DISTRATO */}
      {distratoModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] animate-in fade-in p-6">
            <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6" style={{ background: '#0c0908', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                <h3 className="text-red-500 text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-4">
                    <AlertCircle size={24}/> Confirmar Distrato
                </h3>
                <p className="text-[12px] mb-4" style={{ color: '#8a7a68' }}>
                    Você está prestes a distratar o contrato <strong style={{ color: '#f0e6d8' }}>#{distratoModal.id}</strong> ({distratoModal.cliente_nome}).
                    Esta ação <span className="text-red-500 font-bold">cancelará as parcelas futuras</span> vinculadas a esta venda.
                </p>
                <div className="grid grid-cols-2 gap-3 mb-6">
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Data do distrato</label>
                        <input type="date" value={distratoModal.data_distrato_form || hojeLocal()}
                            onChange={(e) => setDistratoModal({ ...distratoModal, data_distrato_form: e.target.value })}
                            className="w-full p-2.5 rounded text-[11px] outline-none dark-calendar" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Valor devolvido</label>
                        <input type="number" step="0.01" value={distratoModal.valor_devolvido_form ?? ''} placeholder="0,00"
                            onChange={(e) => setDistratoModal({ ...distratoModal, valor_devolvido_form: e.target.value })}
                            className="w-full p-2.5 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                </div>
                <div className="flex justify-end gap-3">
                    <button onClick={() => setDistratoModal(null)} className="px-4 py-2 hover:bg-white/5 transition-colors text-[11px] font-bold uppercase tracking-widest rounded" style={{ color: '#8a7a68' }}>
                        Cancelar
                    </button>
                    <button
                        onClick={() => {
                            fetch(`${API_BASE}/api/distratos`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    id_venda: distratoModal.id,
                                    data_distrato: distratoModal.data_distrato_form || hojeLocal(),
                                    valor_devolvido: parseFloat(distratoModal.valor_devolvido_form || 0),
                                    data_pagamento: null
                                })
                            })
                                .then(async res => {
                                    const body = await res.json().catch(() => ({}));
                                    if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
                                    setDistratoModal(null);
                                    setSelectedVenda(null);
                                    if (hasSearched) handleSearch();
                                })
                                .catch(err => alert("Erro ao distratar: " + err.message));
                        }}
                        className="px-6 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-900/50 text-red-500 rounded text-[11px] font-bold uppercase tracking-widest transition-colors shadow-[0_0_15px_rgba(239,68,68,0.15)]"
                    >
                        Confirmar Distrato
                    </button>
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
  const [searchQuery, setSearchQuery] = useState('');
  const [empreendimentosList, setEmpreendimentosList] = useState([]);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('ABERTA');
  const [dataIniFilter, setDataIniFilter] = useState('');
  const [dataFimFilter, setDataFimFilter] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  
  const [selectedRecebimento, setSelectedRecebimento] = useState(null);

  const [baixaForm, setBaixaForm] = useState({ valor_pago: '', data_pagamento: '', acrescimos: '', descontos: '' });
  const [editParcelaModal, setEditParcelaModal] = useState(null);
  const [salvandoParcelaEdit, setSalvandoParcelaEdit] = useState(false);

  const abrirEdicaoParcela = (r) => setEditParcelaModal({
    row: r, data: r.vencimento_iso || '', valor: r.parcela != null ? String(r.parcela) : '',
    rotulo: r.num_parcela || '', obs: r.obs || ''
  });

  const salvarEdicaoParcela = async () => {
    const m = editParcelaModal;
    if (!m) return;
    if (m.data && m.data < '1990-01-01') { alert('Data inválida.'); return; }
    if (m.valor !== '' && !(parseFloat(m.valor) > 0)) { alert('Valor deve ser maior que zero.'); return; }
    setSalvandoParcelaEdit(true);
    try {
      const idStr = String(m.row.id);
      const isPrazo = idStr.startsWith('prazo_');
      const url = isPrazo
        ? `${API_BASE}/api/vulcano/cronograma/prazo/${idStr.replace('prazo_', '')}`
        : `${API_BASE}/api/vulcano/receber/${idStr}`;
      const payload = isPrazo
        ? { data: m.data || undefined, valor: m.valor !== '' ? parseFloat(m.valor) : undefined, referencia: m.rotulo }
        : { data: m.data || undefined, valor_parcela: m.valor !== '' ? parseFloat(m.valor) : undefined, parcela: m.rotulo, obs: m.obs };
      const res = await fetch(url, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setEditParcelaModal(null);
      handleSearch();
    } catch (e) { alert('Falha ao salvar edição: ' + e.message); }
    finally { setSalvandoParcelaEdit(false); }
  };

  useEffect(() => {
    if (!selectedEmpresa) return;
    fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => setEmpreendimentosList(d))
      .catch(err => console.error(err));
  }, [selectedEmpresa]);

  const handleSearch = (dIni = dataIniFilter, dFim = dataFimFilter) => {
    if (!selectedEmpresa) return;
    if (!empreendimentoFilter || !dIni || !dFim) {
      alert("Por favor, selecione um empreendimento e um período de datas antes de buscar.");
      return;
    }
    setLoading(true);
    setHasSearched(true);

    let url = `${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`;
    if (empreendimentoFilter) url += `&empreendimento_id=${empreendimentoFilter}`;
    if (dIni) url += `&data_ini=${dIni}`;
    if (dFim) url += `&data_fim=${dFim}`;

    fetch(url)
      .then(res => res.json())
      .then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  };

  // Navegacao por competencia: as setas preenchem o mes inteiro em De/Ate e,
  // com empreendimento selecionado, ja rebuscam — a baixa age no periodo em tela.
  const navegarCompetencia = (delta, irParaAtual = false) => {
    const base = (!irParaAtual && dataIniFilter)
      ? new Date(`${dataIniFilter.slice(0, 7)}-01T00:00:00`)
      : new Date();
    const alvo = new Date(base.getFullYear(), base.getMonth() + delta, 1);
    const pad = (n) => String(n).padStart(2, '0');
    const ini = `${alvo.getFullYear()}-${pad(alvo.getMonth() + 1)}-01`;
    const fim = `${alvo.getFullYear()}-${pad(alvo.getMonth() + 1)}-${pad(new Date(alvo.getFullYear(), alvo.getMonth() + 1, 0).getDate())}`;
    setDataIniFilter(ini);
    setDataFimFilter(fim);
    if (empreendimentoFilter) handleSearch(ini, fim);
  };
  const competenciaLabel = dataIniFilter ? `${dataIniFilter.slice(5, 7)}/${dataIniFilter.slice(0, 4)}` : 'mês';

  const uniqueEmps = [...new Set(data.map(r => r.empreendimento))].sort();

  const handleSelectRecebimento = (r) => {
    if (selectedRecebimento?.id === r.id) { setSelectedRecebimento(null); return; }
    setSelectedRecebimento(r);
    setBaixaForm({
      valor_pago: r.parcela || 0,
      data_pagamento: baixaForm.data_pagamento || new Date().toISOString().split('T')[0],
      acrescimos: 0,
      descontos: 0
    });
  };

  const filtered = data.filter(r => {
    let ok = true;
    
    const isAberto = (!r.total || r.total <= 0) && !!r.num_parcela && r.num_parcela.toUpperCase() !== 'ATO';
    if (statusFilter === 'ABERTA' && !isAberto && !r._justPaid) ok = false;
    if (statusFilter === 'BAIXADA' && isAberto) ok = false;

    // no periodo se o VENCIMENTO cai nele OU se foi PAGA nele (parcela vencida
    // em abril e baixada em junho aparece ao pesquisar junho)
    const pagto = (r.data_pagamento || '').slice(0, 10);
    const pagoNoPeriodo = pagto && (!dataIniFilter || pagto >= dataIniFilter) && (!dataFimFilter || pagto <= dataFimFilter);
    if (!pagoNoPeriodo) {
        if (dataIniFilter && r.vencimento_iso && r.vencimento_iso < dataIniFilter) ok = false;
        if (dataFimFilter && r.vencimento_iso && r.vencimento_iso > dataFimFilter) ok = false;
    }

    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const str = `${r.cliente} ${r.descricao_venda} ${r.id} ${r.cliente_cnpj}`.toLowerCase();
        if (!str.includes(query)) ok = false;
    }
    return ok;
  });

  const grouped = { 'VENCIDAS': [], 'VENCE HOJE': [], 'VENCE ESTA SEMANA': [], 'VENCE ESTE MÊS': [], 'PRÓXIMOS MESES': [], 'BAIXADAS': [] };
  const today = new Date(); today.setHours(0,0,0,0);
  
  filtered.forEach(r => {
    const isAberto = (!r.total || r.total <= 0) && !!r.num_parcela && r.num_parcela.toUpperCase() !== 'ATO';
    if (!isAberto && !r._justPaid) { grouped['BAIXADAS'].push(r); return; }

    if (!r.vencimento_iso) { grouped['PRÓXIMOS MESES'].push(r); return; }
    
    const vDate = new Date(`${r.vencimento_iso}T00:00:00`);
    const diffTime = vDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) grouped['VENCIDAS'].push(r);
    else if (diffDays === 0) grouped['VENCE HOJE'].push(r);
    else if (diffDays <= 7) grouped['VENCE ESTA SEMANA'].push(r);
    else if (vDate.getMonth() === today.getMonth() && vDate.getFullYear() === today.getFullYear()) grouped['VENCE ESTE MÊS'].push(r);
    else grouped['PRÓXIMOS MESES'].push(r);
  });

  const flatGrouped = [
      ...grouped['VENCIDAS'], ...grouped['VENCE HOJE'], ...grouped['VENCE ESTA SEMANA'], ...grouped['VENCE ESTE MÊS'], ...grouped['PRÓXIMOS MESES'], ...grouped['BAIXADAS']
  ];

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' && e.target.type === 'text') return;

      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (!flatGrouped.length) return;
        
        let nextIdx = 0;
        if (selectedRecebimento) {
          const currentIdx = flatGrouped.findIndex(x => x.id === selectedRecebimento.id);
          if (currentIdx !== -1) {
            nextIdx = e.key === 'ArrowDown' ? currentIdx + 1 : currentIdx - 1;
          }
        }
        
        if (nextIdx >= 0 && nextIdx < flatGrouped.length) {
          e.preventDefault(); 
          const nextR = flatGrouped[nextIdx];
          setSelectedRecebimento(nextR);
          setBaixaForm(prev => ({
            valor_pago: nextR.parcela || 0,
            data_pagamento: prev.data_pagamento || new Date().toISOString().split('T')[0],
            acrescimos: 0,
            descontos: 0
          }));
          
          setTimeout(() => {
            const rowEl = document.getElementById(`row-${nextR.id}`);
            if (rowEl) {
                rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                const inputEl = document.getElementById(`input-valor-${nextR.id}`);
                if (inputEl) {
                    inputEl.focus();
                    inputEl.select();
                }
            }
          }, 50);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedRecebimento, flatGrouped]);

  const submitBaixa = async (e, r_id) => {
    e.preventDefault();
    
    // OPTIMISTIC UI
    const newData = [...data];
    const dataIdx = newData.findIndex(x => x.id === r_id);
    if (dataIdx !== -1) {
        newData[dataIdx] = {
            ...newData[dataIdx],
            total: parseFloat(baixaForm.valor_pago) || 0,
            data_pagamento: baixaForm.data_pagamento,
            variacao: (parseFloat(baixaForm.acrescimos) || 0) - (parseFloat(baixaForm.descontos) || 0),
            _justPaid: true // Keep it in the same visual group temporarily
        };
        setData(newData);
    }

    // Auto-advance
    const r_idx = flatGrouped.findIndex(x => x.id === r_id);
    let nextIdx = r_idx + 1;
    let nextR = null;
    
    while(nextIdx < flatGrouped.length) {
       const nx = flatGrouped[nextIdx];
       const nxAberto = (!nx.total || nx.total <= 0) && !!nx.num_parcela && nx.num_parcela.toUpperCase() !== 'ATO' && !nx._justPaid;
       if (nxAberto) {
           nextR = nx;
           break;
       }
       nextIdx++;
    }

    if (nextR) {
        setSelectedRecebimento(nextR);
        setBaixaForm(prev => ({
            valor_pago: nextR.parcela || 0,
            data_pagamento: prev.data_pagamento, 
            acrescimos: 0,
            descontos: 0
        }));
        // Use a slightly longer timeout to ensure React finished rendering
        setTimeout(() => {
            const rowEl = document.getElementById(`row-${nextR.id}`);
            if (rowEl) {
                rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                const inputEl = document.getElementById(`input-valor-${nextR.id}`);
                if (inputEl) {
                    inputEl.focus();
                    inputEl.select();
                }
            }
        }, 150);
    } else {
        setSelectedRecebimento(null);
    }

    try {
      await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          id_receber: r_id.toString(),
          empresa_id: parseInt(selectedEmpresa, 10),
          valor_pago: parseFloat(baixaForm.valor_pago) || 0,
          data_pagamento: baixaForm.data_pagamento,
          acrescimos: parseFloat(baixaForm.acrescimos) || 0,
          descontos: parseFloat(baixaForm.descontos) || 0
        })
      });
    } catch (err) {
      console.error("Erro ao dar baixa", err);
      fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
        .then(res => res.json())
        .then(d => setData(Array.isArray(d) ? d : []));
    }
  };

  const totalGeral = filtered.reduce((acc, curr) => acc + (curr.parcela || 0), 0);

  return (
    <div className="flex flex-col h-full animate-in fade-in" style={{ background: '#0c0908' }}>
      <div className="px-6 py-4 flex flex-col gap-4 shrink-0 z-20" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex justify-between items-end">
            <div className="flex items-baseline gap-3">
                <h2 className="text-[24px] font-black tracking-tighter uppercase" style={{ color: '#f0e6d8' }}>Recebimentos</h2>
                <span className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>· {filtered.length} parcelas</span>
            </div>
            
            <div className="flex gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                    <Search size={12}/>
                    <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Buscar parcela..." className="bg-transparent border-none outline-none text-[12px] w-48 placeholder-[#5a4e42]" style={{ color: '#f0e6d8' }} />
                    <kbd className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>/</kbd>
                </div>
                
                <button onClick={() => {
                  const csvContent = "data:text/csv;charset=utf-8," + "Data,Total_Pago,Parcela,Variacao,Num_Parcela,Venda,Cliente\n" + filtered.map(e => `${e.data},${e.total},${e.parcela},${e.variacao},${e.num_parcela || 'ATO'},"${e.descricao_venda}","${e.cliente}"`).join("\n");
                  const encodedUri = encodeURI(csvContent);
                  const link = document.createElement("a");
                  link.setAttribute("href", encodedUri);
                  link.setAttribute("download", "recebimentos.csv");
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }} className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-[12px] font-bold shadow-lg transition-colors hover:bg-[#ff7a1a]/90" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                    <Download size={12}/> Exportar CSV <kbd className="ml-1 text-[10px] bg-black/20 border border-black/30 px-1 rounded" style={{ color: '#3a1606' }}>⇧⌘E</kbd>
                </button>
            </div>
        </div>
        
        <div className="flex flex-wrap gap-3 items-center">
            <select value={empreendimentoFilter} onChange={(e) => setEmpreendimentoFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="">Selecione Empreendimento</option>
                {empreendimentosList.map((emp) => <option key={emp.id} value={emp.id}>{emp.nome}</option>)}
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="TODOS">Todas Parcelas</option>
                <option value="ABERTA">Abertas (Pendentes)</option>
                <option value="BAIXADA">Baixadas (Pagas)</option>
            </select>
            
            <div className="flex items-center gap-1 px-2 py-1 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.18)' }}>
                <button onClick={() => navegarCompetencia(-1)} title="Mês anterior" className="p-1.5 rounded hover:bg-white/10 transition-colors" style={{ color: '#ff7a1a' }}><ChevronLeft size={14}/></button>
                <button onClick={() => navegarCompetencia(0, true)} title="Ir para o mês atual" className="min-w-[64px] text-center font-mono text-[12px] font-bold px-1 hover:text-[#ff7a1a] transition-colors" style={{ color: '#f0e6d8' }}>{competenciaLabel}</button>
                <button onClick={() => navegarCompetencia(1)} title="Próximo mês" className="p-1.5 rounded hover:bg-white/10 transition-colors" style={{ color: '#ff7a1a' }}><ChevronRight size={14}/></button>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <span className="text-[11px] font-mono">De</span>
                <input type="date" value={dataIniFilter} onChange={(e) => setDataIniFilter(e.target.value)} className="bg-transparent border-none outline-none text-[11px] font-mono dark-calendar" style={{ color: '#f0e6d8' }} />
                <span className="text-[11px] font-mono">Até</span>
                <input type="date" value={dataFimFilter} onChange={(e) => setDataFimFilter(e.target.value)} className="bg-transparent border-none outline-none text-[11px] font-mono dark-calendar" style={{ color: '#f0e6d8' }} />
                {(dataIniFilter || dataFimFilter) && (
                  <button onClick={() => {setDataIniFilter(''); setDataFimFilter('');}} className="ml-1 hover:text-[#ff7a1a]"><X size={12}/></button>
                )}
            </div>

            <button onClick={() => handleSearch()} className="px-4 py-1.5 rounded-lg text-[12px] font-bold transition-colors hover:bg-white/10" style={{ background: 'rgba(255, 160, 80, 0.1)', border: '1px solid rgba(255, 160, 80, 0.2)', color: '#ff7a1a' }}>
                Buscar
            </button>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg ml-auto" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)' }}>
                <span className="text-[12px]" style={{ color: '#8a7a68' }}>Total Listado:</span>
                <span className="text-[12px] font-mono font-bold" style={{ color: '#f0e6d8' }}>{formatCurrency(totalGeral)}</span>
            </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto custom-scrollbar relative">
            {loading && data.length === 0 ? (
                <div className="flex flex-col justify-center items-center h-full gap-3 text-[#8a7a68] animate-pulse">
                    <Loader2 size={32} className="animate-spin text-[#ff7a1a]" />
                    <span className="text-[12px] uppercase font-bold tracking-widest">Carregando carteira...</span>
                </div>
            ) : !hasSearched ? (
                <div className="flex justify-center items-center h-full text-[#5a4e42] uppercase text-[10px] tracking-widest font-bold">Selecione empreendimento e período para buscar.</div>
            ) : filtered.length === 0 ? (
                <div className="flex justify-center items-center h-full text-[#5a4e42] uppercase text-[10px] tracking-widest font-bold">Nenhum registro encontrado.</div>
            ) : (
                <div className="flex flex-col">
                    {Object.entries(grouped).filter(([_, items]) => items.length > 0).map(([groupName, items]) => (
                        <div key={groupName} className="mb-4">
                            <div className="px-6 py-2 flex items-center gap-3 sticky top-0 z-10" style={{ background: '#0c0908' }}>
                                <span className={`font-mono text-[9.5px] font-bold tracking-[0.28em] ${groupName === 'VENCIDAS' ? 'text-red-500' : groupName === 'VENCE HOJE' ? 'text-orange-500' : 'text-[#5a4e42]'}`}>
                                    {groupName}
                                </span>
                                <div className="flex-1 h-[1px]" style={{ background: 'rgba(255, 160, 80, 0.08)' }}></div>
                                <span className="font-mono text-[9.5px]" style={{ color: '#5a4e42' }}>{items.length}</span>
                            </div>
                            <div className="flex flex-col">
                                {items.map(r => {
                                    const isSelected = selectedRecebimento?.id === r.id;
                                    const isAberto = (!r.total || r.total <= 0) && !!r.num_parcela && r.num_parcela.toUpperCase() !== 'ATO';
                                    const isVencida = groupName === 'VENCIDAS';
                                    
                                    return (
                                        <div id={`row-${r.id}`} key={r.id} className="flex flex-col" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                                            <div 
                                                onClick={() => {
                                                    handleSelectRecebimento(r);
                                                    if(isAberto) {
                                                        setTimeout(() => {
                                                            const inp = document.getElementById(`input-valor-${r.id}`);
                                                            if (inp) { inp.focus(); inp.select(); }
                                                        }, 50);
                                                    }
                                                }}
                                                className="grid grid-cols-[80px_40px_1fr_200px_120px_100px_80px_30px] items-center gap-3 px-6 py-3 cursor-pointer transition-colors group/row"
                                                style={{
                                                    background: isSelected ? 'rgba(255, 122, 26, 0.05)' : isVencida ? 'rgba(239, 68, 68, 0.02)' : 'transparent',
                                                    borderLeft: isSelected ? '2px solid #ff7a1a' : isVencida ? '2px solid #ef4444' : '2px solid transparent'
                                                }}
                                            >
                                                <div className="flex flex-col">
                                                    <span className="font-mono text-[10.5px]" style={{ color: isSelected ? '#ff7a1a' : '#5a4e42' }}>#{r.id?.toString().replace('prazo_', 'pr_') || 'N/A'}</span>
                                                    <span className="font-mono text-[9px]" style={{ color: '#8a7a68' }}>{r.num_parcela || 'ATO'}</span>
                                                </div>
                                                
                                                <div className="w-[30px] h-[22px] rounded flex items-center justify-center font-mono text-[9.5px] font-bold" 
                                                     style={{ background: 'linear-gradient(135deg, rgba(255, 122, 26, 0.25), rgba(201, 58, 18, 0.15))', border: '1px solid rgba(255, 140, 42, 0.25)', color: '#ffd28a' }}>
                                                    {(r.empreendimento || 'EMP').substring(0,3).toUpperCase()}
                                                </div>
                                                
                                                <div className="min-w-0">
                                                    <div className="font-medium text-[13.5px] truncate" style={{ color: '#f0e6d8' }}>{r.cliente}</div>
                                                    <div className="font-mono text-[10.5px] mt-1" style={{ color: '#8a7a68' }}>
                                                        {r.descricao_venda} · <span style={{ color: '#5a4e42' }}>{r.cliente_cnpj || 'Sem CPF/CNPJ'}</span>
                                                    </div>
                                                </div>
                                                
                                                <div className="font-mono text-[11px] truncate" style={{ color: '#8a7a68' }}>{r.empreendimento}</div>
                                                
                                                <div className={`font-medium text-[13.5px] font-mono ${isVencida ? 'text-red-400' : 'text-[#f0e6d8]'}`}>{formatCurrency(r.parcela)}</div>
                                                
                                                <div className="flex items-center gap-2">
                                                    {!isAberto ? (
                                                        <><span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_6px_#22c55e]"></span><span className="font-mono text-[9.5px] tracking-[0.16em] text-green-500">PAGO</span></>
                                                    ) : isVencida ? (
                                                        <><span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_6px_#ef4444]"></span><span className="font-mono text-[9.5px] tracking-[0.16em] text-red-500">ATRASADA</span></>
                                                    ) : (
                                                        <><span className="w-1.5 h-1.5 rounded-full" style={{ background: '#ffc247', boxShadow: '0 0 6px #ffc247' }}></span><span className="font-mono text-[9.5px] tracking-[0.16em]" style={{ color: '#ffc247' }}>ABERTA</span></>
                                                    )}
                                                </div>
                                                
                                                <div className="font-mono text-[10px] text-right" style={{ color: '#5a4e42' }}>{r.data}</div>

                                                <button
                                                    onClick={(e) => { e.stopPropagation(); abrirEdicaoParcela(r); }}
                                                    title="Editar parcela"
                                                    className="p-1 rounded opacity-40 group-hover/row:opacity-100 hover:bg-white/10 transition-all"
                                                    style={{ color: '#ffc247' }}>
                                                    <Pencil size={13}/>
                                                </button>
                                            </div>

                                            {isSelected && isAberto && (
                                                <div className="px-6 py-4 animate-in slide-in-from-top-2" style={{ background: 'rgba(255, 122, 26, 0.02)', borderLeft: '2px solid #ff7a1a' }}>
                                                    <form onSubmit={(e) => submitBaixa(e, r.id)} className="flex items-end gap-4">
                                                        <div className="flex-1 grid grid-cols-4 gap-4">
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Valor</label>
                                                                <input id={`input-valor-${r.id}`} autoFocus type="number" step="0.01" required value={baixaForm.valor_pago} onChange={e => setBaixaForm({...baixaForm, valor_pago: e.target.value})} onFocus={(e) => e.target.select()} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-[#f0e6d8] rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] font-mono" />
                                                            </div>
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Acréscimos</label>
                                                                <input type="number" step="0.01" value={baixaForm.acrescimos} onChange={e => setBaixaForm({...baixaForm, acrescimos: e.target.value})} onFocus={(e) => e.target.select()} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-green-400 rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] font-mono" />
                                                            </div>
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Descontos</label>
                                                                <input type="number" step="0.01" value={baixaForm.descontos} onChange={e => setBaixaForm({...baixaForm, descontos: e.target.value})} onFocus={(e) => e.target.select()} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-red-400 rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] font-mono" />
                                                            </div>
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Data Pgto</label>
                                                                <input type="date" required value={baixaForm.data_pagamento} onChange={e => setBaixaForm({...baixaForm, data_pagamento: e.target.value})} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-[#f0e6d8] rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] dark-calendar font-mono" />
                                                            </div>
                                                        </div>
                                                        <button type="submit" className="h-[34px] px-6 rounded-lg text-[10px] font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(255,122,26,0.2)] hover:opacity-90 transition-opacity flex items-center justify-center gap-2" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                                                            <CheckCircle2 size={12} /> Salvar <kbd className="ml-1 text-[9px] bg-black/20 px-1 rounded">↵</kbd>
                                                        </button>
                                                    </form>
                                                </div>
                                            )}
                                            
                                            {isSelected && !isAberto && (
                                                <div className="px-6 py-4 flex gap-8 items-center animate-in slide-in-from-top-2" style={{ background: 'rgba(34, 197, 94, 0.02)', borderLeft: '2px solid #22c55e' }}>
                                                    <div>
                                                        <span className="font-mono text-[9px] tracking-[0.18em] text-green-600/70 block mb-1">DATA EFETIVA</span>
                                                        <span className="text-[12px] font-mono text-green-500 font-bold">{r.data_pagamento || r.data}</span>
                                                    </div>
                                                    <div>
                                                        <span className="font-mono text-[9px] tracking-[0.18em] text-green-600/70 block mb-1">TOTAL PAGO</span>
                                                        <span className="text-[12px] font-mono text-green-500 font-bold">{formatCurrency(r.total)}</span>
                                                    </div>
                                                    <div>
                                                        <span className="font-mono text-[9px] tracking-[0.18em] text-green-600/70 block mb-1">VARIAÇÃO</span>
                                                        <span className="text-[12px] font-mono text-green-500">{formatCurrency(r.variacao)}</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
      </div>

      <div className="px-6 py-2 flex justify-between items-center shrink-0 z-20" style={{ background: '#0c0908', borderTop: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex gap-4 font-mono text-[9px] font-bold tracking-[0.16em]" style={{ color: '#5a4e42' }}>
            <span>↑ ↓ NAVEGAR</span>
            <span>⇥ CAMPOS</span>
            <span>↵ SALVAR E PULAR</span>
            <span>/ BUSCAR</span>
            <span>⇧⌘E EXPORTAR</span>
        </div>
      </div>

      {/* MODAL EDITAR PARCELA */}
      {editParcelaModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[110] animate-in fade-in p-6">
            <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6" style={{ background: '#0c0908', border: '1px solid rgba(255, 160, 80, 0.18)' }}>
                <h3 className="text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-1" style={{ color: '#f0e6d8' }}>
                    <Pencil size={18} color="#ff7a1a"/> Editar Parcela
                </h3>
                <p className="text-[11px] mb-5" style={{ color: '#8a7a68' }}>
                    <b style={{ color: '#f0e6d8' }}>#{String(editParcelaModal.row.id).replace('prazo_', 'pr_')}</b> — {editParcelaModal.row.cliente} · {editParcelaModal.row.descricao_venda}
                    {String(editParcelaModal.row.id).startsWith('prazo_') && <> <span style={{ color: '#ffd28a' }}>(parcela de cronograma ainda não efetivada)</span></>}
                </p>
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Vencimento</label>
                        <input type="date" min="1990-01-01" value={editParcelaModal.data} onChange={(e) => setEditParcelaModal({ ...editParcelaModal, data: e.target.value })} className="w-full p-2.5 rounded text-[11px] outline-none dark-calendar" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Valor da parcela</label>
                        <input type="number" step="0.01" value={editParcelaModal.valor} onChange={(e) => setEditParcelaModal({ ...editParcelaModal, valor: e.target.value })} placeholder="0,00" className="w-full p-2.5 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Parcela (rótulo)</label>
                        <input value={editParcelaModal.rotulo} onChange={(e) => setEditParcelaModal({ ...editParcelaModal, rotulo: e.target.value })} placeholder="ex.: 95/240" className="w-full p-2.5 rounded text-[11px] outline-none font-mono" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                    </div>
                    {!String(editParcelaModal.row.id).startsWith('prazo_') && (
                        <div>
                            <label className="text-[10px] uppercase font-bold mb-1 block" style={{ color: '#8a7a68' }}>Observação</label>
                            <input value={editParcelaModal.obs} onChange={(e) => setEditParcelaModal({ ...editParcelaModal, obs: e.target.value })} className="w-full p-2.5 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} />
                        </div>
                    )}
                </div>
                <div className="flex justify-end gap-3">
                    <button onClick={() => setEditParcelaModal(null)} className="px-4 py-2 hover:bg-white/5 transition-colors text-[11px] font-bold uppercase tracking-widest rounded" style={{ color: '#8a7a68' }}>Cancelar</button>
                    <button onClick={salvarEdicaoParcela} disabled={salvandoParcelaEdit} className="px-6 py-2 rounded text-[11px] font-bold uppercase tracking-widest disabled:opacity-50" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                        {salvandoParcelaEdit ? 'Gravando...' : 'Salvar'}
                    </button>
                </div>
            </div>
        </div>
      )}

    </div>
  );
}
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
          ? ' Nenhuma linha: o regex do modelo pode não bater com este PDF (ou resposta inválida). Tente "Só IA" para comparar.'
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
          className="bg-[var(--v-hover)] border border-[#F97316]/40 text-[var(--v-accent-5)] hover:bg-[#F97316] hover:text-black py-2 px-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] disabled:opacity-50 transition-colors"
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
                          className={`px-4 py-1.5 text-[10px] uppercase font-bold tracking-widest rounded-[var(--v-radius)] transition-colors ${viewMode === 'raw' ? 'bg-[#F97316] text-[var(--v-text-bold)]' : 'text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)]'}`}
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
                            ? 'bg-[#F97316]/20 border-[#F97316]/60 text-[var(--v-accent-5)] shadow-[0_0_10px_rgba(162,89,255,0.3)]'
                            : 'bg-[var(--v-hover)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent-5)] hover:border-[#F97316]/40'
                        }`}
                      >
                        <Zap size={12} className={useSplinkMatch ? 'text-[var(--v-accent-5)]' : 'text-[var(--v-text-faint)]'}/>
                        {useSplinkMatch ? 'Splink ON' : 'Splink OFF'}
                      </button>
                      <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="bg-[var(--v-hover)] border border-[var(--v-border)] hover:border-[#F97316] text-[var(--v-text-muted)] hover:text-[#fff] px-3 py-2 rounded transition-colors text-[10px] font-bold uppercase tracking-widest flex items-center gap-2"
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
                                            <span className={`text-[9px] font-black px-1.5 py-0.5 rounded uppercase ${d.match_engine === 'splink' ? 'bg-[#F97316]/20 text-[var(--v-accent-5)] border border-[#F97316]/30' : 'bg-[var(--v-hover)] text-[var(--v-text-faint)] border border-[var(--v-border)]'}`}>
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
                      className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-widest text-center transition-colors border-r border-[var(--v-border)] flex items-center justify-center gap-2 ${chatTab === 'chat' ? 'bg-[var(--v-hover)] text-[var(--v-accent-5)] border-t-2 border-t-[#F97316]' : 'bg-[var(--v-deep)] text-[var(--v-text-muted)] hover:bg-[var(--v-hover)] border-t-2 border-transparent'}`}
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
                            Ex.: "Remover linhas sem data", "Corrigir parcela 01/10A para 01/10", "Trocar vírgula por ponto em valor_parcela".
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
                            className="flex-1 bg-[var(--v-deep)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#F97316]"
                            disabled={isChatting}
                          />
                          <button
                            onClick={handleChatAdjust}
                            disabled={isChatting || !chatInput.trim()}
                            className="bg-[#F97316] text-black px-3 py-2 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] disabled:opacity-60 flex items-center gap-2"
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
