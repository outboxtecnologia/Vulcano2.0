import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Layers, RefreshCw, AlertCircle, TrendingUp, ChevronDown, Plus } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const TributosGlobaisView = ({ selectedEmpresa }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [dataIni, setDataIni] = useState(`${new Date().getFullYear()}-01`);
    const [dataFim, setDataFim] = useState('');
    const [fetchTrigger, setFetchTrigger] = useState(0);
    const [expandedRow, setExpandedRow] = useState(null);

    const isFiltered = Boolean(dataIni || dataFim);

    useEffect(() => {
        if (!selectedEmpresa) return;
        setLoading(true);
        setError(null);

        fetch(`${API_BASE}/api/receitas-caixa?empresa_id=${selectedEmpresa}${dataIni ? `&data_ini=${dataIni}` : ''}${dataFim ? `&data_fim=${dataFim}` : ''}`)
            .then(res => {
                if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
                return res.json();
            })
            .then(json => {
                setData(json);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, [selectedEmpresa, fetchTrigger]);

    // Calcular estatísticas tributárias globais (Visão Balanço Patrimonial)
    let totalCaixaAcumulado = 0;
    let totalSocAcumulado = 0;
    if (data?.dashboard_meta) {
        Object.values(data.dashboard_meta).forEach(meta => {
            totalCaixaAcumulado += (meta.tributos_caixa_acumulado || 0);
            totalSocAcumulado += (meta.tributos_soc_acumulado || 0);
        });
    }

    const pieData = [
        { name: 'Carga Regime Caixa', value: totalCaixaAcumulado },
        { name: 'Carga Regime Competência', value: totalSocAcumulado }
    ];

    const COLORS = ['var(--v-accent-4)', 'var(--v-accent-6)'];

    return (
        <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
                        <Layers className="text-[var(--v-accent-4)]" size={32}/> 
                        Tributos Globais (Caixa vs Competência)
                    </h2>
                    <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Apur. Presumido (Pis 0.65%, Cofins 3%, CSLL 1.08%, IRPJ 1.2% + 10%) vs RET (4%)</p>
                </div>
                <div className="flex gap-4 p-3 bg-[var(--v-surface-container)] rounded-sm border border-[var(--v-border)] items-end">
                    <div>
                        <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Competência Inicial</label>
                        <input type="month" value={dataIni} onChange={e => setDataIni(e.target.value)} className="bento-input min-w-[140px]" />
                    </div>
                    <div>
                        <label className="text-[9px] uppercase tracking-widest text-[var(--v-text-muted)] font-black mb-1 block">Competência Final</label>
                        <input type="month" value={dataFim} onChange={e => setDataFim(e.target.value)} className="bento-input min-w-[140px]" />
                    </div>
                    <div className="flex-1 flex justify-end">
                        <button 
                            onClick={() => setFetchTrigger(prev => prev + 1)}
                            className="bg-[var(--v-accent-4)] text-black font-black uppercase tracking-widest text-[10px] px-6 py-2 rounded-sm hover:opacity-80 transition-opacity flex items-center gap-2"
                        >
                            <RefreshCw size={14} /> Atualizar Matriz
                        </button>
                    </div>
                </div>
            </div>


            {loading && (
                <div className="flex-1 flex flex-col items-center justify-center p-12 space-y-4">
                    <RefreshCw className="animate-spin text-[var(--v-accent-4)]" size={48} />
                    <p className="text-[10px] uppercase font-bold tracking-[0.3em] text-[var(--v-text-muted)]">Calculando Matriz Tributária...</p>
                </div>
            )}

            {error && !loading && (
                <div className="bg-[var(--v-error)]/10 text-[var(--v-error)] border border-[var(--v-error)]/30 p-4 rounded-sm flex items-center gap-3">
                    <AlertCircle size={20} /> <span className="text-sm font-bold">{error}</span>
                </div>
            )}

            {!loading && !error && data && (
                <>
                    <div className="grid grid-cols-3 gap-6">
                        <div className="magma-card p-6 flex flex-col justify-center border-l-4 border-l-[var(--v-accent-4)] relative overflow-hidden group">
                            <span className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Base Acum. Faturamento (Soc)</span>
                            <h4 className="text-3xl font-black text-white mt-2 drop-shadow-lg">{formatCurrency(totalSocAcumulado)}</h4>
                        </div>
                        <div className="magma-card p-6 flex flex-col justify-center border-l-4 border-l-[var(--v-accent-5)] relative overflow-hidden group">
                            <span className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Total Acum. p/ Recolher (Caixa)</span>
                            <h4 className="text-3xl font-black text-[var(--v-accent-5)] mt-2 drop-shadow-lg">{formatCurrency(totalCaixaAcumulado)}</h4>
                        </div>
                        <div className="magma-card p-6 flex flex-col justify-center border-l-4 border-l-[var(--v-accent-6)] relative overflow-hidden group">
                            <span className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Saldo Diferimento Fiscal (Provisão)</span>
                            <h4 className="text-3xl font-black text-[var(--v-accent-6)] mt-2 drop-shadow-lg">{formatCurrency(totalSocAcumulado - totalCaixaAcumulado)}</h4>
                            <TrendingUp className="text-[var(--v-accent-6)] absolute -right-5 -bottom-5 opacity-10 group-hover:scale-125 transition-transform" size={100} />
                        </div>
                    </div>

                    <div className="magma-card overflow-hidden border border-[var(--v-border)] rounded-sm">
                        <table className="w-full text-left text-[11px] border-collapse">
                            <thead className="bg-[#111] sticky top-0 border-b border-[var(--v-border)]">
                                <tr>
                                    <th className="p-3 tracking-widest text-[#555] uppercase font-bold">Obras / Empreendimentos</th>
                                    <th className="p-3 tracking-widest text-[#555] uppercase font-bold text-center">Regime</th>
                                    <th className="p-3 tracking-widest text-white/50 uppercase font-bold text-right">PIS/COFINS</th>
                                    <th className="p-3 tracking-widest text-white/50 uppercase font-bold text-right">CSLL + IRPJ Base</th>
                                    <th className="p-3 tracking-widest text-[var(--v-accent-5)] uppercase font-bold text-right">Adicional IR (10%)</th>
                                    <th className="p-3 tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">RET 4%</th>
                                    <th className="p-3 tracking-widest text-[var(--v-accent-2)] uppercase font-black text-right">TRIB. SOC.</th>
                                    <th className="p-3 tracking-widest text-[var(--v-accent-4)] uppercase font-black text-right">TRIB. FISCAL</th>
                                    <th className="p-3 tracking-widest text-[#aaa] uppercase font-black text-center">STATUS (IR|CS)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(data.dashboard_meta || {}).map(([name, meta], idx) => {
                                    const pisCofins = (meta.pis || 0) + (meta.cofins || 0);
                                    const csllIrpj = (meta.csll || 0) + (meta.irpj || 0);
                                    const ret = meta.ret || 0;
                                    const isRet = ret > 0 && pisCofins === 0;
                                    
                                    // Using the accumulated balance to measure Deferred vs Anticipated (Account Status)
                                    const balSoc = meta.tributos_soc_acumulado || 0;
                                    const balFiscal = meta.tributos_caixa_acumulado || 0;
                                    const statusDiff = balSoc - balFiscal;
                                    
                                    const mesSoc = isFiltered ? meta.tributos_soc_mes : balSoc;
                                    const mesFiscal = isFiltered ? meta.tributos_caixa_mes : balFiscal;
                                    
                                    let statusLabel = "-";
                                    let statusColor = "text-[#888]";
                                    if (statusDiff > 10) {
                                        statusLabel = `DIFERIDO PI (${formatCurrency(statusDiff)})`;
                                        statusColor = "text-[var(--v-accent-6)] bg-[var(--v-accent-6)]/10 px-2 py-0.5 rounded";
                                    } else if (statusDiff < -10) {
                                        statusLabel = `ANTECIPADO (${formatCurrency(Math.abs(statusDiff))})`;
                                        statusColor = "text-[var(--v-accent-3)] bg-[var(--v-accent-3)]/10 px-2 py-0.5 rounded";
                                    }
                                    
                                    return (
                                        <React.Fragment key={idx}>
                                            <tr 
                                                onClick={() => setExpandedRow(expandedRow === idx ? null : idx)}
                                                className="border-b border-[#222] hover:bg-[#1a1a1c] transition-colors cursor-pointer"
                                            >
                                                <td className="p-3 font-bold text-[var(--v-text)] max-w-xs truncate flex items-center gap-2">
                                                    {expandedRow === idx ? <ChevronDown size={14} /> : <Plus size={14} />} {name}
                                                </td>
                                                <td className="p-3 text-center">
                                                    {isRet ? <span className="bg-[var(--v-accent-3)]/20 text-[var(--v-accent-3)] px-2 py-0.5 rounded text-[9px] uppercase font-black">RET</span> : <span className="bg-[var(--v-text-muted)]/20 text-[#aaa] px-2 py-0.5 rounded text-[9px] uppercase font-black">PRES</span>}
                                                </td>
                                                <td className="p-3 text-right font-mono text-[#888]">{formatCurrency(pisCofins)}</td>
                                                <td className="p-3 text-right font-mono text-[#888]">{formatCurrency(csllIrpj)}</td>
                                                <td className="p-3 text-right font-mono font-bold text-[var(--v-accent-5)]">{formatCurrency(meta.irpj_adicional)}</td>
                                                <td className="p-3 text-right font-mono font-bold text-[var(--v-accent-3)]">{formatCurrency(ret)}</td>
                                                <td className="p-3">
                                                    <div className="flex flex-col items-end">
                                                        <span className="font-black text-[var(--v-accent-2)]">{formatCurrency(mesSoc)}</span>
                                                        {isFiltered && <span className="text-[9px] text-[var(--v-text-muted)]">Acum: {formatCurrency(balSoc)}</span>}
                                                    </div>
                                                </td>
                                                <td className="p-3">
                                                    <div className="flex flex-col items-end">
                                                        <span className="font-black text-[var(--v-accent-4)]">{formatCurrency(mesFiscal)}</span>
                                                        {isFiltered && <span className="text-[9px] text-[var(--v-text-muted)]">Acum: {formatCurrency(balFiscal)}</span>}
                                                    </div>
                                                </td>
                                                <td className="p-3 text-center font-mono font-bold text-[9px] uppercase">
                                                    <span className={statusColor}>{statusLabel}</span>
                                                </td>
                                            </tr>
                                            {expandedRow === idx && meta.unidades && meta.unidades.length > 0 && (
                                                <tr className="bg-[#111] border-b border-[#333]">
                                                    <td colSpan={9} className="p-4">
                                                        <div className="overflow-x-auto max-h-[300px] custom-scrollbar border border-[#222]">
                                                            <table className="w-full text-left text-[10px]">
                                                                <thead className="bg-[#1a1a1c] sticky top-0">
                                                                    <tr className="text-[#888] uppercase tracking-widest font-bold">
                                                                        <th className="p-2 border-b border-[#222]">Unidade</th>
                                                                        <th className="p-2 border-b border-[#222]">Comprador</th>
                                                                        <th className="p-2 border-b border-[#222] text-right">VGV</th>
                                                                        <th className="p-2 border-b border-[#222] text-right">POC Total</th>
                                                                        <th className="p-2 border-b border-[#222] text-right">Rec. Caixa</th>
                                                                        <th className="p-2 border-b border-[#222] text-right">Trib. Soc. ({isFiltered ? 'Mês' : 'Total'})</th>
                                                                        <th className="p-2 border-b border-[#222] text-right">Trib. Fiscal ({isFiltered ? 'Mês' : 'Total'})</th>
                                                                        <th className="p-2 border-b border-[#222] text-right">Saldo Dif.</th>
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    {meta.unidades.map((u, i) => {
                                                                         const sDiff = u.tributos_soc_acumulado - u.tributos_caixa_acumulado;
                                                                         const cxMes = isFiltered ? u.caixa_mes : u.caixa_acumulado;
                                                                         const tSocMes = isFiltered ? u.soc_mes * (meta.irpj_adicional > 0 ? 0.0593 : 0.04) : u.tributos_soc_acumulado; // Approx unit rate
                                                                         const tFisMes = isFiltered ? u.tributos_caixa_mes : u.tributos_caixa_acumulado;
                                                                         return (
                                                                        <tr key={i} className="border-b border-[#222] hover:bg-[#1f1f22]">
                                                                            <td className="p-2 font-bold">{u.unidade}</td>
                                                                            <td className="p-2 max-w-[200px] truncate">{u.comprador}</td>
                                                                            <td className="p-2 text-right font-mono text-[#aa3333]">{formatCurrency(u.vgv)}</td>
                                                                            <td className="p-2 text-right font-mono text-[#888]">{(meta.poc || 0).toFixed(2)}%</td>
                                                                            <td className="p-2 text-right font-mono text-[var(--v-accent-3)]">{formatCurrency(cxMes)}</td>
                                                                            <td className="p-2 text-right font-mono text-[var(--v-accent-2)]">{formatCurrency(isFiltered ? u.tributos_soc_mes : u.tributos_soc_acumulado)}</td>
                                                                            <td className="p-2 text-right font-mono text-[var(--v-accent-4)]">{formatCurrency(tFisMes)}</td>
                                                                            <td className={`p-2 text-right font-mono font-bold ${sDiff > 0 ? 'text-[var(--v-accent-6)]' : 'text-[#888]'}`}>{formatCurrency(sDiff)}</td>
                                                                        </tr>
                                                                    )})}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </React.Fragment>
                                    );
                                })}
                                {Object.keys(data.dashboard_meta || {}).length === 0 && (
                                    <tr><td colSpan="9" className="p-10 text-center text-[#555] uppercase text-[10px] tracking-widest">Sem base faturada</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    <div className="magma-card overflow-hidden border border-[var(--v-border)] rounded-sm mt-6">
                        <div className="p-4 bg-[var(--v-surface-container)] border-b border-[var(--v-border)]">
                            <h3 className="text-xs uppercase font-black tracking-widest text-[var(--v-accent-6)] flex items-center gap-2"><TrendingUp size={14} /> Demonstrativo das Contabilizações (Período)</h3>
                        </div>
                        <div className="overflow-x-auto custom-scrollbar">
                            <table className="w-full text-left text-[11px] border-collapse">
                                <thead className="bg-[#111] sticky top-0 border-b border-[var(--v-border)]">
                                    <tr>
                                        <th className="p-3 tracking-widest text-[#555] uppercase font-bold">Obras / Empreendimentos</th>
                                        <th className="p-3 tracking-widest text-[#555] uppercase font-bold">Venda/Faturamento (Competência)</th>
                                        <th className="p-3 tracking-widest text-[#555] uppercase font-bold">Recebimento (Caixa)</th>
                                        <th className="p-3 tracking-widest text-[#555] uppercase font-bold">Provisão Diferimento (Ativo)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(data.dashboard_meta || {}).map(([name, meta], idx) => {
                                        const ct = meta.contas_contabeis || {};
                                        // A receita no mes é "receita_soc_mes" ou o acumulado dependendo da view, mas vamos usar "receita_societaria" do diff acumulado caso dataIni e dataFim estejam juntos, o backend traz o do periodo
                                        const fat = meta.receita_soc_mes || meta.receita_societaria || 0;
                                        const cx = meta.caixa_mes || meta.caixa_acumulado || 0;
                                        const dif = fat - cx;

                                        return (
                                            <tr key={idx} className="border-b border-[#222] hover:bg-[#1a1a1c] transition-colors">
                                                <td className="p-3 font-bold text-[var(--v-text)] truncate">{name}</td>
                                                <td className="p-3 text-[#aa3333] font-mono text-[10px]">
                                                    D - {ct.CONTACLI || 'CLIENTES'} <br/>
                                                    C - {ct.CONTAREC || 'RECEITA DE VENDAS DRE'} <br/>
                                                    <span className="font-bold text-white/70">{formatCurrency(fat)}</span>
                                                </td>
                                                <td className="p-3 text-[#33aa33] font-mono text-[10px]">
                                                    D - {ct.CONTACAIXA || 'BANCOS'} <br/>
                                                    C - {ct.CONTACLI || 'CLIENTES'} <br/>
                                                    <span className="font-bold text-white/70">{formatCurrency(cx)}</span>
                                                </td>
                                                <td className="p-3 text-[#aa88aa] font-mono text-[10px]">
                                                    D - PROVISÃO P/ TRIBUTOS SOBRE LUCRO <br/>
                                                    C - TRIBUTOS DIFERIDOS (PASSIVO) <br/>
                                                    <span className="font-bold text-white/70">{formatCurrency(meta.tributos_soc_acumulado - meta.tributos_caixa_acumulado)}</span>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                    {Object.keys(data.dashboard_meta || {}).length === 0 && (
                                        <tr><td colSpan="4" className="p-10 text-center text-[#555] uppercase text-[10px] tracking-widest">Sem contabilizações processadas no período</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>

    );
};
