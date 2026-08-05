import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { FileText, Download, ShieldCheck, AlertCircle, RefreshCw, Code2, CheckCircle2, ReceiptText } from 'lucide-react';
import { API_BASE } from './apiBase';
import { useSearchParamState } from './hooks/useSearchParamState';

const TABS = ['RET', 'F200', 'RESUMO'];

const fmt = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

// ── Tab pill ──────────────────────────────────────────────────────────────────
const Tab = ({ active, onClick, accent, children }) => (
    <button
        onClick={onClick}
        className="relative pb-3 px-1 text-[10px] font-black uppercase tracking-[0.2em] transition-colors"
        style={{ color: active ? accent : 'var(--v-text-ghost)' }}
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
        {/* Rotulo em <span>: texto solto irmao de icone condicional vira no de referencia
            do insertBefore e quebra o commit do React se algo (tradutor de pagina) tiver
            embrulhado o texto. Este botao e compartilhado por toda a tela. */}
        {loading ? <RefreshCw size={11} className="animate-spin" /> : <Icon size={11} />}
        <span>{loading ? 'Aguarde...' : label}</span>
    </button>
);

// ── Cabeçalho de tabela padrão ────────────────────────────────────────────────
const Th = ({ children, right = false, accent }) => (
    <th className={`px-4 py-3 text-[9px] font-black uppercase tracking-[0.2em] border-b border-[var(--v-line)] ${right ? 'text-right' : 'text-left'}`}
        style={{ color: accent || 'var(--v-text-ghost)' }}>
        {children}
    </th>
);

