import React, { useState } from 'react';
import { FileText, Download, ShieldCheck, AlertCircle, RefreshCw, Code2, CheckCircle2, ReceiptText } from 'lucide-react';
import { API_BASE } from './apiBase';

const fmt = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

// ── Tab pill ──────────────────────────────────────────────────────────────────
const Tab = ({ active, onClick, accent, children }) => (
    <button
        onClick={onClick}
        className="relative pb-3 px-1 text-[10px] font-black uppercase tracking-[0.2em] transition-colors"
        style={{ color: active ? accent : '#444' }}
    >
        {children}
        {active && (
            <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: accent }} />
        )}
    </button>
);

// ── Botão padrão Magma ────────────────────────────────────────────────────────
const MagmaBtn = ({ onClick, disabled, loading, icon: Icon, label, accent, filled = false }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        style={filled
            ? { background: accent, color: '#000' }
            : { borderColor: `${accent}44`, color: accent }}
        className={`flex items-center gap-2 ${filled ? '' : 'bg-transparent border'} rounded-lg px-4 py-2 text-[9px] font-black uppercase tracking-[0.2em] transition-all disabled:opacity-40 hover:opacity-80`}
    >
        {loading ? <RefreshCw size={11} className="animate-spin" /> : <Icon size={11} />}
        {loading ? 'Aguarde...' : label}
    </button>
);

// ── Cabeçalho de tabela padrão ────────────────────────────────────────────────
const Th = ({ children, right = false, accent }) => (
    <th className={`px-4 py-3 text-[9px] font-black uppercase tracking-[0.2em] border-b border-[#161616] ${right ? 'text-right' : 'text-left'}`}
        style={{ color: accent || '#444' }}>
        {children}
    </th>
);

