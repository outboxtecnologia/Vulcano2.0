import React, { useState, useEffect } from 'react';
import { Construction, RefreshCw, Layers, AlertCircle, Search, Filter, CheckSquare, Square, Building2, Calendar, ChevronDown, ChevronRight, Save } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { API_BASE } from './apiBase';

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const EvolucaoPOCView = ({ selectedEmpresa }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Filters state
    const [empreendimentos, setEmpreendimentos] = useState([]);
    const [selectedEmps, setSelectedEmps] = useState([]);
    const [dataIni, setDataIni] = useState('');
    const [dataFim, setDataFim] = useState('');
    const [loadingEmps, setLoadingEmps] = useState(false);
    const [hasQueried, setHasQueried] = useState(false);
    
    // Drill-down State
    const [expandedEmp, setExpandedEmp] = useState(null);
    const [pocFormPeriod, setPocFormPeriod] = useState('');
    const [pocFormPercent, setPocFormPercent] = useState('');
    const [savingPoc, setSavingPoc] = useState(false);

    // Fetch Empreendimentos when selectedEmpresa changes
    useEffect(() => {
        if (!selectedEmpresa) return;
        setLoadingEmps(true);
        // Reset query state on enterprise switch
        setData(null);
        setHasQueried(false);
        setSelectedEmps([]);
        setExpandedEmp(null);
        
        fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
            .then(res => res.json())
            .then(json => {
                setEmpreendimentos(json || []);
                setLoadingEmps(false);
            })
            .catch(() => {
                setLoadingEmps(false);
            });
    }, [selectedEmpresa]);

    const handleSearch = () => {
        if (!selectedEmpresa) return;
        
        setLoading(true);
        setError(null);
        setHasQueried(true);
        setExpandedEmp(null);

        const qs = new URLSearchParams();
        qs.set('empresa_id', selectedEmpresa);
        if (dataIni) qs.set('data_ini', dataIni);
        if (dataFim) qs.set('data_fim', dataFim);
        if (selectedEmps.length > 0) {
            qs.set('empreendimentos_ids', selectedEmps.join(','));
        }

        fetch(`${API_BASE}/api/receitas-caixa?${qs.toString()}`)
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
    };

    const toggleAllEmps = () => {
        if (selectedEmps.length === empreendimentos.length) {
            setSelectedEmps([]);
        } else {
            setSelectedEmps(empreendimentos.map(e => e.id));
        }
    };
    
    const handleSaveManualPoc = async (empName) => {
        if (!pocFormPeriod || !pocFormPercent) {
            alert("Preencha o mês/ano e o percentual!");
            return;
        }
        
        setSavingPoc(true);
        try {
            const res = await fetch(`${API_BASE}/api/poc`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    empreendimento: empName,
                    periodo: pocFormPeriod,
                    percentual: parseFloat(pocFormPercent)
                })
            });
            if (!res.ok) throw new Error("Falha ao salvar no banco");
            
            // Re-fetch to see visual changes
            handleSearch();
            alert("POC registrado com sucesso!");
            setPocFormPeriod('');
            setPocFormPercent('');
        } catch (e) {
            alert("Aviso: " + e.message);
        } finally {
            setSavingPoc(false);
        }
    };

    // Calcular Chart de Progressão Global usando Histórico Verdadeiro
    const pocChartData = [];
    if (data?.dashboard_meta) {
        const uniquePeriods = new Set();
        const empTimelines = [];
        
        // Extract all timelines
        Object.values(data.dashboard_meta).forEach(meta => {
            if (meta.historico_poc) {
                meta.historico_poc.forEach(h => uniquePeriods.add(h.periodo));
                empTimelines.push(meta.historico_poc);
            }
        });
        
        const sortedPeriods = Array.from(uniquePeriods).sort();
        
        sortedPeriods.forEach(period => {
            let totalPoc = 0;
            let activeCount = empTimelines.length;
            
            empTimelines.forEach(timeline => {
                // Find highest POC at or before this period for this project
                let bestPoc = 0;
                for (let h of timeline) {
                    if (h.periodo <= period) bestPoc = h.poc;
                }
                totalPoc += bestPoc;
            });
            
            const avgPoc = activeCount > 0 ? (totalPoc / activeCount) : 0;
            pocChartData.push({ period, poc_esperado: parseFloat(avgPoc.toFixed(2)) });
        });
    }

    return (
        <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
                        <Construction className="text-[var(--v-accent-3)]" size={32}/> 
                        Evolução POC 
                    </h2>
                    <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Percentage of Completion</p>
                </div>
            </div>

            {/* Top Filter Block */}
            <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] p-4 space-y-4 shadow-xl">
                <div className="flex flex-col md:flex-row gap-6">
                    {/* Empreendimentos Selector - Ampliado */}
                    <div className="flex-1 space-y-2">
                        <div className="flex justify-between items-center text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)]">
                            <span className="flex items-center gap-1"><Building2 size={12}/> Obras Analisadas</span>
                            <button onClick={toggleAllEmps} className="text-[var(--v-accent-4)] hover:text-[#fff] transition-colors">{selectedEmps.length === empreendimentos.length && empreendimentos.length > 0 ? "Desmarcar Todos" : "Marcar Todos"}</button>
                        </div>
                        {/* Altura aumentada para melhor visualização: max-h-[300px] */}
                        <div className="bg-[var(--v-scrim)] border border-[var(--v-border)] rounded-[var(--v-radius)] max-h-[300px] overflow-y-auto custom-scrollbar p-2 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                            {loadingEmps ? (
                                <div className="text-center p-2 text-xs text-[var(--v-text-faint)] uppercase col-span-full">Carregando Obras...</div>
                            ) : empreendimentos.length === 0 ? (
                                <div className="text-center p-2 text-xs text-[var(--v-text-faint)] uppercase col-span-full">Nenhuma Obra Ativa</div>
                            ) : empreendimentos.map(emp => (
                                <label 
                                    key={emp.id} 
                                    onClick={(e) => {
                                        e.preventDefault();
                                        setSelectedEmps(prev => prev.includes(emp.id) ? prev.filter(x => x !== emp.id) : [...prev, emp.id]);
                                    }}
                                    className={`flex items-start gap-2 p-1.5 rounded-[var(--v-radius)] cursor-pointer border transition-colors select-none ${selectedEmps.includes(emp.id) ? 'border-[var(--v-info)]/30 bg-[var(--v-info)]/5 text-[var(--v-text-bold)]' : 'border-transparent text-[var(--v-text-muted)] hover:bg-[var(--v-hover)]'}`}
                                >
                                    <div className="mt-0.5 text-[var(--v-accent-4)]">
                                        {selectedEmps.includes(emp.id) ? <CheckSquare size={14}/> : <Square size={14} className="opacity-50"/>}
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-[10px] font-bold uppercase leading-tight">{emp.nome}</span>
                                        <span className="text-[8px] tracking-widest text-[var(--v-text-faint)]">ID: {emp.id}</span>
                                    </div>
                                </label>
                            ))}

                        </div>
                    </div>

                    {/* Date Filters & Action */}
                    <div className="w-full md:w-[320px] flex flex-col gap-4">
                        <div className="flex gap-3">
                            <div className="flex-1 space-y-1">
                                <label className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)] flex items-center gap-1"><Calendar size={12}/> Dt. Inicio</label>
                                <input type="month" value={dataIni} onChange={(e) => setDataIni(e.target.value)} className="w-full bg-[var(--v-scrim)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#007aff] rounded-[var(--v-radius)] [color-scheme:dark]" />
                            </div>
                            <div className="flex-1 space-y-1">
                                <label className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)] flex items-center gap-1"><Calendar size={12}/> Dt. Fim</label>
                                <input type="month" value={dataFim} onChange={(e) => setDataFim(e.target.value)} className="w-full bg-[var(--v-scrim)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#007aff] rounded-[var(--v-radius)] [color-scheme:dark]" />
                            </div>
                        </div>
                        <button 
                            onClick={handleSearch}
                            disabled={loading || selectedEmps.length === 0}
                            className="bg-[var(--v-info)] hover:bg-[var(--v-info)] text-[var(--v-text-bold)] py-3 rounded-[var(--v-radius)] font-black text-[10px] uppercase tracking-[0.2em] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 mt-auto shadow-[0_0_15px_rgba(0,122,255,0.4)]"
                        >
                            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Layers size={14} />}
                            {loading ? "Calculando VGV/POC..." : "Processar Evolução POC"}
                        </button>
                    </div>
                </div>
            </div>

            {/* Empty State */}
            {!hasQueried && !loading && (
                <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-[var(--v-border)] rounded-[var(--v-radius)] opacity-50 space-y-3 mt-4">
                    <Filter size={40} className="text-[var(--v-text-faint)]" />
                    <p className="text-[10px] uppercase tracking-widest font-black text-[var(--v-text-muted)]">Defina os parâmetros acima e inicie o processamento</p>
                </div>
            )}

            {error && !loading && (
                <div className="bg-[rgb(var(--v-accent-rgb)_/_0.1)] text-[var(--v-accent)] border border-[var(--v-accent)]/30 p-4 rounded-[var(--v-radius)] flex items-center gap-3">
                    <AlertCircle size={20} /> <span className="text-sm font-bold">{error}</span>
                </div>
            )}

            {/* Results Block */}
            {!loading && !error && data && hasQueried && (
                <div className="space-y-6 slide-in-from-bottom-4 animate-in duration-500">
                    <div className="magma-card p-6 h-[400px] flex flex-col relative overflow-hidden bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)]">
                        <div className="flex justify-between items-center mb-6 z-10">
                            <h3 className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)]">Curva do Portfólio Analisado</h3>
                            <div className="flex gap-4">
                                <div className="text-right">
                                    <p className="text-[9px] text-[var(--v-text-muted)] font-black uppercase tracking-widest">Total Acumulado</p>
                                    <p className="text-xs text-[var(--v-accent-3)] font-mono">{formatCurrency(data.totais_gerais?.receita_societaria || 0)}</p>
                                </div>
                            </div>
                        </div>
                        <ResponsiveContainer width="100%" height="100%" className="z-10">
                            <AreaChart data={pocChartData}>
                                <defs>
                                    <linearGradient id="colorPoc" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--v-accent-3)" stopOpacity={0.4}/>
                                        <stop offset="95%" stopColor="var(--v-accent-3)" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                                <XAxis dataKey="period" stroke="var(--v-text-ghost)" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="var(--v-text-ghost)" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                <Tooltip contentStyle={{ backgroundColor: '#131313', border: '1px solid var(--v-text-ghost)' }} />
                                <Area type="monotone" dataKey="poc_esperado" stroke="var(--v-accent-3)" strokeWidth={3} fillOpacity={1} fill="url(#colorPoc)" />
                            </AreaChart>
                        </ResponsiveContainer>
                        <Construction size={200} className="absolute -bottom-10 -right-10 text-[var(--v-accent-3)] opacity-5" />
                    </div>

                    <div className="magma-card overflow-hidden border border-[var(--v-border)] rounded-[var(--v-radius)] bg-[var(--v-deep)]">
                        <table className="w-full text-left text-xs border-collapse">
                            <thead className="bg-[var(--v-deep)] sticky top-0 border-b border-[var(--v-border)]">
                                <tr>
                                    <th className="p-4 w-8"></th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Empreendimento</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-right">VGV Base</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-4)] uppercase font-bold text-center">Evolutivo Histórico (Último POC)</th>
                                    <th className="p-4 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">Acumulado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(data.dashboard_meta || {}).map(([name, meta], idx) => (
                                    <React.Fragment key={idx}>
                                        <tr 
                                            onClick={() => setExpandedEmp(expandedEmp === name ? null : name)}
                                            className={`border-b border-[var(--v-border)] cursor-pointer transition-colors ${expandedEmp === name ? 'bg-[var(--v-hover)] border-l-4 border-l-[#007aff]' : 'hover:bg-[#151518] border-l-4 border-l-transparent'}`}
                                        >
                                            <td className="p-4 text-[var(--v-text-faint)]">
                                                {expandedEmp === name ? <ChevronDown size={14} className="text-[var(--v-accent-4)]"/> : <ChevronRight size={14}/>}
                                            </td>
                                            <td className="p-4 font-black text-[var(--v-text-bold)] uppercase text-[10px] tracking-wider">{name}</td>
                                            <td className="p-4 text-right font-mono text-[var(--v-text-muted)]">{formatCurrency(meta.vgv)}</td>
                                            <td className="p-4 text-center font-mono font-black text-[var(--v-accent-4)] bg-[var(--v-info)]/5">{(meta.poc || 0).toFixed(2)}%</td>
                                            <td className="p-4 text-right font-mono text-[var(--v-accent-3)] font-bold">{formatCurrency(meta.receita_societaria)}</td>
                                        </tr>
                                        {/* Painel Interno (Drill-Down / Formulário POC) */}
                                        {expandedEmp === name && (
                                            <tr className="bg-[#0f0f10] border-b border-[var(--v-border)]">
                                                <td colSpan="5" className="p-0">
                                                    <div className="p-6 border-l-4 border-[var(--v-info)] flex gap-8 animate-in slide-in-from-top-2 duration-300">
                                                        
                                                        {/* Painel: Lançamento Manual / Adição POC */}
                                                        <div className="w-[300px] border border-[var(--v-border)] bg-[#141416] p-4 rounded-[var(--v-radius)] space-y-4 shadow-inner">
                                                            <div>
                                                                <h4 className="text-[10px] font-black text-[var(--v-text-bold)] uppercase tracking-widest mb-1 flex items-center gap-1.5"><Layers size={12}/> Oficializar POC Mensal</h4>
                                                                <p className="text-[9px] text-[var(--v-text-faint)] uppercase">Composição de Diário / Lançamento Base Firebird e SQLite</p>
                                                            </div>
                                                            <div className="space-y-3">
                                                                <div className="space-y-1.5">
                                                                    <label className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)]">Mês Competência</label>
                                                                    <input 
                                                                        type="month" 
                                                                        value={pocFormPeriod} 
                                                                        onChange={(e) => setPocFormPeriod(e.target.value)} 
                                                                        className="w-full bg-[var(--v-deep)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#007aff] rounded-[var(--v-radius)] [color-scheme:dark]" 
                                                                    />
                                                                </div>
                                                                <div className="space-y-1.5">
                                                                    <label className="text-[10px] uppercase font-black tracking-widest text-[var(--v-text-muted)]">Medição Física (%)</label>
                                                                    <div className="relative group">
                                                                        <input 
                                                                            type="number" 
                                                                            step="0.01"
                                                                            placeholder="Ex: 5.45"
                                                                            value={pocFormPercent} 
                                                                            onChange={(e) => setPocFormPercent(e.target.value)} 
                                                                            className="w-full bg-[var(--v-deep)] border border-[var(--v-border)] p-2 text-xs text-[var(--v-text-bold)] outline-none focus:border-[#007aff] rounded-[var(--v-radius)] pr-6" 
                                                                        />
                                                                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--v-text-faint)] font-black text-[10px] group-focus-within:text-[var(--v-accent-4)]">%</span>
                                                                    </div>
                                                                </div>
                                                                <button 
                                                                    onClick={() => handleSaveManualPoc(name)}
                                                                    disabled={savingPoc}
                                                                    className="w-full bg-[var(--v-ok)] hover:bg-[#28a745] text-[var(--v-text-inv)] font-black text-[10px] uppercase tracking-widest py-2.5 flex justify-center items-center gap-2 rounded-[var(--v-radius)] transition-colors disabled:opacity-50 mt-2"
                                                                >
                                                                  {savingPoc ? <RefreshCw size={12} className="animate-spin" /> : <Save size={12} />}
                                                                  GRAVAR SISTEMA
                                                                </button>
                                                            </div>
                                                        </div>

                                                        {/* Painel: Extrato/Espelho Base */}
                                                        <div className="flex-1 space-y-4">
                                                             <h4 className="text-[10px] font-black text-[var(--v-text-faint)] uppercase tracking-[0.2em] border-b border-[var(--v-border)] pb-2">Espelho de Receitas e Impostos</h4>
                                                             <div className="grid grid-cols-3 gap-4 mb-4">
                                                                 <div className="bg-[var(--v-deep)] p-3 rounded-[var(--v-radius)] border border-[var(--v-border)]">
                                                                     <p className="text-[8px] uppercase tracking-widest text-[var(--v-text-faint)] font-black mb-1">Recebimentos (Caixa Real)</p>
                                                                     <p className="text-[var(--v-text-bold)] font-mono text-sm">{formatCurrency(meta.caixa_acumulado)}</p>
                                                                 </div>
                                                                 <div className="bg-[var(--v-deep)] p-3 rounded-[var(--v-radius)] border border-[var(--v-border)]">
                                                                     <p className="text-[8px] uppercase tracking-widest text-[var(--v-text-faint)] font-black mb-1">Tributação Sobre Recebimentos</p>
                                                                     <p className="text-[var(--v-accent)] font-mono text-sm">{formatCurrency(meta.tributos_caixa_acumulado)}</p>
                                                                 </div>
                                                                 <div className="bg-[var(--v-deep)] p-3 rounded-[var(--v-radius)] border border-[rgb(var(--v-accent-3-rgb)_/_0.3)]">
                                                                     <p className="text-[8px] uppercase tracking-widest text-[var(--v-accent-3)] font-black mb-1">Provisão de Tributos (POC)</p>
                                                                     <p className="text-[var(--v-accent-3)] font-mono text-sm">{formatCurrency(meta.tributos_soc_acumulado)}</p>
                                                                 </div>
                                                             </div>

                                                             <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] p-3">
                                                                 <h4 className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-black mb-2">Evolução Mensal Reportada</h4>
                                                                 <div className="max-h-[140px] overflow-y-auto custom-scrollbar">
                                                                     <table className="w-full text-left text-[10px]">
                                                                        <thead className="bg-[var(--v-deep)] sticky top-0 border-b border-[var(--v-border)]">
                                                                            <tr>
                                                                                <th className="p-2 text-[var(--v-text-faint)] font-bold">Período (Mês)</th>
                                                                                <th className="p-2 text-right text-[var(--v-accent-3)] font-bold">Medição (POC)</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody>
                                                                            {meta.historico_poc?.length > 0 ? [...meta.historico_poc].sort((a, b) => b.periodo.localeCompare(a.periodo)).map((h, i) => (
                                                                                <tr key={i} className="border-b border-[rgb(var(--v-border-rgb)_/_0.5)] hover:bg-[var(--v-hover)] transition-colors">
                                                                                    <td className="p-2 text-[var(--v-text-bold)] font-mono">{h.periodo}</td>
                                                                                    <td className="p-2 text-right font-mono text-[var(--v-accent-3)] font-black">{h.poc.toFixed(2)}%</td>
                                                                                </tr>
                                                                            )) : (
                                                                                <tr><td colSpan="2" className="p-4 text-center text-[var(--v-text-faint)]">Nenhum histórico registrado</td></tr>
                                                                            )}
                                                                        </tbody>
                                                                     </table>
                                                                 </div>
                                                             </div>
                                                             
                                                             <div className="text-[9px] text-[var(--v-text-faint)] font-black uppercase tracking-widest">
                                                                Nota: O espelho consolidado resume totais até a competência de filtragem. A inserção manual à esquerda substituirá a tabela mensal.
                                                             </div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                ))}
                                {Object.keys(data.dashboard_meta || {}).length === 0 && (
                                    <tr><td colSpan="5" className="p-8 text-center text-[var(--v-text-faint)] uppercase text-[10px] tracking-widest">Sem métricas de POC para o filtro selecionado</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};