export const FiscalSpedView = ({ selectedEmpresa }) => {
    const [ano, setAno] = useSearchParamState('ano', new Date().getFullYear().toString());
    const [mes, setMes] = useSearchParamState('mes', (new Date().getMonth() + 1).toString().padStart(2, '0'));
    const [retData, setRetData] = useState(null);
    const [resumoData, setResumoData] = useState(null);
    const [f200Data, setF200Data] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // A aba e um segmento da rota (/fiscal/ret, /fiscal/f200, /fiscal/resumo).
    // setActiveTab mantem a assinatura antiga porque tambem e chamado como efeito
    // colateral das apuracoes (fetchRetPreview/fetchF200/fetchResumo), nao so pelos
    // cliques nas abas. Sempre replace: apurar tres vezes nao deve encher o historico,
    // e o Voltar do navegador deve sair da tela, nao passear pelas abas.
    const { tab } = useParams();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const activeTab = TABS.includes(String(tab).toUpperCase()) ? String(tab).toUpperCase() : 'RET';
    const setActiveTab = useCallback((next) => {
        navigate(`/empresa/${selectedEmpresa}/fiscal/${String(next).toLowerCase()}`, { replace: true });
    }, [navigate, selectedEmpresa]);
    const [anoDimob, setAnoDimob] = useState(new Date().getFullYear().toString());
    const [loadingDimob, setLoadingDimob] = useState(false);
    const [dimobPreviewData, setDimobPreviewData] = useState(null);
    const [retCommitting, setRetCommitting] = useState(false);
    const [f200Committing, setF200Committing] = useState(false);
    const [visaoTecnica, setVisaoTecnica] = useState(false);

    // Marca qual combinacao (empresa|ano|mes|aba) ja foi apurada. Sem isto, clicar em
    // "Apurar F200" dispararia a chamada duas vezes: uma pelo botao e outra pelo efeito
    // de deep-link, que reage a troca de aba feita pelo proprio fetch.
    const apuracaoFeita = useRef(null);
    const chaveApuracao = (aba) => `${selectedEmpresa}|${ano}|${mes}|${aba}`;

    const fetchRetPreview = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        apuracaoFeita.current = chaveApuracao('RET');
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
        apuracaoFeita.current = chaveApuracao('F200');
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/f200/preview?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            if (!res.ok) throw new Error("Apuração F200 falhou.");
            setF200Data(await res.json()); setActiveTab('F200');
        } catch (err) { setError(err.message); } finally { setLoading(false); }
    };

    const fetchResumo = async () => {
        if (!selectedEmpresa || !ano || !mes) return;
        apuracaoFeita.current = chaveApuracao('RESUMO');
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/sped/resumo?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`);
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : "Quadro Resumo falhou.");
            setResumoData(d); setActiveTab('RESUMO');
        } catch (err) { setError(err.message); } finally { setLoading(false); }
    };

    // Deep-link: /empresa/959/fiscal/f200?ano=2025&mes=03 ja abre apurado, senao o link
    // levaria a pessoa a uma tela com os filtros certos e nenhum dado.
    //
    // So vale quando a URL traz a competencia de fato. Entrar na tela pelo menu
    // continua abrindo em branco, esperando o clique em Apurar — apuracao nao e
    // consulta, nao deve rodar so porque alguem passou por aqui.
    const veioDeLink = searchParams.has('ano') && searchParams.has('mes');
    useEffect(() => {
        if (!veioDeLink || !selectedEmpresa || !ano || !mes) return;
        if (apuracaoFeita.current === chaveApuracao(activeTab)) return;
        if (activeTab === 'F200') fetchF200();
        else if (activeTab === 'RESUMO') fetchResumo();
        else fetchRetPreview();
    }, [veioDeLink, selectedEmpresa, ano, mes, activeTab]);

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
                <div className="w-8 h-8 rounded-lg bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <ShieldCheck size={16} className="text-[var(--v-accent)]" />
                </div>
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase text-[var(--v-text-bold)]">
                        Painel Fiscal &amp; SPED
                    </h2>
                    <p className="text-[10px] text-[var(--v-text-ghost)] uppercase tracking-[0.25em]">
                        Auditoria e Compliance Tributário
                    </p>
                </div>
            </div>

            {/* ── Barra de filtros ── */}
            <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl p-4 flex flex-wrap gap-3 items-end">
                <div className="w-24">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Ano</label>
                    <select value={ano} onChange={e => setAno(e.target.value)}
                        className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] hover:border-[#333] text-[var(--v-text-bold)] text-[11px] font-mono px-2 py-2 rounded-lg outline-none transition-colors">
                        {[2022, 2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                </div>
                <div className="w-20">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Mês</label>
                    <select value={mes} onChange={e => setMes(e.target.value)}
                        className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] hover:border-[#333] text-[var(--v-text-bold)] text-[11px] font-mono px-2 py-2 rounded-lg outline-none transition-colors">
                        {Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0')).map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                </div>
                <div className="flex gap-2 flex-wrap">
                    <MagmaBtn onClick={fetchRetPreview} disabled={loading} loading={loading && activeTab === 'RET'}
                        icon={ShieldCheck} label="Apurar RET 4%" accent="var(--v-ok)" />
                    <MagmaBtn onClick={fetchF200} disabled={loading} loading={loading && activeTab === 'F200'}
                        icon={FileText} label="Apurar F200 (Presumido)" accent="var(--v-src-questor)" />
                    <MagmaBtn onClick={fetchResumo} disabled={loading} loading={loading && activeTab === 'RESUMO'}
                        icon={FileText} label="Quadro Resumo" accent="#f59e0b" />
                </div>
                <div className="ml-auto text-right hidden sm:block">
                    <div className="text-[9px] text-[var(--v-text-ghost)] uppercase tracking-widest">Competência</div>
                    <div className="text-[13px] font-black font-mono text-[var(--v-text-faint)]">{ano}-{mes}</div>
                </div>
            </div>

            {/* ── Erro ── */}
            {error && (
                <div className="bg-red-950/30 text-red-400 border border-red-900/40 rounded-xl p-4 flex items-center gap-3 text-sm">
                    <AlertCircle size={18} /> <span className="font-bold">{error}</span>
                </div>
            )}

            {/* ── Tabs ── */}
            <div className="flex gap-6 border-b border-[var(--v-line)]">
                <Tab active={activeTab === 'RET'} onClick={() => setActiveTab('RET')} accent="var(--v-ok)">
                    Configuração RET 4%
                </Tab>
                <Tab active={activeTab === 'F200'} onClick={() => setActiveTab('F200')} accent="var(--v-src-questor)">
                    Operações F200 (EFD)
                </Tab>
                <Tab active={activeTab === 'RESUMO'} onClick={() => setActiveTab('RESUMO')} accent="#f59e0b">
                    Quadro Resumo
                </Tab>
            </div>

            {/* ── Conteúdo das tabs ── */}
            <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl overflow-hidden">

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
                                <tr className="bg-[var(--v-deep)]">
                                    <Th>Empreendimento</Th>
                                    <Th right>Recebimentos</Th>
                                    <Th right>Valor Parcela</Th>
                                    <Th right>Valor Variação</Th>
                                    <Th right>Distrato</Th>
                                    <Th right accent="var(--v-src-questor)">Base Cálculo</Th>
                                    <Th right accent="var(--v-src-questor)">Valor PIS</Th>
                                    <Th right accent="var(--v-src-questor)">Valor COFINS</Th>
                                    <Th right accent="var(--v-ok)">Base Cálculo RET</Th>
                                    <Th right accent="var(--v-ok)">Valor RET</Th>
                                </tr>
                            </thead>
                            <tbody>
                                {(resumoData.data || []).map((r, i) => (
                                    <tr key={i} className="border-b border-[var(--v-line)] hover:bg-[var(--v-hover)]">
                                        <td className="px-4 py-2.5 text-[var(--v-text-muted)] font-bold whitespace-nowrap">{r.empreendimento}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-text-bold)]">{fmt(r.recebimentos)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.valor_parcela)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.variacao)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.distrato)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-src-questor)]">{fmt(r.bc_f200)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-src-questor)]">{fmt(r.pis)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-src-questor)]">{fmt(r.cofins)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right text-[var(--v-ok)]">{fmt(r.bc_ret)}</td>
                                        <td className="px-4 py-2.5 font-mono text-right font-black text-[var(--v-ok)]">{fmt(r.valor_ret)}</td>
                                    </tr>
                                ))}
                                {(resumoData.data || []).length === 0 && (
                                    <tr><td colSpan={10} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                        Sem movimento na competência.
                                    </td></tr>
                                )}
                            </tbody>
                            {(resumoData.data || []).length > 0 && (
                                <tfoot>
                                    <tr className="bg-[var(--v-deep)] border-t border-[var(--v-line)] font-mono font-bold">
                                        <td className="px-4 py-3 text-[9px] uppercase tracking-widest text-[var(--v-text-ghost)]">Totais</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-text-bold)]">{fmt(resumoData.totais?.recebimentos)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-text-muted)]">{fmt(resumoData.totais?.valor_parcela)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-text-muted)]">{fmt(resumoData.totais?.variacao)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-text-muted)]">{fmt(resumoData.totais?.distrato)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-src-questor)]">{fmt(resumoData.totais?.bc_f200)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-src-questor)]">{fmt(resumoData.totais?.pis)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-src-questor)]">{fmt(resumoData.totais?.cofins)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-ok)]">{fmt(resumoData.totais?.bc_ret)}</td>
                                        <td className="px-4 py-3 text-right text-[var(--v-ok)]">{fmt(resumoData.totais?.valor_ret)}</td>
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
                                    <tr className="bg-[var(--v-deep)]">
                                        <Th>Obra (RET)</Th>
                                        <Th>Estab</Th>
                                        <Th>Status</Th>
                                        <Th right>Base de Cálculo</Th>
                                        <Th right accent="var(--v-ok)">PIS</Th>
                                        <Th right accent="var(--v-ok)">COFINS</Th>
                                        <Th right accent="var(--v-ok)">CSLL</Th>
                                        <Th right accent="var(--v-ok)">IRPJ</Th>
                                        <Th right accent="var(--v-accent)">Guia RET</Th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {retData.map((r, i) => (
                                        <tr key={i} className="border-b border-[var(--v-line)] hover:bg-[var(--v-hover)] transition-colors">
                                            <td className="px-4 py-3 font-mono font-bold text-[var(--v-text-muted)]">{r.unidade || 'N/A'}<span className="text-[var(--v-text-ghost)]"> · {r.aliqret}%</span></td>
                                            <td className="px-4 py-3 font-mono text-[var(--v-text-muted)]">{r.codigoestab ?? '—'}</td>
                                            <td className="px-4 py-3 font-mono text-[10px]">
                                                <span style={{ color: r.status === 'PRONTO' ? 'var(--v-ok)' : r.status === 'JA_LANCADO' ? 'var(--v-text-muted)' : 'var(--v-accent)' }}>
                                                    {r.status === 'SEM_DE_PARA' ? 'SEM DE-PARA' : r.status === 'JA_LANCADO' ? 'JÁ LANÇADO' : r.status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 font-mono text-right text-[var(--v-text-bold)]">{fmt(r.base_calculo)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[var(--v-text-faint)]">{fmt(r.pis)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[var(--v-text-faint)]">{fmt(r.cofins)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[var(--v-text-faint)]">{fmt(r.csll)}</td>
                                            <td className="px-4 py-3 font-mono text-right text-[var(--v-text-faint)]">{fmt(r.irpj)}</td>
                                            <td className="px-4 py-3 font-mono text-right font-black text-[var(--v-accent)]">{fmt(r.total_ret)}</td>
                                        </tr>
                                    ))}
                                    {retData.length === 0 && (
                                        <tr><td colSpan={9} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                            Sem recebimento de obra optante pelo RET nesta competência — confira mês/ano (há baixas até fev/2026 na base local).
                                        </td></tr>
                                    )}
                                </tbody>
                                {retData.length > 0 && (
                                    <tfoot>
                                        <tr className="bg-[var(--v-deep)] border-t border-[var(--v-line)]">
                                            <td colSpan={8} className="px-4 py-3 text-[9px] uppercase tracking-widest text-[var(--v-text-ghost)] font-bold">Total RET a Recolher</td>
                                            <td className="px-4 py-3 text-right font-black text-[var(--v-accent)]">
                                                {fmt(retData.reduce((s, r) => s + (r.total_ret || 0), 0))}
                                            </td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>
                        {retData.length > 0 && (
                            <div className="border-t border-[var(--v-line)] p-4 flex justify-end">
                                <MagmaBtn onClick={commitRet} disabled={retCommitting} loading={retCommitting}
                                    icon={CheckCircle2} label="Confirmar e Injetar Lote RET no Questor"
                                    accent="var(--v-ok)" filled />
                            </div>
                        )}
                    </div>
                )}

                {/* ── F200 ── */}
                {activeTab === 'F200' && f200Data && (
                    <div>
                        <div className="flex justify-end px-4 py-2 border-b border-[var(--v-line)]">
                            <button onClick={() => setVisaoTecnica(!visaoTecnica)}
                                className="flex items-center gap-1.5 text-[9px] text-[var(--v-src-questor)] uppercase tracking-widest font-bold hover:opacity-70 transition-opacity">
                                <Code2 size={11} />
                                {visaoTecnica ? 'Visão Resumida' : 'Modo Técnico JSON'}
                            </button>
                        </div>
                        <div className="overflow-x-auto">
                            {!visaoTecnica ? (
                                <table className="w-full text-[11px]">
                                    <thead>
                                        <tr className="bg-[var(--v-deep)]">
                                            <Th>Unidade · Obra</Th>
                                            <Th>Cliente</Th>
                                            <Th>Status</Th>
                                            <Th>Data Venda</Th>
                                            <Th right>Total Venda</Th>
                                            <Th right>Rec. Acum.</Th>
                                            <Th right>Valor Parcela</Th>
                                            <Th right>Variação</Th>
                                            <Th right>Recebido no Mês</Th>
                                            <Th right accent="var(--v-src-questor)">PIS</Th>
                                            <Th right accent="var(--v-src-questor)">COFINS</Th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(f200Data.data || []).map((r, i) => (
                                            <tr key={i} className="border-b border-[var(--v-line)] hover:bg-[var(--v-hover)] transition-colors">
                                                <td className="px-4 py-3 font-mono text-[var(--v-text-muted)] max-w-52 truncate whitespace-nowrap">
                                                    #{r.numcadimob ?? '?'} {(r.unidade || '').replace(/\s+/g, ' ')}
                                                    <span className="text-[var(--v-text-ghost)]"> · {r.obra}</span>
                                                </td>
                                                <td className="px-4 py-3 text-[var(--v-text-muted)] max-w-40 truncate whitespace-nowrap">{r.cliente}</td>
                                                <td className="px-4 py-3 font-mono text-[10px]">
                                                    <span style={{ color: (r.status === 'PRONTO' || r.status === 'NOVO_CADASTRO') ? 'var(--v-ok)' : r.status === 'JA_LANCADO' ? 'var(--v-text-muted)' : 'var(--v-accent)' }}>
                                                        {r.status === 'JA_LANCADO' ? 'JÁ LANÇADO' : r.status?.replace(/_/g, ' ')}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 font-mono text-[var(--v-text-muted)] whitespace-nowrap">{r.dtoper ? r.dtoper.split('-').reverse().join('/') : ''}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.vltotvend)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-text-faint)]">{fmt(r.vlrecacum)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.valor_parcela ?? r.vltotrec)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.variacao)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-text-bold)]">{fmt(r.vltotrec)}</td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-src-questor)]">{fmt(r.vlpis)} <span className="text-[var(--v-text-ghost)]">({r.aliqpis}%)</span></td>
                                                <td className="px-4 py-3 font-mono text-right text-[var(--v-src-questor)]">{fmt(r.vlcofins)} <span className="text-[var(--v-text-ghost)]">({r.aliqcofins}%)</span></td>
                                            </tr>
                                        ))}
                                        {(f200Data.data || []).length === 0 && (
                                            <tr><td colSpan={11} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                                Sem recebimentos F200 (fora do RET) para a competência.
                                            </td></tr>
                                        )}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="p-4 flex flex-col gap-3">
                                    {(f200Data.data || []).map((r, i) => (
                                        <div key={i} className="border-l-2 border-[var(--v-src-questor)] pl-4 bg-[var(--v-deep)] rounded-r-lg p-3">
                                            <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-ghost)] font-bold mb-2">EFDUNIDIMOBVENDIDA · #{r.numcadimob} · {r.status}</p>
                                            <pre className="text-[10px] text-[var(--v-src-questor)] font-mono bg-[var(--v-deep)] p-3 rounded-lg border border-[var(--v-line)] overflow-auto">
                                                {JSON.stringify(r, null, 2)}
                                            </pre>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        {(f200Data.data || []).length > 0 && (
                            <div className="border-t border-[var(--v-line)] p-4 flex justify-end">
                                <MagmaBtn onClick={commitF200} disabled={f200Committing} loading={f200Committing}
                                    icon={CheckCircle2} label="Confirmar e Injetar Lote F200 no Questor"
                                    accent="var(--v-src-questor)" filled />
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* ── DIMOB ── */}
            <div className="border-t border-[#141414] pt-6">
                <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
                    <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/20 flex items-center justify-center shrink-0 mt-0.5">
                            <ReceiptText size={15} className="text-[var(--v-accent)]" />
                        </div>
                        <div>
                            <h3 className="text-[13px] font-black uppercase tracking-tight text-[var(--v-accent)]">
                                DIMOB — Declaração de Informações Imobiliárias
                            </h3>
                            <p className="text-[9px] text-[var(--v-text-ghost)] uppercase tracking-[0.2em] mt-0.5">
                                Obrigação Acessória Anual · Geração de Arquivo PGD
                            </p>
                        </div>
                    </div>
                    <div className="flex items-end gap-3 bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl p-3">
                        <div className="w-24">
                            <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Ano Calendário</label>
                            <select value={anoDimob} onChange={e => setAnoDimob(e.target.value)}
                                className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] text-[var(--v-text-bold)] text-[11px] font-mono px-2 py-2 rounded-lg outline-none">
                                {[2022, 2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                            </select>
                        </div>
                        <MagmaBtn onClick={fetchDimobPreview} disabled={loadingDimob} loading={loadingDimob}
                            icon={FileText} label="Auditar Registros" accent="var(--v-accent)" />
                        <MagmaBtn onClick={fetchDimob} disabled={loadingDimob} loading={loadingDimob}
                            icon={Download} label="Baixar PGD DIMOB (.txt)" accent="var(--v-accent)" filled />
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
                                <div key={tipo} className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl overflow-hidden">
                                    <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--v-line)] bg-[var(--v-deep)]">
                                        <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-4 rounded-full bg-[var(--v-accent)]" />
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--v-accent)]">
                                                {tipo === 'venda' ? 'R03 — Alienação de Imóveis' : 'R02 — Rendimentos de Locações'}
                                            </h4>
                                            <span className="text-[9px] font-mono text-[var(--v-text-ghost)]">{registros.length} registros</span>
                                        </div>
                                        <div className="flex gap-6 text-right">
                                            {tipo === 'venda' && (
                                                <div>
                                                    <div className="text-[8px] text-[var(--v-text-ghost)] uppercase tracking-widest">Venda Total</div>
                                                    <div className="text-[12px] font-black font-mono text-[var(--v-text-muted)]">{fmt(totalVenda)}</div>
                                                </div>
                                            )}
                                            <div>
                                                <div className="text-[8px] text-[var(--v-text-ghost)] uppercase tracking-widest">Recebido (Caixa)</div>
                                                <div className="text-[12px] font-black font-mono text-[var(--v-text-bold)]">{fmt(totalPago)}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <table className="w-full text-[11px]">
                                        <thead>
                                            <tr>
                                                <Th>Cliente / CPF·CNPJ</Th>
                                                <Th>Unidade</Th>
                                                {tipo === 'venda' && <Th right>Valor Total Venda</Th>}
                                                <Th right accent="var(--v-accent)">Rendimentos Pagos</Th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {registros.map((r, i) => (
                                                <tr key={i} className="border-b border-[var(--v-line)] hover:bg-[var(--v-hover)] transition-colors">
                                                    <td className="px-4 py-2.5 text-[var(--v-text-muted)]">
                                                        {r.cliente_nome}
                                                        <br /><span className="text-[9px] font-mono text-[var(--v-text-ghost)]">{r.cliente_cpf}</span>
                                                    </td>
                                                    <td className="px-4 py-2.5 font-mono text-[var(--v-text-faint)]">{r.unidade}</td>
                                                    {tipo === 'venda' && <td className="px-4 py-2.5 font-mono text-right text-[var(--v-text-faint)]">{fmt(r.valor_venda)}</td>}
                                                    <td className="px-4 py-2.5 font-mono text-right font-black text-[var(--v-accent)]">{fmt(r.valor_pago)}</td>
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
