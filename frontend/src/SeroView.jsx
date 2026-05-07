import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, AlertCircle, RefreshCw, Building2, HardHat, FileBarChart2, TrendingUp, Ruler, UploadCloud, Save, Download, X } from 'lucide-react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts';
import * as XLSX from 'xlsx';
import { API_BASE } from './apiBase';

const fmt = (val) => {
    if (val === null || val === undefined || isNaN(val)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

const fmtM2 = (val) =>
    Number(val || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' m²';

// ── Card de KPI ──────────────────────────────────────────────────────────────
const KpiCard = ({ icon: Icon, label, value, sub, accent = 'var(--v-accent-2)', glow = false, large = false, onClick }) => (
    <div onClick={onClick} style={{ borderTopColor: accent }} className={`relative bg-[#0e0e0e] border border-[#1e1e1e] border-t-2 rounded-xl p-5 flex flex-col gap-1 overflow-hidden group hover:border-[#2e2e2e] transition-all duration-300 ${onClick ? 'cursor-pointer' : ''}`}>
        {glow && <div style={{ background: accent }} className="absolute inset-0 opacity-[0.04] pointer-events-none rounded-xl" />}
        <div className="flex items-center gap-2 mb-1">
            <Icon size={12} style={{ color: accent }} />
            <span className="text-[9px] font-black uppercase tracking-[0.2em]" style={{ color: accent }}>{label}</span>
        </div>
        <span style={{ color: glow ? accent : 'var(--v-text-bold)' }}
              className={`${large ? 'text-2xl' : 'text-xl'} font-black leading-tight ${glow ? 'drop-shadow-[0_0_12px_rgba(255,100,50,0.4)]' : ''}`}>
            {value}
        </span>
        {sub && <span className="text-[9px] text-[#444] mt-0.5">{sub}</span>}
    </div>
);

// ── Tooltip customizado ───────────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-[#111] border border-[#2a2a2a] rounded-lg p-3 text-[11px] shadow-xl">
            <p className="text-[#666] font-mono mb-2 text-[10px]">{label}</p>
            {payload.map((p, i) => (
                <div key={i} className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
                    <span className="text-[#888]">{p.name === 'previsto' ? 'Previsto' : 'Realizado'}</span>
                    <span className="font-black text-white ml-auto pl-4">
                        {fmt(p.value)}
                    </span>
                </div>
            ))}
        </div>
    );
};

// ── Componente principal ──────────────────────────────────────────────────────
export const SeroView = ({ selectedEmpresa }) => {
    const [ano, setAno] = useState((new Date().getFullYear() - (new Date().getMonth() < 3 ? 1 : 0)).toString());
    const [mes, setMes] = useState(new Date().getMonth() < 3 ? '12' : (new Date().getMonth()).toString().padStart(2, '0'));
    const [seroData, setSeroData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [obras, setObras] = useState([]);
    const [selectedObraId, setSelectedObraId] = useState('');
    const [importingPdf, setImportingPdf] = useState(false);
    const [pdfData, setPdfData] = useState(null);
    const [savingPdf, setSavingPdf] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [modalDetail, setModalDetail] = useState(null);

    useEffect(() => {
        if (!selectedEmpresa) return;
        fetch(`${API_BASE}/api/sero/obras?empresa_id=${selectedEmpresa}`, { cache: 'no-cache' })
            .then(res => {
                const ct = res.headers.get('content-type') || '';
                if (!ct.includes('application/json')) return [];
                return res.json();
            })
            .then(data => setObras(Array.isArray(data) ? data : []))
            .catch(console.error);
    }, [selectedEmpresa]);

    const fetchSero = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        setLoading(true); setError(null);
        try {
            const ep = selectedObraId
                ? `${API_BASE}/api/sero/maodeobra?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}&cno=${selectedObraId}`
                : `${API_BASE}/api/sero/maodeobra?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`;
            const res = await fetch(ep);
            if (!res.ok) { const t = await res.text(); throw new Error(`HTTP ${res.status}: ${t}`); }
            setSeroData(await res.json());
        } catch (err) {
            setError(err.message); setSeroData(null);
        } finally { setLoading(false); }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setImportingPdf(true);
        setError(null);
        setPdfData(null);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`${API_BASE}/api/sero/importar-pdf`, {
                method: 'POST',
                body: formData
            });
            if (!res.ok) {
                const t = await res.text();
                throw new Error(`HTTP ${res.status}: ${t}`);
            }
            const data = await res.json();
            setPdfData(data);
        } catch (err) {
            setError(`Erro ao ler PDF: ${err.message}`);
        } finally {
            setImportingPdf(false);
            e.target.value = ''; // reseta input
        }
    };

    const handleSavePdfData = async () => {
        if (!pdfData || pdfData.length === 0 || !selectedEmpresa) return;
        setSavingPdf(true);
        setError(null);
        setSaveSuccess(false);

        try {
            const res = await fetch(`${API_BASE}/api/sero/salvar-importacao`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    empresa_id: parseInt(selectedEmpresa, 10),
                    registros: pdfData
                })
            });
            if (!res.ok) {
                const t = await res.text();
                throw new Error(`HTTP ${res.status}: ${t}`);
            }
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 4000);
        } catch (err) {
            setError(`Erro ao salvar dados: ${err.message}`);
        } finally {
            setSavingPdf(false);
        }
    };


    useEffect(() => {
        if (selectedEmpresa && ano && mes) fetchSero();
    }, [selectedEmpresa, selectedObraId, ano, mes]);

    const r = seroData?.resumo || {};
    const obraAtual = obras.find(o => String(o.id) === String(selectedObraId));

    const mergedData = React.useMemo(() => {
        if (!pdfData) return null;
        const pdfComps = new Set(pdfData.map(p => p.competencia));
        const sysData = (seroData?.alocacoes_terceiros || []).filter(t => !pdfComps.has(t.compet)).map(t => ({
            competencia: t.compet,
            cnpj_cpf: t.cno,
            origem: t.nome_obra + ' (Questor)',
            valor_original: null,
            taxa_correcao: null,
            valor_atualizado: t.valor_recolhido,
            is_system: true
        }));
        const merged = [...pdfData.map(p => ({ ...p, is_system: false })), ...sysData];
        merged.sort((a, b) => (a.competencia < b.competencia ? 1 : -1));
        return merged;
    }, [pdfData, seroData]);

    const totalTerceiros = React.useMemo(() => {
        if (pdfData && mergedData) {
            return mergedData.reduce((s, t) => s + (t.valor_atualizado || 0), 0);
        }
        return r.mao_de_obra_terceiros_gps || 0;
    }, [pdfData, mergedData, r.mao_de_obra_terceiros_gps]);

    const totalBaseMO = (r.mao_de_obra_folha || 0) + totalTerceiros;

    const chartData = React.useMemo(() => {
        if (!seroData?.curva_s) return [];
        if (!pdfData) return seroData.curva_s;

        const mesesValores = new Map();
        
        (seroData.alocacoes_folha || []).forEach(f => {
            mesesValores.set(f.compet, (mesesValores.get(f.compet) || 0) + (f.valor || 0));
        });
        
        (mergedData || []).forEach(t => {
            mesesValores.set(t.competencia, (mesesValores.get(t.competencia) || 0) + (t.valor_atualizado || 0));
        });

        let acumulado = 0;
        return seroData.curva_s.map(pt => {
            const valorMes = mesesValores.get(pt.mes) || 0;
            acumulado += valorMes;
            return {
                ...pt,
                realizado_mes: valorMes,
                realizado: acumulado
            };
        });
    }, [seroData, pdfData, mergedData]);

    const handleExportXLSX = () => {
        const dataToExport = pdfData ? mergedData : (seroData?.alocacoes_terceiros || []);
        if (!dataToExport || dataToExport.length === 0) return;

        const rows = dataToExport.map(t => {
            if (pdfData) {
                return {
                    'Competência': t.competencia,
                    'CPF / CNPJ': t.cnpj_cpf,
                    'Origem': t.origem,
                    'Valor Original': t.valor_original,
                    'Taxa': t.taxa_correcao,
                    'Valor Atualizado': t.valor_atualizado
                };
            } else {
                return {
                    'Competência': t.compet,
                    'Tomador / Obra': t.nome_obra,
                    'CNO / CNPJ': t.cno,
                    'GPS Recolhido': t.valor_recolhido
                };
            }
        });

        const ws = XLSX.utils.json_to_sheet(rows);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Terceiros");
        XLSX.writeFile(wb, `terceiros_sero_${ano}_${mes}.xlsx`);
    };

    return (
        <div className="w-full max-w-7xl mx-auto flex flex-col gap-6 pt-4 pb-10">

            {/* ── Cabeçalho ── */}
            <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <div className="w-8 h-8 rounded-lg bg-[var(--v-accent-2)]/10 border border-[var(--v-accent-2)]/20 flex items-center justify-center">
                            <Activity size={16} className="text-[var(--v-accent-2)]" />
                        </div>
                        <h2 className="text-2xl font-black tracking-tighter uppercase text-[var(--v-text-bold)]">
                            Painel SERO / INSS
                        </h2>
                    </div>
                    <p className="text-[10px] text-[#444] uppercase tracking-[0.25em] ml-11">
                        Auditoria de Mão de Obra · CNO · GPS
                    </p>
                </div>

                {/* Badge da obra selecionada */}
                {obraAtual && (
                    <div className="flex items-center gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-3 py-2">
                        <HardHat size={12} className="text-[var(--v-accent-2)]" />
                        <span className="text-[10px] text-[#888] uppercase tracking-widest">Obra filtrada:</span>
                        <span className="text-[11px] font-black text-white">{obraAtual.nome}</span>
                        <span className="text-[9px] font-mono text-[#555]">{obraAtual.inscricao}</span>
                    </div>
                )}
            </div>

            {/* ── Barra de Filtros ── */}
            <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-4 flex flex-wrap gap-3 items-end">

                {/* Select Obra */}
                <div className="flex-1 min-w-[240px]">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">
                        Obra / CEI / CNO
                    </label>
                    <div className="relative">
                        <Building2 size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#444] pointer-events-none" />
                        <select
                            value={selectedObraId}
                            onChange={e => setSelectedObraId(e.target.value)}
                            className="w-full bg-[#111] border border-[#222] hover:border-[#333] focus:border-[var(--v-accent-2)] text-white text-[11px] font-mono pl-7 pr-3 py-2 rounded-lg outline-none transition-colors appearance-none"
                        >
                            <option value="">Todas as Obras (Consolidado)</option>
                            {obras.map(o => (
                                <option key={o.id} value={String(o.id)}>
                                    {o.inscricao ? `${o.inscricao}  ${o.nome}` : o.nome}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Ano */}
                <div className="w-20">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Ano</label>
                    <select
                        value={ano}
                        onChange={e => setAno(e.target.value)}
                        className="w-full bg-[#111] border border-[#222] hover:border-[#333] focus:border-[var(--v-accent-2)] text-white text-[11px] font-mono px-2 py-2 rounded-lg outline-none transition-colors"
                    >
                        {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y} value={String(y)}>{y}</option>)}
                    </select>
                </div>

                {/* Mês */}
                <div className="w-20">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Mês</label>
                    <select
                        value={mes}
                        onChange={e => setMes(e.target.value)}
                        className="w-full bg-[#111] border border-[#222] hover:border-[#333] focus:border-[var(--v-accent-2)] text-white text-[11px] font-mono px-2 py-2 rounded-lg outline-none transition-colors"
                    >
                        {Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0')).map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                </div>

                {/* Botão */}
                <button
                    id="btn-processar-inss"
                    onClick={fetchSero}
                    disabled={loading}
                    className="flex items-center gap-2 bg-[var(--v-accent-2)]/10 border border-[var(--v-accent-2)]/25 text-[var(--v-accent-2)] hover:bg-[var(--v-accent-2)] hover:text-black transition-all duration-200 font-black text-[9px] tracking-[0.2em] uppercase rounded-lg px-5 py-2 h-[34px] disabled:opacity-40"
                >
                    {loading
                        ? <RefreshCw size={12} className="animate-spin" />
                        : <ShieldCheck size={12} />}
                    {loading ? 'Processando...' : 'Apurar INSS'}
                </button>

                {/* Botão Upload PDF */}
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <input 
                            type="file" 
                            accept="application/pdf" 
                            onChange={handleFileUpload}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                            disabled={importingPdf}
                        />
                        <button
                            disabled={importingPdf}
                            className="flex items-center gap-2 bg-[#222]/50 border border-[#333] text-[#aaa] hover:bg-[#333] hover:text-white transition-all duration-200 font-black text-[9px] tracking-[0.2em] uppercase rounded-lg px-5 py-2 h-[34px] disabled:opacity-40"
                        >
                            {importingPdf 
                                ? <RefreshCw size={12} className="animate-spin" /> 
                                : <UploadCloud size={12} />}
                            {importingPdf ? 'Lendo PDF...' : 'Importar PDF SERO'}
                        </button>
                    </div>
                    {pdfData && (
                        <button
                            onClick={() => { setPdfData(null); setError(null); }}
                            className="flex items-center justify-center w-[34px] h-[34px] bg-[#222] border border-[#333] text-[#888] hover:bg-red-900/40 hover:text-red-400 hover:border-red-900/50 transition-all duration-200 rounded-lg"
                            title="Descartar Importação"
                        >
                            <X size={14} />
                        </button>
                    )}
                </div>

                {/* Competência ativa */}
                <div className="ml-auto text-right hidden sm:block">
                    <div className="text-[9px] text-[#444] uppercase tracking-widest">Competência</div>
                    <div className="text-[13px] font-black font-mono text-[#666]">{ano}-{mes}</div>
                </div>
            </div>

            {/* ── Erro ── */}
            {error && !seroData && !pdfData && (
                <div className="bg-red-950/30 text-red-400 border border-red-900/40 rounded-xl p-4 flex items-center gap-3 text-sm">
                    <AlertCircle size={18} /> <span className="font-bold">{error}</span>
                </div>
            )}
            
            {/* ── Sucesso ao Salvar ── */}
            {saveSuccess && (
                <div className="bg-emerald-950/30 text-emerald-400 border border-emerald-900/40 rounded-xl p-4 flex items-center gap-3 text-sm">
                    <ShieldCheck size={18} /> <span className="font-bold">Dados salvos com sucesso no Vulcano!</span>
                </div>
            )}

            {/* ── Loading skeleton ── */}
            {loading && !seroData && (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {[...Array(6)].map((_, i) => (
                        <div key={i} className="bg-[#0e0e0e] border border-[#1a1a1a] rounded-xl p-5 h-24 animate-pulse">
                            <div className="bg-[#1a1a1a] h-2 w-20 rounded mb-3" />
                            <div className="bg-[#1a1a1a] h-6 w-32 rounded" />
                        </div>
                    ))}
                </div>
            )}

            {/* ── KPIs ── */}
            {seroData && (
                <>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                        <KpiCard
                            icon={FileBarChart2}
                            label="Base MO Total"
                            value={fmt(totalBaseMO)}
                            sub="Folha + GPS acumulado"
                            accent="var(--v-accent-2)"
                        />
                        <KpiCard
                            icon={TrendingUp}
                            label="Folha Própria"
                            value={fmt(r.mao_de_obra_folha)}
                            sub="VER DETALHAMENTO (CLIQUE)"
                            accent="#60a5fa"
                            onClick={() => setModalDetail('folha')}
                        />
                        <KpiCard
                            icon={Building2}
                            label="Terceiros GPS"
                            value={fmt(totalTerceiros)}
                            sub={pdfData ? "SERO Atualizado" : "VALORORIGEMGPS"}
                            accent="#34d399"
                        />
                        <KpiCard
                            icon={ShieldCheck}
                            label="INSS a Recolher"
                            value={fmt(r.total_inss)}
                            sub="Passivo apurado"
                            accent="#f97316"
                            glow
                            large
                        />
                        <KpiCard
                            icon={HardHat}
                            label="CUB Vigente"
                            value={fmt(r.cub_vigente)}
                            sub="Índice padrão SC"
                            accent="#a78bfa"
                        />
                        <KpiCard
                            icon={Ruler}
                            label="Área da Obra"
                            value={fmtM2(r.area_total)}
                            sub="EMPREENDIMENTO Vulcano"
                            accent="#00ff88"
                        />
                    </div>

                    {/* ── Divisor visual ── */}
                    <div className="flex items-center gap-3">
                        <div className="h-px flex-1 bg-[#1a1a1a]" />
                        <span className="text-[9px] uppercase tracking-[0.25em] text-[#333] font-bold">Análise Histórica</span>
                        <div className="h-px flex-1 bg-[#1a1a1a]" />
                    </div>

                    {/* ── Gráfico Curva-S ── */}
                    <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-5">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#555]">
                                    Avanço Físico-Financeiro — Curva-S
                                </h4>
                                <p className="text-[9px] text-[#333] mt-0.5">Previsto (CUB × m²) vs Realizado (Folha + GPS)</p>
                            </div>
                            <div className="flex items-center gap-4 text-[9px]">
                                <span className="flex items-center gap-1.5"><span className="inline-block w-4 h-px border-t border-dashed border-[#555]" />Previsto</span>
                                <span className="flex items-center gap-1.5 text-[var(--v-accent-2)]"><span className="inline-block w-4 h-0.5 bg-[var(--v-accent-2)] rounded" />Realizado</span>
                            </div>
                        </div>
                        <div className="h-52">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="gradPrev" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#444" stopOpacity={0.15} />
                                            <stop offset="95%" stopColor="#444" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="gradReal" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--v-accent-2)" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="var(--v-accent-2)" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#181818" vertical={false} />
                                    <XAxis dataKey="mes" stroke="#333" fontSize={9} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#333" fontSize={9} tickLine={false} axisLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Area type="monotone" dataKey="previsto" stroke="#444" strokeWidth={1} strokeDasharray="5 5" fill="url(#gradPrev)" dot={false} name="previsto" />
                                    <Area type="monotone" dataKey="realizado" stroke="var(--v-accent-2)" strokeWidth={2.5} fill="url(#gradReal)" dot={{ fill: 'var(--v-accent-2)', r: 3, strokeWidth: 0 }} name="realizado" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* ── Tabela Terceiros GPS ── */}
                    {(seroData.alocacoes_terceiros?.length > 0 || pdfData?.length > 0) && (
                        <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl overflow-hidden mt-6">
                            <div className="flex items-center justify-between px-5 py-3 border-b border-[#161616]">
                                <div className="flex items-center gap-2">
                                    <div className="w-1.5 h-4 rounded-full bg-[#34d399]" />
                                    <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#34d399]">
                                        {pdfData ? 'Terceiros SERO (Fonte: PDF)' : 'Terceiros GPS (Questor)'}
                                    </h4>
                                    <span className="text-[9px] text-[#444] font-mono">
                                        {pdfData ? pdfData.length : seroData.alocacoes_terceiros.length} registros
                                    </span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={handleExportXLSX}
                                        className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-[#888] hover:text-[#34d399] transition-colors"
                                    >
                                        <Download size={12} />
                                        Exportar XLSX
                                    </button>
                                    <span className="text-[9px] text-[#555] uppercase tracking-widest hidden sm:block">
                                        {pdfData ? 'DADOS EXTRAÍDOS DO PDF ORIGINAL' : 'TERCEIROPGTO · VALORORIGEMGPS'}
                                    </span>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-[11px]">
                                    <thead>
                                        <tr className="border-b border-[#161616]">
                                            <th className="text-left px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#333] font-bold">Competência</th>
                                            <th className="text-left px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#333] font-bold">
                                                {pdfData ? 'CPF / CNPJ' : 'Tomador / Obra'}
                                            </th>
                                            <th className="text-left px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#333] font-bold">
                                                {pdfData ? 'Origem' : 'CNO / CNPJ'}
                                            </th>
                                            {pdfData && <th className="text-right px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#333] font-bold">Valor Original</th>}
                                            {pdfData && <th className="text-right px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#333] font-bold">Taxa</th>}
                                            <th className="text-right px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#333] font-bold">
                                                {pdfData ? 'Valor Atualizado' : 'GPS Recolhido'}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {pdfData ? (
                                            mergedData.map((t, i) => (
                                                <tr key={i} className={`border-b border-[#0f0f0f] hover:bg-[#111] transition-colors ${t.is_system ? 'opacity-60' : ''}`}>
                                                    <td className="px-5 py-2 font-mono text-[#444] text-[10px]">{t.competencia}</td>
                                                    <td className="px-5 py-2 font-mono text-[#888] text-[10px]">{t.cnpj_cpf}</td>
                                                    <td className="px-5 py-2 text-white max-w-[200px] truncate" title={t.origem}>{t.origem}</td>
                                                    <td className="px-5 py-2 text-right font-mono text-[#666]">{t.valor_original !== null ? fmt(t.valor_original) : '-'}</td>
                                                    <td className="px-5 py-2 text-right font-mono text-[#666]">{t.taxa_correcao !== null ? Number(t.taxa_correcao).toFixed(4) : '-'}</td>
                                                    <td className="px-5 py-2 text-right font-black text-[#34d399]">{fmt(t.valor_atualizado)}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            seroData.alocacoes_terceiros.slice(0, 60).map((t, i) => (
                                                <tr key={i} className="border-b border-[#0f0f0f] hover:bg-[#111] transition-colors">
                                                    <td className="px-5 py-2 font-mono text-[#444] text-[10px]">{t.compet}</td>
                                                    <td className="px-5 py-2 text-[#888] max-w-[260px] truncate">{t.nome_obra}</td>
                                                    <td className="px-5 py-2 font-mono text-[#444] text-[10px]">{t.cno}</td>
                                                    <td className="px-5 py-2 text-right font-black text-[#34d399]">{fmt(t.valor_recolhido)}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                    <tfoot>
                                        <tr className="border-t border-[#1e1e1e] bg-[#0e0e0e]">
                                            <td colSpan={pdfData ? 5 : 3} className="px-5 py-2.5 text-[9px] uppercase tracking-widest text-[#444] font-bold">
                                                {pdfData ? 'Total Atualizado' : 'Total GPS'}
                                            </td>
                                            <td className="px-5 py-2.5 text-right font-black text-[#34d399]">
                                                {pdfData 
                                                    ? fmt(mergedData.reduce((s, t) => s + (t.valor_atualizado || 0), 0))
                                                    : fmt(seroData.alocacoes_terceiros.reduce((s, t) => s + (t.valor_recolhido || 0), 0))}
                                            </td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                            
                            {/* ── Botões de Ação (Apenas se tiver PDF Data) ── */}
                            {pdfData && (
                                <div className="px-5 py-4 border-t border-[#161616] bg-[#0e0e0e] flex justify-end gap-3">
                                    <button
                                        onClick={() => { setPdfData(null); setError(null); }}
                                        disabled={savingPdf}
                                        className="flex items-center gap-2 bg-[#222] border border-[#333] text-[#aaa] hover:bg-red-900/40 hover:border-red-900/50 hover:text-red-400 transition-all duration-200 font-black text-[10px] tracking-[0.15em] uppercase rounded-lg px-5 py-2.5 h-[36px] disabled:opacity-40"
                                    >
                                        <X size={14} />
                                        Descartar
                                    </button>
                                    <button
                                        onClick={handleSavePdfData}
                                        disabled={savingPdf}
                                        className="flex items-center gap-2 bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] hover:bg-[#10b981] hover:text-black transition-all duration-200 font-black text-[10px] tracking-[0.15em] uppercase rounded-lg px-5 py-2.5 h-[36px] disabled:opacity-40"
                                    >
                                        {savingPdf ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                                        {savingPdf ? 'Salvando...' : 'Salvar Extrato no Vulcano'}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* ── Estado vazio ── */}
            {!seroData && !loading && !error && (
                <div className="flex flex-col items-center justify-center py-24 text-[#333]">
                    <ShieldCheck size={48} className="mb-4 opacity-20" />
                    <p className="text-sm font-bold uppercase tracking-widest">Selecione uma empresa e clique em Apurar INSS</p>
                </div>
            )}

            {/* ── Modal Detalhamento Folha ── */}
            {modalDetail === 'folha' && seroData?.alocacoes_folha && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-[#0a0a0a] border border-[#222] rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-[#222] bg-[#111]">
                            <div className="flex items-center gap-3">
                                <TrendingUp size={16} className="text-[#60a5fa]" />
                                <div>
                                    <h3 className="text-sm font-black text-white uppercase tracking-widest">Detalhamento: Folha Própria</h3>
                                    <p className="text-[10px] text-[#888]">Eventos 5041 Rateados (Acumulado até a competência selecionada)</p>
                                </div>
                            </div>
                            <button onClick={() => setModalDetail(null)} className="text-[#888] hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-0 overflow-y-auto custom-scrollbar">
                            <table className="w-full text-left text-[11px]">
                                <thead className="bg-[#111] sticky top-0 border-b border-[#222]">
                                    <tr>
                                        <th className="px-6 py-3 font-bold text-[#888] uppercase tracking-widest">Competência</th>
                                        <th className="px-6 py-3 font-bold text-[#888] uppercase tracking-widest">Obra / Cadastro Questor</th>
                                        <th className="px-6 py-3 font-bold text-[#888] uppercase tracking-widest text-right">Valor Rateado</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#1a1a1a]">
                                    {seroData.alocacoes_folha.map((t, idx) => (
                                        <tr key={idx} className="hover:bg-[#111] transition-colors">
                                            <td className="px-6 py-3 font-mono text-[#aaa] text-[10px]">{t.compet}</td>
                                            <td className="px-6 py-3 text-[#eee]">{t.nome_obra} <span className="text-[9px] text-[#555] ml-2">[{t.codigooutemp}]</span></td>
                                            <td className="px-6 py-3 font-black text-[#60a5fa] text-right">{fmt(t.valor)}</td>
                                        </tr>
                                    ))}
                                    {seroData.alocacoes_folha.length === 0 && (
                                        <tr>
                                            <td colSpan={3} className="px-6 py-8 text-center text-[#555]">Nenhum registro encontrado.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                        <div className="px-6 py-4 border-t border-[#222] bg-[#111] flex justify-end">
                            <button onClick={() => setModalDetail(null)} className="px-6 py-2 bg-[#222] hover:bg-[#333] text-white rounded-lg text-[10px] uppercase tracking-widest font-bold transition-colors">
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