export const FiscalSpedView = ({ selectedEmpresa }) => {
    const [ano, setAno] = useState(new Date().getFullYear().toString());
    const [mes, setMes] = useState((new Date().getMonth() + 1).toString().padStart(2, '0'));
    const [retData, setRetData] = useState(null);
    const [resumoData, setResumoData] = useState(null);
    const [f200Data, setF200Data] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('RET');
    const [anoDimob, setAnoDimob] = useState(new Date().getFullYear().toString());
    const [loadingDimob, setLoadingDimob] = useState(false);
    const [dimobPreviewData, setDimobPreviewData] = useState(null);
    const [retCommitting, setRetCommitting] = useState(false);
    const [f200Committing, setF200Committing] = useState(false);
    const [visaoTecnica, setVisaoTecnica] = useState(false);

    const fetchRetPreview = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/ret/preview?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            if (!res.ok) throw new Error("Apuração RET falhou.");
            const d = await res.json();
            setRetData(Array.isArray(d) ? d : (d.data || [])); setActiveTab('RET');
        } catch (err) { setError(err.message); } finally { setLoading(false); }
    };

    const fetchF200 = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/f200/preview?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            if (!res.ok) throw new Error("Apuração F200 falhou.");
            setF200Data(await res.json()); setActiveTab('F200');
        } catch (err) { setError(err.message); } finally { setLoading(false); }
    };

    const fetchResumo = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/resumo?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : "Quadro Resumo falhou.");
            setResumoData(d); setActiveTab('RESUMO');
        } catch (err) { setError(err.message); } finally { setLoading(false); }
    };

    const commitRet = async () => {
        if (!selectedEmpresa || !ano || !mes || !retData) return;
        if (!window.confirm(`Gravar guias RET na competência ${mes}/${ano}?`)) return;
        setRetCommitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/sped/ret/commit?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`, { method: 'POST' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || data.detail || "Erro ao injetar RET.");
            alert("Sucesso: " + data.message);
            fetchRetPreview(); // recarrega para refletir os JÁ LANÇADO
        } catch (err) { alert(err.message); } finally { setRetCommitting(false); }
    };

    const commitF200 = async () => {
        if (!selectedEmpresa || !ano || !mes || !f200Data) return;
        if (!window.confirm(`Injetar lotes F200 da competência ${mes}/${ano} no Questor?`)) return;
        setF200Committing(true);
        try {
            const res = await fetch(`${API_BASE}/api/sped/f200/commit?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`, { method: 'POST' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || "Erro ao injetar F200.");
            alert("Sucesso: " + data.message);
        } catch (err) { alert(err.message); } finally { setF200Committing(false); }
    };

    const fetchDimobPreview = async () => {
        if (!selectedEmpresa || !anoDimob) return;
        setLoadingDimob(true);
        try {
            const res = await fetch(`${API_BASE}/api/dimob/preview?empresa_id=${selectedEmpresa}&ano=${anoDimob}`);
            const data = await res.json();
            if (!data.success) throw new Error(data.message || "Auditoria DIMOB falhou.");
            setDimobPreviewData(data);
        } catch (err) { alert(err.message); } finally { setLoadingDimob(false); }
    };

    const fetchDimob = async () => {
        if (!selectedEmpresa || !anoDimob) return;
        setLoadingDimob(true);
        try {
            const res = await fetch(`${API_BASE}/api/dimob/gerar?empresa_id=${selectedEmpresa}&ano=${anoDimob}`);
            if (!res.ok) throw new Error("Geração DIMOB falhou.");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `DIMOB_${anoDimob}_EMP_${selectedEmpresa}.txt`;
            document.body.appendChild(a); a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) { alert(err.message); } finally { setLoadingDimob(false); }
    };

    return (
        <div className="w-full max-w-7xl mx-auto flex flex-col gap-6 pt-4 pb-10">

            {/* ── Cabeçalho ── */}
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#f97316]/10 border border-[#f97316]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <ShieldCheck size={16} className="text-[#f97316]" />
                </div>
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase text-white">
                        Painel Fiscal &amp; SPED
                    </h2>
                    <p className="text-[10px] text-[#444] uppercase tracking-[0.25em]">
                        Auditoria e Compliance Tributário
                    </p>
                </div>
            </div>

            {/* ── Barra de filtros ── */}
            <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-4 flex flex-wrap gap-3 items-end">
                <div className="w-24">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Ano</label>
                    <select value={ano} onChange={e => setAno(e.target.value)}
                        className="w-full bg-[#111] border border-[#222] hover:border-[#333] text-white text-[11px] font-mono px-2 py-2 rounded-lg outline-none transition-colors">
                        {[2022, 2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                </div>
                <div className="w-20">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Mês</label>
                    <select value={mes} onChange={e => setMes(e.target.value)}
                        className="w-full bg-[#111] border border-[#222] hover:border-[#333] text-white text-[11px] font-mono px-2 py-2 rounded-lg outline-none transition-colors">
                        {Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0')).map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                </div>
                <div className="flex gap-2 flex-wrap">
                    <MagmaBtn onClick={fetchRetPreview} disabled={loading} loading={loading && activeTab === 'RET'}
                        icon={ShieldCheck} label="Apurar RET 4%" accent="#22c55e" />
                    <MagmaBtn onClick={fetchF200} disabled={loading} loading={loading && activeTab === 'F200'}
                        icon={FileText} label="Apurar F200 (Presumido)" accent="#60a5fa" />
                    <MagmaBtn onClick={fetchResumo} disabled={loading} loading={loading && activeTab === 'RESUMO'}
                        icon={FileText} label="Quadro Resumo" accent="#f59e0b" />
                </div>
                <div className="ml-auto text-right hidden sm:block">
                    <div className="text-[9px] text-[#444] uppercase tracking-widest">Competência</div>
                    <div className="text-[13px] font-black font-mono text-[#555]">{ano}-{mes}</div>
                </div>
            </div>

            {/* ── Erro ── */}
            {error && (
                <div className="bg-red-950/30 text-red-400 border border-red-900/40 rounded-xl p-4 flex items-center gap-3 text-sm">
                    <AlertCircle size={18} /> <span className="font-bold">{error}</span>
                </div>
            )}

            {/* ── Tabs ── */}
            <div className="flex gap-6 border-b border-[#1a1a1a]">
                <Tab active={activeTab === 'RET'} onClick={() => setActiveTab('RET')} accent="#22c55e">
                    Configuração RET 4%
                </Tab>
                <Tab active={activeTab === 'F200'} onClick={() => setActiveTab('F200')} accent="#60a5fa">
                    Operações F200 (EFD)
                </Tab>
                <Tab active={activeTab === 'RESUMO'} onClick={() => setActiveTab('RESUMO')} accent="#f59e0b">
                    Quadro Resumo
                </Tab>
            </div>

            {/* ── Conteúdo das tabs ── */}
            <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl overflow-hidden">

                {/* Estado vazio */}
                {!retData && !f200Data && !resumoData && !loading && (
                    <div className="flex flex-col items-center justify-center py-24 text-[#2a2a2a]">
                        <ShieldCheck size={52} className="mb-4" />
                        <p className="text-[10px] font-bold uppercase tracking-widest">Selecione uma competência e apure</p>
                    </div>
                )}

                {/* ── Quadro Resumo (F200 + 1800 por empreendimento) ── */}
                {activeTab === 'RESUMO' && resumoData && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-[11px]">
                            <thead>
                                <tr className="bg-[#0e0e0e]">
                                    <Th>Empreendimento</Th>
                                    <Th right>Recebimentos</Th>
                                    <Th right>Valor Parcela</Th>
                                    <Th right>Valor Variação</Th>
                                    <Th right>Distrato</Th>
                                    <Th right accent="#60a5fa">Base Cálculo</Th>
                                    <Th right accent="#60a5fa">Valor PIS</Th>
                                    <Th right accent="#60a5fa">Valor COFINS</Th>
                                    <Th right accent="#22c55e">Base Cálculo RET</Th>
                                    <Th right accent="#22c55e">Valor RET</Th>
                                </tr>
                            </thead>
                            <tbody>
                                {(resumoData.data || []).map((r, i) => (
                                    <tr key={i} className="border-b border-[#0f0f0f] hover:bg-[#111]">
                                        <td className="px-4 py-2.5 text-[#bbb] font-bold whitespace-nowrap">{r.empreendimento}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-white">{fmt(r.recebimentos)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#999]">{fmt(r.valor_parcela)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#777]">{fmt(r.variacao)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#777]">{fmt(r.distrato)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#60a5fa]">{fmt(r.bc_f200)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#60a5fa]">{fmt(r.pis)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#60a5fa]">{fmt(r.cofins)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[#22c55e]">{fmt(r.bc_ret)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right font-black text-[#22c55e]">{fmt(r.valor_ret)}</td>
                                    </tr>
                                ))}
                                {(resumoData.data || []).length === 0 && (
                                    <tr><td colSpan={10} className="py-16 text-center text-[#333] text-[10px] uppercase tracking-widest">
                                        Sem movimento na competência.
                                    </td></tr>
                                )}
                            </tbody>
                            {(resumoData.data || []).length > 0 && (
                                <tfoot>
                                    <tr className="bg-[#0e0e0e] border-t border-[#1e1e1e] font-mono font-bold">
                                        <td className="px-4 py-3 text-[9px] uppercase tracking-widest text-[#444]">Totais</td>
                                        <td className="px-4 py-3 text-right text-white">{fmt(resumoData.totais?.recebimentos)}</td>
                                        <td className="px-4 py-3 text-right text-[#999]">{fmt(resumoData.totais?.valor_parcela)}</td>
                                        <td className="px-4 py-3 text-right text-[#777]">{fmt(resumoData.totais?.variacao)}</td>
                                        <td className="px-4 py-3 text-right text-[#777]">{fmt(resumoData.totais?.distrato)}</td>
                                        <td className="px-4 py-3 text-right text-[#60a5fa]">{fmt(resumoData.totais?.bc_f200)}</td>
                                        <td className="px-4 py-3 text-right text-[#60a5fa]">{fmt(resumoData.totais?.pis)}</td>
                                        <td className="px-4 py-3 text-right text-[#60a5fa]">{fmt(resumoData.totais?.cofins)}</td>
                                        <td className="px-4 py-3 text-right text-[#22c55e]">{fmt(resumoData.totais?.bc_ret)}</td>
                                        <td className="px-4 py-3 text-right text-[#22c55e]">{fmt(resumoData.totais?.valor_ret)}</td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>
                    </div>
                )}

                {/* ── RET 4% ── */}
                {activeTab === 'RET' && retData && (
                    <div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-[11px]">
                                <thead>
                                    <tr className="bg-[#0e0e0e]">
                                        <Th>Obra (RET)</Th>
                                        <Th>Estab</Th>
                                        <Th>Status</Th>
                                        <Th right>Base de Cálculo</Th>
                                        <Th right accent="#22c55e">PIS</Th>
                                        <Th right accent="#22c55e">COFINS</Th>
                                        <Th right accent="#22c55e">CSLL</Th>
                                        <Th right accent="#22c55e">IRPJ</Th>
                                        <Th right accent="#f97316">Guia RET</Th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {retData.map((r, i) => (
                                        <tr key={i} className="border-b border-[#0f0f0f] hover:bg-[#111] transition-colors">
                                            <td className="px-4 py-3 font-mono font-bold text-[#888]">{r.unidade || 'N/A'}<span className="text-[#444]"> · {r.aliqret}%</span></td>
                                            <td className="px-4 py-3 font-mono text-[#666]">{r.codigoestab ?? '—'}</td>
                                            <td className="px-4 py-3 font-mono text-[10px]">
                                                <span style={{ color: r.status === 'PRONTO' ? '#22c55e' : r.status === 'JA_LANCADO' ? '#888' : '#f97316' }}>
                                                    {r.status === 'SEM_DE_PARA' ? 'SEM DE-PARA' : r.status === 'JA_LANCADO' ? 'JÁ LANÇADO' : r.status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 font-mono text-right text-white">{fmt(r.base_calculo)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[#555]">{fmt(r.pis)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[#555]">{fmt(r.cofins)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[#555]">{fmt(r.csll)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[#555]">{fmt(r.irpj)}</td>
                                            <td className="px-4 py-3 font-mono text-right font-black text-[#f97316]">{fmt(r.total_ret)}</td>
                                        </tr>
                                    ))}
                                    {retData.length === 0 && (
                                        <tr><td colSpan={9} className="py-16 text-center text-[#333] text-[10px] uppercase tracking-widest">
                                            Sem recebimento de obra optante pelo RET nesta competência — confira mês/ano (há baixas até fev/2026 na base local).
                                        </td></tr>
                                    )}
                                </tbody>
                                {retData.length > 0 && (
                                    <tfoot>
                                        <tr className="bg-[#0e0e0e] border-t border-[#1e1e1e]">
                                            <td colSpan={8} className="px-4 py-3 text-[9px] uppercase tracking-widest text-[#444] font-bold">Total RET a Recolher</td>
                                            <td className="px-4 py-3 text-right font-black text-[#f97316]">
                                                {fmt(retData.reduce((s, r) => s + (r.total_ret || 0), 0))}
                                            </td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>
                        {retData.length > 0 && (
                            <div className="border-t border-[#161616] p-4 flex justify-end">
                                <MagmaBtn onClick={commitRet} disabled={retCommitting} loading={retCommitting}
                                    icon={CheckCircle2} label="Confirmar e Injetar Lote RET no Questor"
                                    accent="#22c55e" filled />
                            </div>
                        )}
                    </div>
                )}

                {/* ── F200 ── */}
                {activeTab === 'F200' && f200Data && (
                    <div>
                        <div className="flex justify-end px-4 py-2 border-b border-[#161616]">
                            <button onClick={() => setVisaoTecnica(!visaoTecnica)}
                                className="flex items-center gap-1.5 text-[9px] text-[#60a5fa] uppercase tracking-widest font-bold hover:opacity-70 transition-opacity">
                                <Code2 size={11} />
                                {visaoTecnica ? 'Visão Resumida' : 'Modo Técnico JSON'}
                            </button>
                        </div>
                        <div className="overflow-x-auto">
                            {!visaoTecnica ? (
                                <table className="w-full text-[11px]">
                                    <thead>
                                        <tr className="bg-[#0e0e0e]">
                                            <Th>Unidade · Obra</Th>
                                            <Th>Cliente</Th>
                                            <Th>Status</Th>
                                            <Th>Data Venda</Th>
                                            <Th right>Total Venda</Th>
                                            <Th right>Rec. Acum.</Th>
                                            <Th right>Valor Parcela</Th>
                                            <Th right>Variação</Th>
                                            <Th right>Recebido no Mês</Th>
                                            <Th right accent="#60a5fa">PIS</Th>
                                            <Th right accent="#60a5fa">COFINS</Th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(f200Data.data || []).map((r, i) => (
                                            <tr key={i} className="border-b border-[#0f0f0f] hover:bg-[#111] transition-colors">
                                                <td className="px-4 py-3 font-mono text-[#888] max-w-52 truncate whitespace-nowrap">
                                                    #{r.numcadimob ?? '?'} {(r.unidade || '').replace(/\s+/g, ' ')}
                                                    <span className="text-[#444]"> · {r.obra}</span>
                                                </td>
                                                <td className="px-4 py-3 text-[#777] max-w-40 truncate whitespace-nowrap">{r.cliente}</td>
                                                <td className="px-4 py-3 font-mono text-[10px]">
                                                    <span style={{ color: (r.status === 'PRONTO' || r.status === 'NOVO_CADASTRO') ? '#22c55e' : r.status === 'JA_LANCADO' ? '#888' : '#f97316' }}>
                                                        {r.status === 'JA_LANCADO' ? 'JÁ LANÇADO' : r.status?.replace(/_/g, ' ')}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 font-mono text-[#666] whitespace-nowrap">{r.dtoper ? r.dtoper.split('-').reverse().join('/') : ''}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[#999]">{fmt(r.vltotvend)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[#555]">{fmt(r.vlrecacum)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[#999]">{fmt(r.valor_parcela ?? r.vltotrec)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[#777]">{fmt(r.variacao)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-white">{fmt(r.vltotrec)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[#60a5fa]">{fmt(r.vlpis)} <span className="text-[#444]">({r.aliqpis}%)</span></td>
                                                <td className="px-4 py-3 font-mono text-right text-[#60a5fa]">{fmt(r.vlcofins)} <span className="text-[#444]">({r.aliqcofins}%)</span></td>
                                            </tr>
                                        ))}
                                        {(f200Data.data || []).length === 0 && (
                                            <tr><td colSpan={11} className="py-16 text-center text-[#333] text-[10px] uppercase tracking-widest">
                                                Sem recebimentos F200 (fora do RET) para a competência.
                                            </td></tr>
                                        )}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="p-4 flex flex-col gap-3">
                                    {(f200Data.data || []).map((r, i) => (
                                        <div key={i} className="border-l-2 border-[#60a5fa] pl-4 bg-[#0e0e0e] rounded-r-lg p-3">
                                            <p className="text-[9px] uppercase tracking-widest text-[#444] font-bold mb-2">EFDUNIDIMOBVENDIDA · #{r.numcadimob} · {r.status}</p>
                                            <pre className="text-[10px] text-[#60a5fa] font-mono bg-black p-3 rounded-lg border border-[#1a1a1a] overflow-auto">
                                                {JSON.stringify(r, null, 2)}
                                            </pre>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        {(f200Data.data || []).length > 0 && (
                            <div className="border-t border-[#161616] p-4 flex justify-end">
                                <MagmaBtn onClick={commitF200} disabled={f200Committing} loading={f200Committing}
                                    icon={CheckCircle2} label="Confirmar e Injetar Lote F200 no Questor"
                                    accent="#60a5fa" filled />
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* ── DIMOB ── */}
            <div className="border-t border-[#141414] pt-6">
                <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
                    <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[#f97316]/10 border border-[#f97316]/20 flex items-center justify-center shrink-0 mt-0.5">
                            <ReceiptText size={15} className="text-[#f97316]" />
                        </div>
                        <div>
                            <h3 className="text-[13px] font-black uppercase tracking-tight text-[#f97316]">
                                DIMOB — Declaração de Informações Imobiliárias
                            </h3>
                            <p className="text-[9px] text-[#444] uppercase tracking-[0.2em] mt-0.5">
                                Obrigação Acessória Anual · Geração de Arquivo PGD
                            </p>
                        </div>
                    </div>
                    <div className="flex items-end gap-3 bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-3">
                        <div className="w-24">
                            <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Ano Calendário</label>
                            <select value={anoDimob} onChange={e => setAnoDimob(e.target.value)}
                                className="w-full bg-[#111] border border-[#222] text-white text-[11px] font-mono px-2 py-2 rounded-lg outline-none">
                                {[2022, 2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                            </select>
                        </div>
                        <MagmaBtn onClick={fetchDimobPreview} disabled={loadingDimob} loading={loadingDimob}
                            icon={FileText} label="Auditar Registros" accent="#f97316" />
                        <MagmaBtn onClick={fetchDimob} disabled={loadingDimob} loading={loadingDimob}
                            icon={Download} label="Baixar PGD DIMOB (.txt)" accent="#f97316" filled />
                    </div>
                </div>

                {dimobPreviewData?.registros && (
                    <div className="flex flex-col gap-4">
                        {['venda', 'locacao'].map(tipo => {
                            const registros = dimobPreviewData.registros.filter(r => r.tipo === tipo);
                            if (!registros.length) return null;
                            const totalPago = registros.reduce((s, r) => s + (r.valor_pago || 0), 0);
                            const totalVenda = registros.reduce((s, r) => s + (r.valor_venda || 0), 0);
                            return (
                                <div key={tipo} className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl overflow-hidden">
                                    <div className="flex items-center justify-between px-5 py-3 border-b border-[#161616] bg-[#0e0e0e]">
                                        <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-4 rounded-full bg-[#f97316]" />
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#f97316]">
                                                {tipo === 'venda' ? 'R03 — Alienação de Imóveis' : 'R02 — Rendimentos de Locações'}
                                            </h4>
                                            <span className="text-[9px] font-mono text-[#444]">{registros.length} registros</span>
                                        </div>
                                        <div className="flex gap-6 text-right">
                                            {tipo === 'venda' && (
                                                <div>
                                                    <div className="text-[8px] text-[#444] uppercase tracking-widest">Venda Total</div>
                                                    <div className="text-[12px] font-black font-mono text-[#666]">{fmt(totalVenda)}</div>
                                                </div>
                                            )}
                                            <div>
                                                <div className="text-[8px] text-[#444] uppercase tracking-widest">Recebido (Caixa)</div>
                                                <div className="text-[12px] font-black font-mono text-white">{fmt(totalPago)}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <table className="w-full text-[11px]">
                                        <thead>
                                            <tr>
                                                <Th>Cliente / CPF·CNPJ</Th>
                                                <Th>Unidade</Th>
                                                {tipo === 'venda' && <Th right>Valor Total Venda</Th>}
                                                <Th right accent="#f97316">Rendimentos Pagos</Th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {registros.map((r, i) => (
                                                <tr key={i} className="border-b border-[#0f0f0f] hover:bg-[#111] transition-colors">
                                                    <td className="px-4 py-2.5 text-[#888]">
                                                        {r.cliente_nome}
                                                        <br /><span className="text-[9px] font-mono text-[#444]">{r.cliente_cpf}</span>
                                                    </td>
                                                    <td className="px-4 py-2.5 font-mono text-[#555]">{r.unidade}</td>
                                                    {tipo === 'venda' && <td className="px-4 py-2.5 font-mono text-right text-[#555]">{fmt(r.valor_venda)}</td>}
                                                    <td className="px-4 py-2.5 font-mono text-right font-black text-[#f97316]">{fmt(r.valor_pago)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};
