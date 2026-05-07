import React, { useState, useEffect } from 'react';
import { Layers, CheckSquare, AlertCircle, RefreshCw, HandCoins, UploadCloud, Plus, Calendar, Building2, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { API_BASE } from './apiBase';

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ --,--';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

const strPad = (n) => String(n).padStart(2, '0');

// Componente de linha expandível do extrato gerencial
const ExtratRow = ({ g, selectedEmp, selectedEmpresa, filterMes, filterAno }) => {
    const [expanded, setExpanded] = useState(false);
    const [loading, setLoading] = useState(false);
    const [lancamentos, setLancamentos] = useState(null);

    const handleExpand = async () => {
        if (expanded) { setExpanded(false); return; }
        if (lancamentos !== null) { setExpanded(true); return; }
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/custos/analitico/${selectedEmp}?mes=${g.mes}&ano=${g.ano}&empresa_id=${selectedEmpresa}`);
            if (!res.ok) throw new Error('Erro ao buscar analítico');
            const json = await res.json();
            setLancamentos(json.lancamentos || []);
        } catch (e) {
            setLancamentos([]);
        } finally {
            setLoading(false);
            setExpanded(true);
        }
    };

    const isMesAtivo = g.ano === parseInt(filterAno) && g.mes === parseInt(filterMes);

    return (
        <>
            <tr
                onClick={handleExpand}
                className={`border-b border-[var(--v-bg)] hover:bg-[var(--v-hover)] cursor-pointer transition-colors ${isMesAtivo ? 'bg-[var(--v-accent-2)]/5' : ''}`}
            >
                <td className="p-3 font-mono text-[#ddd] flex items-center gap-2">
                    {loading ? <Loader2 size={12} className="animate-spin text-[var(--v-accent-2)]" /> :
                        expanded ? <ChevronDown size={12} className="text-[var(--v-accent-2)]" /> :
                            <ChevronRight size={12} className="text-[var(--v-text-faint)]" />}
                    {g.ano} - {strPad(g.mes)}
                    {isMesAtivo && <span className="text-[8px] bg-[var(--v-accent-2)] text-black px-1.5 py-0.5 rounded font-black uppercase ml-1">Competência Ativa</span>}
                </td>
                <td className="p-3 font-bold text-[var(--v-text-bold)] font-mono text-right">{formatCurrency(g.valor)}</td>
            </tr>
            {expanded && lancamentos !== null && (
                <tr className="bg-[#0a0a0a]">
                    <td colSpan={2} className="p-0">
                        <div className="max-h-[300px] overflow-y-auto custom-scrollbar border-l-2 border-[var(--v-accent-2)]/40">
                            <table className="w-full text-left text-[10px]">
                                <thead className="bg-[#060606] sticky top-0">
                                    <tr className="text-[var(--v-text-faint)] uppercase tracking-widest font-bold border-b border-[var(--v-border)]">
                                        <th className="px-3 py-2">Data</th>
                                        <th className="px-3 py-2">Ct. Débito</th>
                                        <th className="px-3 py-2">Ct. Crédito</th>
                                        <th className="px-3 py-2">Histórico</th>
                                        <th className="px-3 py-2 text-right">Valor</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {lancamentos.length === 0 ? (
                                        <tr><td colSpan={5} className="p-4 text-center text-[var(--v-text-faint)] italic">Nenhum lançamento analítico encontrado.</td></tr>
                                    ) : (
                                        lancamentos.map((l, i) => (
                                            <tr key={i} className="border-b border-[#111] hover:bg-[#111] transition-colors">
                                                <td className="px-3 py-1.5 font-mono text-[var(--v-text-muted)]">{l.data}</td>
                                                <td className="px-3 py-1.5 font-mono text-[#aaa]">{l.conta_deb}</td>
                                                <td className="px-3 py-1.5 font-mono text-[#777]">{l.conta_cred}</td>
                                                <td className="px-3 py-1.5 text-[var(--v-text-muted)] max-w-[200px] truncate" title={l.historico}>{l.historico || `Hist. ${l.hist_codigo}`}</td>
                                                <td className={`px-3 py-1.5 text-right font-mono font-bold ${l.valor >= 0 ? 'text-[var(--v-accent-2)]' : 'text-[var(--v-error)]'}`}>
                                                    {formatCurrency(l.valor)}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                                {lancamentos.length > 0 && (
                                    <tfoot className="bg-[#060606] border-t border-[var(--v-border)]">
                                        <tr>
                                            <td colSpan={4} className="px-3 py-2 text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">
                                                {lancamentos.length} lançamentos LCTOGER
                                            </td>
                                            <td className="px-3 py-2 text-right font-black text-[var(--v-accent-2)] font-mono">
                                                {formatCurrency(lancamentos.reduce((s, l) => s + l.valor, 0))}
                                            </td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>
                    </td>
                </tr>
            )}
        </>
    );
};

export const CustosView = ({ selectedEmpresa }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [error, setError] = useState(null);

    // Filters State
    const [selectedEmp, setSelectedEmp] = useState('');
    const [filterMes, setFilterMes] = useState('');
    const [filterAno, setFilterAno] = useState(new Date().getFullYear().toString());

    // Detalhamento State (LCTOGER/LCTOCTB)
    const [detalhamento, setDetalhamento] = useState({ extrato_gerencial: [], extrato_contabil: [] });

    // Modal state para Lançamento
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formMes, setFormMes] = useState('');
    const [formAno, setFormAno] = useState('');
    const [formValor, setFormValor] = useState('');
    const [formHistorico, setFormHistorico] = useState('');
    const [formPoc, setFormPoc] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const [activeEmpData, setActiveEmpData] = useState(null);

    const loadData = async () => {
        if (!selectedEmpresa) return;
        try {
            const response = await fetch(`${API_BASE}/api/empreendimentos/basico?empresa_id=${selectedEmpresa}`);
            if (!response.ok) throw new Error("Falha ao buscar empreendimentos.");
            const json = await response.json();
            setData(json.empreendimentos || []);
        } catch (e) {
            setError(e.message);
        }
    };

    const handlePesquisar = async () => {
        if (!selectedEmp || !filterMes || !filterAno) {
            alert("Selecione o empreendimento, mês e ano para pesquisar.");
            return;
        }
        setLoading(true);
        setError(null);
        setActiveEmpData(null);

        try {
            const response = await fetch(`${API_BASE}/api/custos/dashboard/${selectedEmp}?mes=${filterMes}&ano=${filterAno}&empresa_id=${selectedEmpresa}`);
            if (!response.ok) throw new Error("Erro ao buscar dashboard da obra.");
            const json = await response.json();
            setActiveEmpData(json.empreendimento);

            // Traz o detalhamento também
            const dRes = await fetch(`${API_BASE}/api/custos/detalhamento/${selectedEmp}?empresa_id=${selectedEmpresa}`);
            if (dRes.ok) {
                const dJson = await dRes.json();
                setDetalhamento(dJson);
            }
        } catch (e) {
            setError(e.message);
            setDetalhamento({ extrato_gerencial: [], extrato_contabil: [] });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, [selectedEmpresa]);

    // Auto-calculate suggested POC when Modal opens
    useEffect(() => {
        if (isModalOpen && activeEmpData) {
            const periodStr = `${formAno}-${strPad(formMes)}`;
            const pocMatch = activeEmpData.pocs?.find(p => p.periodo === periodStr);
            if (pocMatch) {
                setFormPoc(pocMatch.percentual);
                if (!formValor && activeEmpData.custo_real_gasto > 0) {
                    const lastCost = (activeEmpData.custos_lancados || []).reduce((acc, curr) => acc + curr.valor, 0);
                    const totalGasto = activeEmpData.custo_real_gasto || 0;
                    const fracaoVendida = activeEmpData.fracao_vendida || 0;
                    const suggestedAccumulated = totalGasto * fracaoVendida;
                    const suggestedMonth = suggestedAccumulated - lastCost;
                    if (suggestedMonth > 0) setFormValor(suggestedMonth.toFixed(2));
                }
            } else {
                setFormPoc('');
            }
        }
    }, [formMes, formAno, isModalOpen, activeEmpData]);

    const handleLcto = async (e) => {
        e.preventDefault();
        if (!formMes || !formAno || !formValor || !formPoc || !formHistorico) {
            alert('Preencha os campos obrigatórios.');
            return;
        }
        setSubmitting(true);
        try {
            const reqData = {
                empresa_id: parseInt(selectedEmpresa),
                empreendimento_id: parseInt(selectedEmp),
                mes: parseInt(formMes),
                ano: parseInt(formAno),
                valor_custo: parseFloat(formValor),
                percentual: parseFloat(formPoc),
                historico: formHistorico
            };
            const response = await fetch(`${API_BASE}/api/custos/lcto`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reqData)
            });
            const json = await response.json();
            if (!response.ok) throw new Error(json.detail || "Erro ao efetivar lançamento contábil");
            alert("Lançamento efetivado! " + formatCurrency(reqData.valor_custo));
            setIsModalOpen(false);
            loadData();
        } catch (e) {
            alert(e.message);
        } finally {
            setSubmitting(false);
        }
    };

    const handleSync = async () => {
        if (!selectedEmp || !filterMes || !filterAno) {
            alert("Preencha obra, mês e ano para sincronizar com o Questor.");
            return;
        }
        setSyncing(true);
        try {
            const response = await fetch(`${API_BASE}/api/custos/sincronizar_totalizadores/${selectedEmp}?mes=${filterMes}&ano=${filterAno}&empresa_id=${selectedEmpresa || 959}`, {
                method: 'POST'
            });
            const json = await response.json();
            if (!response.ok) throw new Error(json.detail || "Erro ao sincronizar Cubo ERP");
            alert("Sucesso! " + json.message);
            await handlePesquisar();
        } catch (e) {
            alert(e.message);
        } finally {
            setSyncing(false);
        }
    };

    const getFilteredTimeline = () => {
        if (!activeEmpData) return [];
        return activeEmpData.timeline || [];
    };

    const timelineElements = getFilteredTimeline();

    return (
        <div className="space-y-6 animate-in fade-in max-w-[1920px] mx-auto w-full h-full flex flex-col pt-4 pb-20">
            <div className="flex justify-between items-end mb-4">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
                        <HandCoins className="text-[var(--v-accent-2)]" size={32}/>
                        Controle de Custos e Lançamentos Contábeis (POC)
                    </h2>
                    <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-12">Integração Empreendimentos Vulcano x Questor LCTO</p>
                </div>
            </div>

            {/* SELETOR TOP NAVIGATION */}
            <div className="magma-card p-4 rounded-[var(--v-radius)] flex items-end gap-6 bg-[var(--v-deep)] border border-[var(--v-border)]">
                <div className="flex-1">
                    <label className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2 flex items-center gap-2">
                        <Building2 size={12}/> Selecione o Empreendimento
                    </label>
                    <select
                        value={selectedEmp}
                        onChange={(e) => setSelectedEmp(e.target.value)}
                        className="w-full bg-[#151515] border border-[var(--v-border)] text-[var(--v-text-bold)] p-3 rounded-[var(--v-radius)] appearance-none focus:outline-none focus:border-[var(--v-accent-2)] pr-10 hover:bg-[var(--v-hover)] transition-colors"
                    >
                        <option value="" disabled>-- SELECIONE UMA OBRA PARA VER O CUSTO --</option>
                        {data.map(emp => (
                            <option key={emp.id} value={emp.id}>{emp.nome}</option>
                        ))}
                    </select>
                </div>

                <div className="w-48">
                    <label className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2 flex items-center gap-2">
                        <Calendar size={12}/> Mês / Ano (Filtro)
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="number"
                            placeholder="Mês"
                            value={filterMes}
                            onChange={(e) => setFilterMes(e.target.value)}
                            className="w-full bg-[#151515] border border-[var(--v-border)] p-3 text-center text-[var(--v-text-bold)] rounded-[var(--v-radius)] outline-none focus:border-[var(--v-accent-2)]"
                        />
                        <input
                            type="number"
                            placeholder="Ano"
                            value={filterAno}
                            onChange={(e) => setFilterAno(e.target.value)}
                            className="w-full bg-[#151515] border border-[var(--v-border)] p-3 text-center text-[var(--v-text-bold)] rounded-[var(--v-radius)] outline-none focus:border-[var(--v-accent-2)]"
                        />
                    </div>
                </div>

                <button
                    onClick={handleSync}
                    disabled={syncing}
                    className="bg-[var(--v-hover)] hover:bg-[#333] text-[var(--v-text-bold)] w-40 py-3 rounded-[var(--v-radius)] text-[10px] font-black uppercase flex items-center justify-center gap-2 transition-all disabled:opacity-50 border border-[var(--v-border)]"
                >
                    {syncing ? <RefreshCw className="animate-spin text-[var(--v-accent-2)]" size={14}/> : <RefreshCw size={14} className="text-[var(--v-text-muted)]"/>}
                    Sync Questor
                </button>

                <button
                    onClick={() => {
                        setFormMes(filterMes || '');
                        setFormAno(filterAno || new Date().getFullYear().toString());
                        setIsModalOpen(true);
                    }}
                    disabled={!selectedEmp || loading}
                    className="bg-[var(--v-accent-2)] hover:bg-[#ff6a00] text-black w-48 py-3 rounded-[var(--v-radius)] text-[10px] font-black uppercase flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_var(--v-accent-2)] disabled:opacity-50 disabled:shadow-none"
                >
                    {loading ? <RefreshCw className="animate-spin" size={14}/> : <Plus size={14}/>}
                    Apropriar Custo
                </button>
            </div>

            {/* PESQUISAR BOTÃO */}
            <button
                onClick={handlePesquisar}
                disabled={loading || !selectedEmp}
                className="w-full py-3 bg-[var(--v-accent-2)]/20 hover:bg-[var(--v-accent-2)]/30 border border-[var(--v-accent-2)]/40 text-[var(--v-accent-2)] font-black uppercase text-[11px] tracking-widest rounded-[var(--v-radius)] flex items-center justify-center gap-2 transition-all disabled:opacity-40"
            >
                {loading ? <><RefreshCw className="animate-spin" size={14}/> Carregando...</> : <><Layers size={14}/> Carregar Dashboard</>}
            </button>

            {error && (
                <div className="bg-[var(--v-error)]/10 border border-[var(--v-error)] p-4 rounded-[var(--v-radius)] flex items-center gap-3 text-[var(--v-error)]">
                    <AlertCircle size={18}/> <span className="text-sm font-bold">{error}</span>
                </div>
            )}

            {/* DASHBOARD (só visível quando empreendimento selecionado) */}
            <div className="flex-1 flex flex-col gap-6 overflow-hidden">
                {!activeEmpData ? (
                    <div className="flex-1 border border-[var(--v-border)] border-dashed rounded-[var(--v-radius)] flex items-center justify-center text-[var(--v-text-faint)] flex-col gap-4">
                        <Layers size={48} className="opacity-20" />
                        <p className="text-[10px] uppercase tracking-widest font-bold">Aguardando Seleção de Empreendimento</p>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2">

                        {/* ALERTA PARAMETRIZAÇÃO */}
                        {(!activeEmpData.conta_custo || !activeEmpData.conta_estoque) && (
                            <div className="bg-[var(--v-error)]/10 border border-[var(--v-error)] p-4 rounded-[var(--v-radius)] flex items-center gap-4 text-[var(--v-error)] mb-2 shadow-[0_0_15px_var(--v-error)]">
                                <AlertCircle size={20} />
                                <div>
                                    <h4 className="font-bold text-sm">Alerta Contábil Crítico</h4>
                                    <p className="text-[10px] uppercase tracking-wider mt-1">Este empreendimento não possui contas parametrizadas no Vulcano. A integração com Questor Falhará.</p>
                                </div>
                            </div>
                        )}

                        {/* STATISTICS */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="magma-card p-4 rounded-[var(--v-radius)] border border-[var(--v-border)]">
                                <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Custo Incorrido Real (Questor)</p>
                                <h4 className="text-xl font-black text-[var(--v-text-bold)]">{formatCurrency(activeEmpData.custo_real_gasto)}</h4>
                            </div>
                            <div className="magma-card p-4 rounded-[var(--v-radius)] border border-[var(--v-border)]">
                                <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Índice Comercial (Vendidas)</p>
                                <h4 className="text-xl font-black text-[var(--v-text-bold)]">{(activeEmpData.fracao_vendida * 100).toFixed(2)}% da Obra</h4>
                            </div>
                            <div className="magma-card p-4 rounded-[var(--v-radius)] border border-[var(--v-border)]">
                                <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Total DRTEE Apropriado</p>
                                <h4 className="text-xl font-black text-[var(--v-accent-2)] drop-shadow-[0_0_10px_var(--v-accent-2)]">
                                    {formatCurrency((activeEmpData.custos_lancados || []).reduce((acc, curr) => acc + curr.valor, 0))}
                                </h4>
                            </div>
                        </div>

                        {/* GRID TABLES */}
                        <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">

                            {/* LEFT COL: MEMÓRIA DE CÁLCULO CPC 47 */}
                            <div className="col-span-12 xl:col-span-6 magma-card flex flex-col border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden min-h-[300px]">
                                <div className="p-4 border-b border-[var(--v-border)] bg-[var(--v-deep)] flex justify-between items-center shrink-0">
                                    <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--v-text-muted)]">
                                        Memória de Cálculo (Apuração CPC 47)
                                    </h3>
                                    <span className="text-[10px] bg-[var(--v-hover)] px-2 py-1 border border-[var(--v-border)] text-[var(--v-text-muted)] font-mono tracking-wider shadow-sm">
                                        COMPETÊNCIA: {filterAno}-{strPad(filterMes)}
                                    </span>
                                </div>
                                <div className="flex-1 p-6 flex flex-col gap-3 font-mono text-[11px]">
                                    <div className="flex justify-between items-center border-b border-[var(--v-border)] pb-2">
                                        <span className="text-[var(--v-text-muted)]">A. Total de Gastos Incorridos (Questor LCTOGER)</span>
                                        <span className="text-[var(--v-text-bold)] font-bold">{formatCurrency(activeEmpData.custo_real_gasto)}</span>
                                    </div>
                                    <div className="flex justify-between items-center border-b border-[var(--v-border)] pb-2">
                                        <span className="text-[var(--v-text-muted)]">B. Índice Comercial (% Área Vendida)</span>
                                        <span className="text-[var(--v-text-bold)] font-bold">
                                            {(activeEmpData.fracao_vendida * 100).toFixed(4)} %
                                            <span className="text-[9px] text-[var(--v-text-faint)] ml-2 font-normal">
                                                ({(activeEmpData.area_vendida || 0).toFixed(2)}m² / {(activeEmpData.area_total || 0).toFixed(2)}m²)
                                            </span>
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center border-b border-[var(--v-border)] pb-2 mt-4">
                                        <span className="text-[var(--v-accent-2)] font-bold">CUSTO TOTAL CALCULADO (A * B)</span>
                                        <span className="text-[var(--v-accent-2)] font-bold">
                                            {formatCurrency(activeEmpData.custo_real_gasto * activeEmpData.fracao_vendida)}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center border-b border-[var(--v-border)] pb-2 text-[var(--v-error)]">
                                        <span className="font-bold">- Custo Acumulado Reconhecido Anteriormente</span>
                                        <span className="font-bold">{formatCurrency((activeEmpData.custo_reconhecido_anterior || 0))}</span>
                                    </div>
                                    <div className="flex justify-between items-center p-4 bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/30 mt-4 rounded-[var(--v-radius)] shadow-[0_0_20px_rgba(255,100,0,0.1)]">
                                        <div className="flex flex-col">
                                            <span className="text-[var(--v-accent)] font-black text-sm uppercase">Lançamento a Efetuar Neste Mês</span>
                                            <span className="text-[9px] text-[var(--v-text-muted)] mt-1 track-widest">
                                                D É B I T O : {activeEmpData.conta_custo || 'S/ Conta'} - {activeEmpData.conta_custo_nome || ''} (Apropriação Imob.)<br/>
                                                C R É D I T O : {activeEmpData.poc_atual >= 100 ? (activeEmpData.conta_estconc || 'S/ Conta') + ' - ' + (activeEmpData.conta_estconc_nome || '') + ' (Estoque Concluído)' : (activeEmpData.conta_estoque || 'S/ Conta') + ' - ' + (activeEmpData.conta_estoque_nome || '') + ' (Estoque em Andamento)'}
                                            </span>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-[var(--v-accent)] font-black text-2xl tracking-tighter drop-shadow-md">
                                                {formatCurrency(Math.max(0, (activeEmpData.custo_real_gasto * activeEmpData.fracao_vendida) - (activeEmpData.custo_reconhecido_anterior || 0)))}
                                            </span>
                                            {timelineElements.some(t => t.periodo === `${filterAno}-${strPad(filterMes)}`) && (
                                                <div className="text-[9px] text-green-400 font-bold flex justify-end gap-1 items-center mt-1"><CheckSquare size={10}/> LCTO JÁ EMITIDO</div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* RIGHT COL: Sub-tabelas Detalhadas */}
                            <div className="col-span-12 xl:col-span-6 flex flex-col gap-6">

                                {/* Extrato Financeiro LCTOGER com Drill-Down */}
                                <div className="magma-card flex-1 flex flex-col border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden min-h-[250px] shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                                    <div className="p-3 border-b border-[var(--v-border)] bg-[var(--v-deep)] flex justify-between items-center shrink-0">
                                        <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#999] flex flex-col">
                                            <span className="text-[var(--v-accent-2)]">Extrato Financeiro Incorrido (LCTOGER)</span>
                                            <span className="text-[8px] text-[var(--v-text-faint)] opacity-80 mt-0.5">Clique em um mês para expandir lançamentos analíticos</span>
                                        </h3>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                                        <table className="w-full text-left text-[11px] whitespace-nowrap">
                                            <thead className="bg-[#0b0b0b] sticky top-0 z-10 shadow-sm">
                                                <tr>
                                                    <th className="p-3 text-[var(--v-text-faint)] tracking-widest font-bold border-b border-[var(--v-border)]">Ano / Mês</th>
                                                    <th className="p-3 text-[var(--v-text-faint)] tracking-widest font-bold border-b border-[var(--v-border)] text-right">Custo Acumulado R$</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {(!detalhamento.extrato_gerencial || detalhamento.extrato_gerencial.length === 0) ? (
                                                    <tr><td colSpan={2} className="p-6 text-center text-[var(--v-text-faint)] text-[10px] italic">Sem histórico de custos. Execute o Sync Questor.</td></tr>
                                                ) : (
                                                    detalhamento.extrato_gerencial.map((g, idx) => (
                                                        <ExtratRow
                                                            key={idx}
                                                            g={g}
                                                            selectedEmp={selectedEmp}
                                                            selectedEmpresa={selectedEmpresa}
                                                            filterMes={filterMes}
                                                            filterAno={filterAno}
                                                        />
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Extrato DRTEE Lançado (LCTOCTB) */}
                                <div className="magma-card flex-1 flex flex-col border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden min-h-[200px] shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                                    <div className="p-3 border-b border-[var(--v-border)] bg-[var(--v-deep)] flex justify-between items-center shrink-0">
                                        <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#999] flex flex-col">
                                            <span className="text-green-500">Apropriações de Custo Emitidas (LCTOCTB)</span>
                                            <span className="text-[8px] text-[var(--v-text-faint)] opacity-80 mt-0.5">Lançamentos efetivados nesta conta baseados no POC</span>
                                        </h3>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                                        <table className="w-full text-left text-[10px] whitespace-nowrap">
                                            <thead className="bg-[#0b0b0b] sticky top-0 z-10 shadow-sm">
                                                <tr>
                                                    <th className="p-2 text-[var(--v-text-faint)] border-b border-[var(--v-border)]">Data Operação</th>
                                                    <th className="p-2 text-[var(--v-text-faint)] border-b border-[var(--v-border)]">Chave Contábil</th>
                                                    <th className="p-2 text-[var(--v-text-faint)] border-b border-[var(--v-border)] text-right">Valor Apropriado</th>
                                                </tr>
                                            </thead>
                                            <tbody className="text-[var(--v-text-muted)]">
                                                {(!detalhamento.extrato_contabil || detalhamento.extrato_contabil.length === 0) ? (
                                                    <tr><td colSpan={3} className="p-6 text-center text-[var(--v-text-faint)] italic">Nenhum lançamento foi exportado para o Questor.</td></tr>
                                                ) : (
                                                    detalhamento.extrato_contabil.map((c, idx) => (
                                                        <tr key={idx} className="border-b border-[var(--v-bg)] hover:bg-[var(--v-hover)]">
                                                            <td className="p-3">{c.data}</td>
                                                            <td className="p-3 text-[9px] opacity-70">#{c.chave}</td>
                                                            <td className="p-3 font-bold text-green-400 text-right">{formatCurrency(c.valor)}</td>
                                                        </tr>
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* MODAL DE LANÇAMENTO */}
            {isModalOpen && activeEmpData && (
                <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-8 animate-in fade-in">
                    <div className="magma-card w-[500px] border border-[var(--v-accent-2)] shadow-[0_0_30px_rgba(255,77,0,0.15)] rounded-[var(--v-radius)] p-8 flex flex-col gap-6 relative">
                        <button onClick={() => setIsModalOpen(false)} className="absolute top-4 right-4 text-[var(--v-text-faint)] hover:text-[#fff] transition-colors p-2 text-[10px] font-bold uppercase tracking-widest bg-[var(--v-deep)] rounded-[var(--v-radius)]">X Fechar</button>
                        <div className="flex flex-col gap-1 pr-6">
                            <h2 className="text-xl font-black uppercase tracking-tighter text-[var(--v-text-bold)]">Criar Lançamento de Custos</h2>
                            <p className="text-[10px] uppercase font-bold text-[var(--v-text-muted)] tracking-widest">{activeEmpData.nome}</p>
                        </div>
                        <div className="p-4 bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] text-[10px] font-mono tracking-widest text-[var(--v-accent-2)] shadow-inner">
                            LCTO Débito: [{activeEmpData.conta_custo || 'N/A'}] Custo Incorrido<br/>
                            LCTO Crédito: [{activeEmpData.conta_estoque || 'N/A'}] Estoque/Obras<br/>
                            Centro de Custo: [{activeEmpData.codigo_cc || 'N/A'}]
                        </div>
                        <form onSubmit={handleLcto} className="flex flex-col gap-5">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2 block">Mês a Apropriar</label>
                                    <input type="number" min="1" max="12" value={formMes} onChange={e => setFormMes(e.target.value)} className="w-full bg-[#0b0b0b] border border-[var(--v-border)] p-3 text-[var(--v-text-bold)] text-center rounded-[var(--v-radius)] outline-none focus:border-[var(--v-accent-2)]" required />
                                </div>
                                <div>
                                    <label className="text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2 block">Ano Contábil</label>
                                    <input type="number" min="2000" max="2100" value={formAno} onChange={e => setFormAno(e.target.value)} className="w-full bg-[#0b0b0b] border border-[var(--v-border)] p-3 text-[var(--v-text-bold)] text-center rounded-[var(--v-radius)] outline-none focus:border-[var(--v-accent-2)]" required />
                                </div>
                            </div>
                            <div className="p-4 border border-[var(--v-accent)]/30 rounded-[var(--v-radius)] bg-[var(--v-accent)]/5">
                                <label className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-2)] mb-2 flex justify-between">Percentual POC Apurado (%)</label>
                                <input type="number" step="0.01" value={formPoc} onChange={e => setFormPoc(e.target.value)} placeholder="0.00" className="w-full bg-transparent border-0 border-b border-[var(--v-accent-2)] text-[var(--v-accent-2)] font-black text-2xl font-mono p-0 outline-none pb-1" required />
                            </div>
                            <div>
                                <label className="text-[9px] font-black uppercase tracking-widest text-[#fff] mb-2 flex justify-between items-center gap-2">
                                    Valor de Custo do Mês (R$) <span className="opacity-50 font-normal normal-case text-[9px] bg-[var(--v-hover)] px-2 py-0.5 rounded-[var(--v-radius)]">Conta Débito Contábil</span>
                                </label>
                                <input type="number" step="0.01" value={formValor} onChange={e => setFormValor(e.target.value)} placeholder="0.00" className="w-full bg-black border border-white p-4 text-[var(--v-text-bold)] text-2xl font-black font-mono rounded-[var(--v-radius)] outline-none focus:border-[var(--v-accent-glow)] shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-colors" required />
                            </div>
                            <div>
                                <label className="text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2 block">Histórico LCTO (Questor)</label>
                                <input type="text" value={formHistorico} onChange={e => setFormHistorico(e.target.value)} placeholder="VALOR REF. CUSTO OBRA..." className="w-full bg-[#0b0b0b] border border-[var(--v-border)] p-3 text-[var(--v-text-muted)] font-bold rounded-[var(--v-radius)] outline-none focus:border-[var(--v-accent-2)] uppercase" required />
                            </div>
                            <button type="submit" disabled={submitting} className="mt-2 bg-[var(--v-accent-2)] hover:bg-[#ff6a00] text-black w-full py-4 text-[12px] font-black tracking-[0.2em] uppercase flex items-center justify-center gap-3 rounded-[var(--v-radius)] shadow-[0_0_20px_var(--v-accent-2)] active:scale-95 transition-all">
                                {submitting ? <RefreshCw className="animate-spin" size={16}/> : <UploadCloud size={16}/>}
                                Gravar no Questor
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
