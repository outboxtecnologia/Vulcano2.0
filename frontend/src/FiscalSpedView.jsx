import React, { useState } from 'react';
import { FileText, Download, ShieldCheck, AlertCircle, RefreshCw, Building2 } from 'lucide-react';

const API_BASE = "http://127.0.0.1:6000";

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const FiscalSpedView = ({ selectedEmpresa }) => {
    const [ano, setAno] = useState(new Date().getFullYear().toString());
    const [mes, setMes] = useState((new Date().getMonth() + 1).toString().padStart(2, '0'));
    const [retData, setRetData] = useState(null);
    const [f200Data, setF200Data] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('RET');

    // DIMOB specific state
    const [anoDimob, setAnoDimob] = useState(new Date().getFullYear().toString());
    const [loadingDimob, setLoadingDimob] = useState(false);
    const [dimobPreviewData, setDimobPreviewData] = useState(null);

    // Commit States
    const [retCommitting, setRetCommitting] = useState(false);
    const [f200Committing, setF200Committing] = useState(false);
    const [visaoTecnica, setVisaoTecnica] = useState(false);

    const fetchRetPreview = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/ret/preview?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            if (!res.ok) throw new Error("Apuracao RET falhou.");
            const data = await res.json();
            setRetData(data);
            setActiveTab('RET');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
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
            a.style.display = 'none';
            a.href = url;
            a.download = `DIMOB_${anoDimob}_EMP_${selectedEmpresa}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert(err.message);
        } finally {
            setLoadingDimob(false);
        }
    };

    const fetchF200 = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/f200/preview?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            if (!res.ok) throw new Error("Apuracao F200 falhou.");
            const data = await res.json();
            setF200Data(data);
            setActiveTab('F200');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const commitF200 = async () => {
        if (!selectedEmpresa || !ano || !mes || !f200Data) return;
        if (!window.confirm(`Tem certeza que deseja cometer (gravar) os lotes F200 da competência ${mes}/${ano} no banco do Questor?`)) return;
        
        setF200Committing(true);
        try {
            const res = await fetch(`${API_BASE}/api/sped/f200/commit?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`, { method: 'POST' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || "Erro ao injetar F200.");
            alert("Sucesso: " + data.message);
            // Re-fetch to see if empty now or just leave it
        } catch (err) {
            alert(err.message);
        } finally {
            setF200Committing(false);
        }
    };

    const commitRet = async () => {
        if (!selectedEmpresa || !ano || !mes || !retData) return;
        if (!window.confirm(`Tem certeza que deseja gravar as guias RET na competência ${mes}/${ano}?`)) return;
        
        setRetCommitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/sped/ret/commit?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`, { method: 'POST' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || "Erro ao injetar RET.");
            alert("Sucesso: " + data.message);
        } catch (err) {
            alert(err.message);
        } finally {
            setRetCommitting(false);
        }
    };

    const fetchDimobPreview = async () => {
        if (!selectedEmpresa || !anoDimob) return;
        setLoadingDimob(true);
        try {
            const res = await fetch(`${API_BASE}/api/dimob/preview?empresa_id=${selectedEmpresa}&ano=${anoDimob}`);
            const data = await res.json();
            if (!data.success) throw new Error(data.message || "Auditoria DIMOB falhou.");
            setDimobPreviewData(data);
        } catch (err) {
            alert(err.message);
        } finally {
            setLoadingDimob(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
                        <ShieldCheck className="text-[var(--v-accent-5)]" size={32}/> 
                        Painel Fiscal & SPED
                    </h2>
                    <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Auditoria e Compliance Tributário</p>
                </div>
            </div>

            <div className="magma-card border border-[var(--v-border)] rounded-sm p-4 shrink-0 flex flex-wrap gap-4 items-end bg-[var(--v-surface-container)]">
                <div className="w-32">
                    <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Ano Competência</label>
                    <select value={ano} onChange={e => setAno(e.target.value)} className="bento-select w-full">
                        {[2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                </div>
                <div className="w-32">
                    <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Mês Competência</label>
                    <select value={mes} onChange={e => setMes(e.target.value)} className="bento-select w-full">
                        {Array.from({length: 12}, (_, i) => String(i + 1).padStart(2, '0')).map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>
                <div className="flex gap-2">
                    <button onClick={fetchRetPreview} disabled={loading} className="bento-button flex items-center gap-2 border-[var(--v-accent-3)] text-[var(--v-accent-3)] hover:bg-[var(--v-accent-3)] hover:text-black">
                        {loading && activeTab === 'RET' ? <RefreshCw size={14} className="animate-spin" /> : <ShieldCheck size={14}/>} Apurar RET 4%
                    </button>
                    <button onClick={fetchF200} disabled={loading} className="bento-button flex items-center gap-2 border-[var(--v-accent-4)] text-[var(--v-accent-4)] hover:bg-[var(--v-accent-4)] hover:text-black">
                        {loading && activeTab === 'F200' ? <RefreshCw size={14} className="animate-spin" /> : <FileText size={14}/>} Apurar F200 (Presumido)
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-[var(--v-error)]/10 text-[var(--v-error)] border border-[var(--v-error)]/30 p-4 rounded-sm flex items-center gap-3">
                    <AlertCircle size={20} /> <span className="text-sm font-bold">{error}</span>
                </div>
            )}

            <div className="flex gap-4 border-b border-[var(--v-border)]">
                <button onClick={() => setActiveTab('RET')} className={`pb-3 px-4 text-xs font-bold uppercase tracking-widest transition-colors ${activeTab === 'RET' ? 'text-[var(--v-accent-3)] border-b-2 border-[var(--v-accent-3)]' : 'text-[var(--v-text-faint)] hover:text-[var(--v-text-muted)]'}`}>Configuração RET 4%</button>
                <button onClick={() => setActiveTab('F200')} className={`pb-3 px-4 text-xs font-bold uppercase tracking-widest transition-colors ${activeTab === 'F200' ? 'text-[var(--v-accent-4)] border-b-2 border-[var(--v-accent-4)]' : 'text-[var(--v-text-faint)] hover:text-[var(--v-text-muted)]'}`}>Operações F200 (EFD)</button>
            </div>

            <div className="flex-1 overflow-auto custom-scrollbar magma-card border border-[var(--v-border)] rounded-sm">
                                {activeTab === 'RET' && retData && (
                    <div className="flex flex-col h-full">
                        <table className="w-full text-left text-xs border-collapse">
                            <thead className="bg-[var(--v-surface-container)] sticky top-0 border-b border-[var(--v-border)]">
                                <tr>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Unidade</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-right">Base de Cálculo (Rec. Caixa)</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">Pis (0,37%)</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">Cofins (1,71%)</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">CSLL (0,66%)</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">IRPJ (1,26%)</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-error)] uppercase font-bold text-right">RET Total (4%)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {retData.map((r, i) => (
                                    <tr key={i} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                                        <td className="p-4 font-mono font-bold text-[var(--v-text)]">{r.unidade || 'N/A'}</td>
                                        <td className="p-4 font-mono text-right text-[var(--v-text-bold)]">{formatCurrency(r.base_calculo)}</td>
                                        <td className="p-4 font-mono text-right text-[var(--v-text-muted)]">{formatCurrency(r.pis)}</td>
                                        <td className="p-4 font-mono text-right text-[var(--v-text-muted)]">{formatCurrency(r.cofins)}</td>
                                        <td className="p-4 font-mono text-right text-[var(--v-text-muted)]">{formatCurrency(r.csll)}</td>
                                        <td className="p-4 font-mono text-right text-[var(--v-text-muted)]">{formatCurrency(r.irpj)}</td>
                                        <td className="p-4 font-mono text-right font-black text-[var(--v-error)]">{formatCurrency(r.total_ret)}</td>
                                    </tr>
                                ))}
                                {retData.length === 0 && <tr><td colSpan="7" className="p-10 text-center text-[#555] opacity-50 uppercase text-[10px] tracking-widest">Sem base de cálculo para o período.</td></tr>}
                            </tbody>
                        </table>
                        
                        {retData.length > 0 && (
                            <div className="bg-[#111] p-4 border-t border-[var(--v-border)] flex justify-end">
                                <button 
                                    onClick={commitRet} 
                                    disabled={retCommitting} 
                                    className="bg-[var(--v-accent-3)] text-black hover:bg-[var(--v-accent-3)]/80 py-2.5 px-6 font-black uppercase text-[10px] tracking-widest rounded-sm transition-colors flex items-center gap-2"
                                >
                                    {retCommitting ? <RefreshCw size={14} className="animate-spin" /> : <ShieldCheck size={14} />} 
                                    {retCommitting ? "Processando..." : "Confirmar e Injetar Lote RET no Questor"}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'F200' && f200Data && (
                    <div className="flex flex-col h-full">
                        <table className="w-full text-left text-xs border-collapse">
                            <thead className="bg-[var(--v-surface-container)] sticky top-0 border-b border-[var(--v-border)]">
                                <tr>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-right" colSpan="5">
                                        <button onClick={() => setVisaoTecnica(!visaoTecnica)} className="hover:text-white transition-colors text-[var(--v-accent-4)]">
                                            {visaoTecnica ? "Voltar para Visão Resumida" : "Modo Dicionário Técnico"}
                                        </button>
                                    </th>
                                </tr>
                                {!visaoTecnica && (
                                <tr>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-t border-[var(--v-border)]">Unidade / Operação</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-center border-t border-[var(--v-border)]">Tabela Destino</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-right border-t border-[var(--v-border)]">Base Rec. Caixa</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-4)] uppercase font-bold text-right border-t border-[var(--v-border)]">PIS Estimado</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-4)] uppercase font-bold text-right border-t border-[var(--v-border)]">COFINS Estimado</th>
                                </tr>
                                )}
                            </thead>
                            <tbody>
                                {!visaoTecnica ? (
                                    (f200Data.data || []).filter(r => r.tabela === 'EFDUNIDIMOBVENDIDA').map((r, i) => (
                                        <tr key={i} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                                            <td className="p-4 font-mono font-bold text-[var(--v-text)] max-w-xs truncate">{r.chaves}</td>
                                            <td className="p-4 font-mono text-center text-[var(--v-text-muted)]">{r.tabela}</td>
                                            <td className="p-4 font-mono text-right text-[var(--v-text-bold)]">{formatCurrency(r.valores?.VLBC || 0)}</td>
                                            <td className="p-4 font-mono text-right text-[var(--v-accent-4)]">{formatCurrency(r.valores?.VLPIS || 0)}</td>
                                            <td className="p-4 font-mono text-right text-[var(--v-accent-4)]">{formatCurrency(r.valores?.VLCOFINS || 0)}</td>
                                        </tr>
                                    ))
                                ) : (
                                    (f200Data.data || []).filter(r => r.tabela === 'EFDUNIDIMOBVENDIDA').map((r, i) => (
                                        <tr key={i} className="border-b border-[#222]">
                                            <td colSpan="5" className="p-4 bg-[#0a0a0c] border-l-2 border-[var(--v-accent-4)]">
                                                <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] mb-2 font-bold">{r.tabela} | {r.chaves}</p>
                                                <pre className="text-[10px] text-[var(--v-accent-4)] font-mono bg-black p-4 rounded-sm border border-[#222] overflow-auto">
                                                    {JSON.stringify(r.valores, null, 2)}
                                                </pre>
                                            </td>
                                        </tr>
                                    ))
                                )}
                                {(f200Data.data || []).length === 0 && <tr><td colSpan="5" className="p-10 text-center text-[#555] opacity-50 uppercase text-[10px] tracking-widest">Sem alienações F200 para a competência.</td></tr>}
                            </tbody>
                        </table>

                        {(f200Data.data || []).length > 0 && (
                            <div className="bg-[#111] p-4 border-t border-[var(--v-border)] flex justify-end">
                                <button 
                                    onClick={commitF200} 
                                    disabled={f200Committing} 
                                    className="bg-[var(--v-accent-4)] text-black hover:bg-[var(--v-accent-4)]/80 py-2.5 px-6 font-black uppercase text-[10px] tracking-widest rounded-sm transition-colors flex items-center gap-2"
                                >
                                    {f200Committing ? <RefreshCw size={14} className="animate-spin" /> : <ShieldCheck size={14} />} 
                                    {f200Committing ? "Injetando..." : "Confirmar e Injetar Lote F200 no Questor"}
                                </button>
                            </div>
                        )}
                    </div>
                )}
                
                {!retData && !f200Data && !loading && (
                    <div className="h-full flex items-center justify-center p-20 opacity-30">
                        <ShieldCheck size={80} className="text-[var(--v-text-faint)]" />
                    </div>
                )}
            </div>

            {/* Separated DIMOB Section (Annual) */}
            <div className="mt-8 border-t border-[var(--v-border)] pt-8">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                    <div>
                        <h3 className="text-xl font-black tracking-tighter uppercase text-[var(--v-accent-5)] flex items-center gap-2">
                            <FileText size={24} /> Declaração de Informações sobre Atividades Imobiliárias (DIMOB)
                        </h3>
                        <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-widest mt-1">
                            Obrigação Acessória Anual - Geração de Arquivo PGD
                        </p>
                    </div>
                    <div className="flex bg-[var(--v-surface-container)] p-3 border border-[var(--v-border)] rounded-sm gap-4 items-end shadow-lg">
                        <div className="w-32">
                            <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Ano Calendário</label>
                            <select value={anoDimob} onChange={e => setAnoDimob(e.target.value)} className="bento-select w-full bg-[#111] text-white">
                                {[2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                            </select>
                        </div>
                        <button 
                            onClick={fetchDimobPreview} 
                            disabled={loadingDimob} 
                            className="bento-button border-[var(--v-accent-5)] text-[var(--v-accent-5)] hover:bg-[var(--v-accent-5)] hover:text-black py-2.5 px-6 font-black uppercase text-[10px] tracking-widest flex items-center gap-2"
                        >
                            {loadingDimob ? <RefreshCw size={14} className="animate-spin" /> : <FileText size={14} />} 
                            {loadingDimob ? "Buscando..." : "Auditar Registros"}
                        </button>
                        <button 
                            onClick={fetchDimob} 
                            disabled={loadingDimob} 
                            className="bg-[var(--v-accent-5)] text-black hover:bg-[var(--v-accent-5)]/80 py-2.5 px-6 font-black uppercase text-[10px] tracking-widest rounded-sm transition-colors flex items-center gap-2"
                        >
                            {loadingDimob ? <RefreshCw size={14} className="animate-spin" /> : <Download size={14} />} 
                            {loadingDimob ? "Gerando..." : "Baixar PGD DIMOB (.txt)"}
                        </button>
                    </div>
                </div>

                {dimobPreviewData && dimobPreviewData.registros && (
                    <div className="mt-4 flex flex-col gap-4">
                        {['venda', 'locacao'].map(tipo => {
                            const registros = dimobPreviewData.registros.filter(r => r.tipo === tipo);
                            if (registros.length === 0) return null;
                            
                            return (
                                <div key={tipo} className="magna-card border border-[var(--v-border)] rounded-sm overflow-auto custom-scrollbar bg-[var(--v-surface-container)]">
                                    <div className="p-4 bg-[#111] border-b border-[var(--v-border)] flex justify-between items-center text-xs">
                                        <div>
                                            <h3 className="text-[10px] text-[var(--v-accent-5)] tracking-widest font-black uppercase mb-1">
                                                {tipo === 'venda' ? 'R03 - Alienação de Imóveis (Vendas da Incoporação)' : 'R02 - Rendimentos de Locações (Aluguéis)'}
                                            </h3>
                                            <p className="font-mono text-[var(--v-text-muted)] text-[10px]">Mostrando {registros.length} registros computados.</p>
                                        </div>
                                        <div className="text-right flex gap-6">
                                            {tipo === 'venda' && (
                                                <div className="text-right">
                                                    <p className="font-mono text-[10px] text-[var(--v-text-faint)]">Vendido em {anoDimob}</p>
                                                    <p className="font-mono text-lg text-[var(--v-text-muted)]">{formatCurrency(registros.reduce((acc, curr) => acc + (curr.valor_venda || 0), 0))}</p>
                                                </div>
                                            )}
                                            <div className="text-right">
                                                <p className="font-mono text-[10px] text-[var(--v-text-faint)]">Total Recebido (Caixa)</p>
                                                <p className="font-mono text-lg text-[var(--v-text-bold)]">{formatCurrency(registros.reduce((acc, curr) => acc + (curr.valor_pago || 0), 0))}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <table className="w-full text-left text-xs border-collapse">
                                        <thead className="bg-[#111] sticky top-0 border-b border-[var(--v-border)]">
                                            <tr>
                                                <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold">Cliente / CPF/CNPJ</th>
                                                <th className="p-3 text-[10px] tracking-widest text-[#555] uppercase font-bold">Unidade / Num</th>
                                                {tipo === 'venda' && <th className="p-3 text-[10px] tracking-widest text-[#777] uppercase font-bold text-right">Valor Total da Venda</th>}
                                                <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent-5)] uppercase font-bold text-right">Rendimentos Pagos</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {registros.map((r, i) => (
                                                <tr key={i} className="border-b border-[#222] hover:bg-[#1a1a1c] transition-colors">
                                                    <td className="p-3 font-mono text-[#ddd]">{r.cliente_nome}<br/><span className="text-[#888] text-[10px]">{r.cliente_cpf}</span></td>
                                                    <td className="p-3 font-mono text-[#aaa]">{r.unidade}</td>
                                                    {tipo === 'venda' && <td className="p-3 font-mono text-right text-[var(--v-text-muted)]">{formatCurrency(r.valor_venda)}</td>}
                                                    <td className="p-3 font-mono text-right text-[var(--v-accent-5)] font-bold">{formatCurrency(r.valor_pago)}</td>
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
