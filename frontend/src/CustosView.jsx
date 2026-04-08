import React, { useState, useEffect } from 'react';
import { Layers, CheckSquare, Search, AlertCircle, RefreshCw, HandCoins, UploadCloud, Plus, Calendar, Building2 } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ --,--';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const CustosView = ({ selectedEmpresa }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [error, setError] = useState(null);
    
    // Filters State - matching standard Vulcano pattern
    const [selectedEmp, setSelectedEmp] = useState('');
    const [filterMes, setFilterMes] = useState('');
    const [filterAno, setFilterAno] = useState(new Date().getFullYear().toString());
    
    // Detalhamento State (LCTOGER/LCTOCTB)
    const [detalhamento, setDetalhamento] = useState({ extrato_gerencial: [], extrato_contabil: [] });
    
    // Modal state for Lançamento
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
            
        } catch(e) {
            setError(e.message);
            setDetalhamento({ extrato_gerencial: [], extrato_contabil: [] });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [selectedEmpresa]);

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
                    const pocInformado = pocMatch.percentual / 100.0;
                    
                    // CPC 47 / IFRS 15 Formula
                    const suggestedAccumulated = totalGasto * fracaoVendida * pocInformado;
                    const suggestedMonth = suggestedAccumulated - lastCost;
                    
                    if (suggestedMonth > 0) {
                        setFormValor(suggestedMonth.toFixed(2));
                    }
                }
            } else {
                 setFormPoc('');
            }
        }
    }, [formMes, formAno, isModalOpen, activeEmpData]);

    const strPad = (n) => String(n).padStart(2, '0');

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
            if (!response.ok) {
                throw new Error(json.detail || "Erro ao efetivar lançamento contábil");
            }
            alert("Lançamento efetivado! " + formatCurrency(reqData.valor_custo));
            setIsModalOpen(false);
            loadData(); // refresh full DB status
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
            handlePesquisar(); // Reload on demand
        } catch(e) {
            alert(e.message);
        } finally {
            setSyncing(false);
        }
    };

    // Filter timeline based on year/month
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

            {/* SELETOR TOP NAVIGATION (Vulcano Standard) */}
            <div className="magma-card p-4 rounded-sm flex items-end gap-6 bg-[#0a0a0a] border border-[#222]">
                <div className="flex-1">
                    <label className="text-[10px] font-black uppercase tracking-widest text-[#666] mb-2 flex items-center gap-2">
                        <Building2 size={12}/> Selecione o Empreendimento
                    </label>
                    <div className="relative">
                        <select 
                            value={selectedEmp}
                            onChange={(e) => setSelectedEmp(e.target.value)}
                            className="w-full bg-[#151515] border border-[#333] text-white p-3 rounded-sm appearance-none focus:outline-none focus:border-[var(--v-accent-2)] flex items-center pr-10 hover:bg-[#1a1a1a] transition-colors"
                        >
                            <option value="" disabled>-- SELECIONE UMA OBRA PARA VER O CUSTO --</option>
                            {data.map(emp => (
                                <option key={emp.id} value={emp.id}>{emp.nome}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="w-48">
                    <label className="text-[10px] font-black uppercase tracking-widest text-[#666] mb-2 flex items-center gap-2">
                        <Calendar size={12}/> Mês / Ano (Filtro)
                    </label>
                    <div className="flex gap-2">
                         <input 
                            type="number" 
                            placeholder="Mês" 
                            value={filterMes}
                            onChange={(e) => setFilterMes(e.target.value)} 
                            className="w-full bg-[#151515] border border-[#333] p-3 text-center text-white rounded-sm outline-none focus:border-[var(--v-accent-2)]" 
                        />
                         <input 
                            type="number" 
                            placeholder="Ano" 
                            value={filterAno}
                            onChange={(e) => setFilterAno(e.target.value)} 
                            className="w-full bg-[#151515] border border-[#333] p-3 text-center text-white rounded-sm outline-none focus:border-[var(--v-accent-2)]" 
                        />
                    </div>
                </div>
                
                <button 
                    onClick={handleSync}
                    disabled={syncing}
                    className="bg-[#222] hover:bg-[#333] text-white w-40 py-3 rounded-sm text-[10px] font-black uppercase flex items-center justify-center gap-2 transition-all disabled:opacity-50 border border-[#444]"
                >
                    {syncing ? <RefreshCw className="animate-spin text-[var(--v-accent-2)]" size={14}/> : <RefreshCw size={14} className="text-[#888]"/>} 
                    Sync Questor
                </button>

                <button 
                    onClick={() => {
                        setFormMes(filterMes || '');
                        setFormAno(filterAno || new Date().getFullYear().toString());
                        setIsModalOpen(true);
                    }}
                    disabled={!selectedEmp || loading}
                    className="bg-[var(--v-accent-2)] hover:bg-[#ff6a00] text-black w-48 py-3 rounded-sm text-[10px] font-black uppercase flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_var(--v-accent-2)] disabled:opacity-50 disabled:shadow-none"
                >
                    {loading ? <RefreshCw className="animate-spin" size={14}/> : <Plus size={14}/>} 
                    Apropriar Custo
                </button>
            </div>


            {/* RIGHT DASHBOARD (Only visible when Empreendimento selected) */}
            <div className="flex-1 flex flex-col gap-6 overflow-hidden">
                {!activeEmpData ? (
                    <div className="flex-1 border border-[#222] border-dashed rounded-sm flex items-center justify-center text-[#555] flex-col gap-4">
                        <Layers size={48} className="opacity-20" />
                        <p className="text-[10px] uppercase tracking-widest font-bold">Aguardando Seleção de Empreendimento</p>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2">
                        {/* PARAMETRIZAÇÃO ALERTS */}
                        {(!activeEmpData.conta_custo || !activeEmpData.conta_estoque) && (
                            <div className="bg-[var(--v-error)]/10 border border-[var(--v-error)] p-4 rounded-sm flex items-center gap-4 text-[var(--v-error)] mb-2 shadow-[0_0_15px_var(--v-error)]">
                                <AlertCircle size={20} />
                                <div>
                                    <h4 className="font-bold text-sm">Alerta Contábil Crítico</h4>
                                    <p className="text-[10px] uppercase tracking-wider mt-1">Este empreendimento não possui contas parametrizadas no Vulcano. A integração com Questor Falhará.</p>
                                </div>
                            </div>
                        )}

                        {/* STATISTICS */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="magma-card p-4 rounded-sm border border-[#222]">
                                <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Custo Incorrido Real (Questor)</p>
                                <h4 className="text-xl font-black text-white">{formatCurrency(activeEmpData.custo_real_gasto)}</h4>
                            </div>
                            <div className="magma-card p-4 rounded-sm border border-[#222]">
                                <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Índice Comercial (Vendidas)</p>
                                <h4 className="text-xl font-black text-white">{(activeEmpData.fracao_vendida * 100).toFixed(2)}% da Obra</h4>
                            </div>
                            <div className="magma-card p-4 rounded-sm border border-[#222]">
                                <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-1">Total DRTEE Apropriado</p>
                                <h4 className="text-xl font-black text-[var(--v-accent-2)] drop-shadow-[0_0_10px_var(--v-accent-2)]">
                                    {formatCurrency((activeEmpData.custos_lancados || []).reduce((acc, curr) => acc + curr.valor, 0))}
                                </h4>
                            </div>
                        </div>

                        {/* GRID TABLES (POC x LCTOGER x LCTOCTB) */}
                        <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
                            
                            {/* LEFT COL: TABELA DE EVOLUÇÃO POC (Original) */}
                            <div className="col-span-12 xl:col-span-6 magma-card flex flex-col border border-[var(--v-border)] rounded-sm overflow-hidden min-h-[300px]">
                                <div className="p-4 border-b border-[#222] bg-[#111] flex justify-between items-center shrink-0">
                                    <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#888]">
                                        Memória de Cálculo (Apuração CPC 47)
                                    </h3>
                                    <span className="text-[10px] bg-[#222] px-2 py-1 border border-[#333] text-[#aaa] font-mono tracking-wider shadow-sm">
                                        COMPETÊNCIA: {filterAno}-{strPad(filterMes)}
                                    </span>
                                </div>
                                <div className="flex-1 p-6 flex flex-col gap-3 font-mono text-[11px]">
                                    
                                    <div className="flex justify-between items-center border-b border-[#222] pb-2">
                                        <span className="text-[#888]">A. Total de Gastos Incorridos (Questor LCTOGER)</span>
                                        <span className="text-white font-bold">{formatCurrency(activeEmpData.custo_real_gasto)}</span>
                                    </div>
                                    
                                    <div className="flex justify-between items-center border-b border-[#222] pb-2">
                                        <span className="text-[#888]">B. Índice Comercial (% Área Vendida)</span>
                                        <span className="text-white font-bold">
                                            {(activeEmpData.fracao_vendida * 100).toFixed(4)} % 
                                            <span className="text-[9px] text-[#555] ml-2 font-normal">
                                                ({(activeEmpData.area_vendida || 0).toFixed(2)}m² / {(activeEmpData.area_total || 0).toFixed(2)}m²)
                                            </span>
                                        </span>
                                    </div>
                                    
                                    <div className="flex justify-between items-center border-b border-[#222] pb-2">
                                        <span className="text-[#888]">C. Índice de Evolução Física (% POC Mês)</span>
                                        <span className="text-white font-bold">{(activeEmpData.poc_atual || 0).toFixed(4)} %</span>
                                    </div>
                                    
                                    <div className="flex justify-between items-center border-b border-[#222] pb-2 mt-4">
                                        <span className="text-[var(--v-accent-2)] font-bold">CUSTO TOTAL CALCULADO (A * B * C)</span>
                                        <span className="text-[var(--v-accent-2)] font-bold">
                                            {formatCurrency(
                                                activeEmpData.custo_real_gasto * 
                                                activeEmpData.fracao_vendida * 
                                                ((activeEmpData.poc_atual || 0) / 100.0)
                                            )}
                                        </span>
                                    </div>

                                    <div className="flex justify-between items-center border-b border-[#222] pb-2 text-[var(--v-error)]">
                                        <span className="font-bold">- Custo Acumulado Reconhecido Anteriormente</span>
                                        <span className="font-bold">{formatCurrency((activeEmpData.custo_reconhecido_anterior || 0))}</span>
                                    </div>

                                    <div className="flex justify-between items-center p-4 bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/30 mt-4 rounded-sm shadow-[0_0_20px_rgba(255,100,0,0.1)]">
                                        <div className="flex flex-col">
                                            <span className="text-[var(--v-accent)] font-black text-sm uppercase">Lançamento a Efetuar Neste Mês</span>
                                            <span className="text-[9px] text-[#888] mt-1 track-widest">
                                                D É B I T O : {activeEmpData.conta_custo || 'S/ Conta'} - {activeEmpData.conta_custo_nome || ''} (Apropriação Imob.)<br/>
                                                C R É D I T O : {activeEmpData.poc_atual >= 100 ? (activeEmpData.conta_estconc || 'S/ Conta') + ' - ' + (activeEmpData.conta_estconc_nome || '') + ' (Estoque Concluído)' : (activeEmpData.conta_estoque || 'S/ Conta') + ' - ' + (activeEmpData.conta_estoque_nome || '') + ' (Estoque em Andamento)'} 
                                            </span>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-[var(--v-accent)] font-black text-2xl tracking-tighter drop-shadow-md">
                                                {formatCurrency(
                                                    Math.max(0, (
                                                        activeEmpData.custo_real_gasto * 
                                                        activeEmpData.fracao_vendida * 
                                                        ((activeEmpData.poc_atual || 0) / 100.0)
                                                    ) - (activeEmpData.custo_reconhecido_anterior || 0))
                                                )}
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
                                
                                {/* Drill-Down Gasto Real */}
                                <div className="magma-card flex-1 flex flex-col border border-[var(--v-border)] rounded-sm overflow-hidden min-h-[250px] shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                                     <div className="p-3 border-b border-[#222] bg-[#111] flex justify-between items-center shrink-0">
                                        <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#999] flex flex-col">
                                            <span className="text-[var(--v-accent-2)]">Extrato Financeiro Incorrido (LCTOGER)</span>
                                            <span className="text-[8px] text-[#555] opacity-80 mt-0.5">Composição Mensal de Desembolso Direto da Obra</span>
                                        </h3>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                                        <table className="w-full text-left text-[11px] whitespace-nowrap">
                                              <thead className="bg-[#0b0b0b] sticky top-0 z-10 shadow-sm">
                                                  <tr>
                                                      <th className="p-3 text-[#555] tracking-widest font-bold border-b border-[#222]">Ano / Mês</th>
                                                      <th className="p-3 text-[#555] tracking-widest font-bold border-b border-[#222]">Custo Acumulado R$</th>
                                                  </tr>
                                              </thead>
                                              <tbody>
                                                  {(!detalhamento.extrato_gerencial || detalhamento.extrato_gerencial.length === 0) ? (
                                                       <tr><td colSpan={2} className="p-6 text-center text-[#555] text-[10px] italic">Sem histórico de custos.</td></tr>
                                                  ) : (
                                                       detalhamento.extrato_gerencial.map((g, idx) => (
                                                            <tr key={idx} className="border-b border-[#111] hover:bg-[#1a1a1a]">
                                                                <td className="p-3 font-mono text-[#ddd]">{g.ano} - {strPad(g.mes)}</td>
                                                                <td className="p-3 font-bold text-white font-mono">{formatCurrency(g.valor)}</td>
                                                            </tr>
                                                       ))
                                                  )}
                                              </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Extrato DRTEE Lançado */}
                                <div className="magma-card flex-1 flex flex-col border border-[var(--v-border)] rounded-sm overflow-hidden min-h-[200px] shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                                     <div className="p-3 border-b border-[#222] bg-[#111] flex justify-between items-center shrink-0">
                                        <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#999] flex flex-col">
                                            <span className="text-green-500">Apropriações de Custo Emitidas (LCTOCTB)</span>
                                            <span className="text-[8px] text-[#555] opacity-80 mt-0.5">Lançamentos efetivados nesta conta baseados no POC</span>
                                        </h3>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                                        <table className="w-full text-left text-[10px] whitespace-nowrap">
                                              <thead className="bg-[#0b0b0b] sticky top-0 z-10 shadow-sm">
                                                  <tr>
                                                      <th className="p-2 text-[#555] border-b border-[#222]">Data Operação</th>
                                                      <th className="p-2 text-[#555] border-b border-[#222]">Chave Contábil</th>
                                                      <th className="p-2 text-[#555] border-b border-[#222]">Valor Apropriado</th>
                                                  </tr>
                                              </thead>
                                              <tbody className="text-[#888]">
                                                  {(!detalhamento.extrato_contabil || detalhamento.extrato_contabil.length === 0) ? (
                                                       <tr><td colSpan={3} className="p-6 text-center text-[#555] italic">Nenhum lançamento foi exportado para o Questor.</td></tr>
                                                  ) : (
                                                       detalhamento.extrato_contabil.map((c, idx) => (
                                                            <tr key={idx} className="border-b border-[#111] hover:bg-[#1a1a1a]">
                                                                <td className="p-3">{c.data}</td>
                                                                <td className="p-3 text-[9px] opacity-70">#{c.chave}</td>
                                                                <td className="p-3 font-bold text-green-400">{formatCurrency(c.valor)}</td>
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
                    <div className="magma-card w-[500px] border border-[var(--v-accent-2)] shadow-[0_0_30px_rgba(255,77,0,0.15)] rounded-sm p-8 flex flex-col gap-6 relative">
                         {/* Close button that fits the aesthetics */}
                        <button onClick={() => setIsModalOpen(false)} className="absolute top-4 right-4 text-[#555] hover:text-[#fff] transition-colors p-2 text-[10px] font-bold uppercase tracking-widest bg-[#111] rounded-sm">X Fechar</button>
                        
                        <div className="flex flex-col gap-1 pr-6">
                            <h2 className="text-xl font-black uppercase tracking-tighter text-white">Criar Lançamento de Custos</h2>
                            <p className="text-[10px] uppercase font-bold text-[#888] tracking-widest">{activeEmpData.nome}</p>
                        </div>
                        
                        <div className="p-4 bg-[#111] border border-[#222] rounded-sm text-[10px] font-mono tracking-widest text-[var(--v-accent-2)] shadow-inner">
                            LCTO Débito: [{activeEmpData.conta_custo || 'N/A'}] Custo Incorrido<br/>
                            LCTO Crédito: [{activeEmpData.conta_estoque || 'N/A'}] Estoque/Obras<br/>
                            Centro de Custo: [{activeEmpData.codigo_cc || 'N/A'}]
                        </div>

                        <form onSubmit={handleLcto} className="flex flex-col gap-5">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[9px] font-black uppercase tracking-widest text-[#555] mb-2 block">Mês a Apropriar</label>
                                    <input type="number" min="1" max="12" value={formMes} onChange={e => setFormMes(e.target.value)} className="w-full bg-[#0b0b0b] border border-[#333] p-3 text-white text-center rounded-sm outline-none focus:border-[var(--v-accent-2)]" required />
                                </div>
                                <div>
                                    <label className="text-[9px] font-black uppercase tracking-widest text-[#555] mb-2 block">Ano Contábil</label>
                                    <input type="number" min="2000" max="2100" value={formAno} onChange={e => setFormAno(e.target.value)} className="w-full bg-[#0b0b0b] border border-[#333] p-3 text-white text-center rounded-sm outline-none focus:border-[var(--v-accent-2)]" required />
                                </div>
                            </div>

                            <div className="p-4 border border-[var(--v-accent)]/30 rounded-sm bg-[var(--v-accent)]/5">
                                <label className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-2)] mb-2 flex justify-between">
                                    Percentual POC Apurado (%)
                                </label>
                                <input type="number" step="0.01" value={formPoc} onChange={e => setFormPoc(e.target.value)} placeholder="0.00" className="w-full bg-transparent border-0 border-b border-[var(--v-accent-2)] text-[var(--v-accent-2)] font-black text-2xl font-mono p-0 outline-none pb-1" required />
                            </div>

                            <div>
                                <label className="text-[9px] font-black uppercase tracking-widest text-[#fff] mb-2 flex justify-between items-center gap-2">
                                   Valor de Custo do Mês (R$) <span className="opacity-50 font-normal normal-case text-[9px] bg-[#222] px-2 py-0.5 rounded-sm">Conta Débito Contábil</span>
                                </label>
                                <input type="number" step="0.01" value={formValor} onChange={e => setFormValor(e.target.value)} placeholder="0.00" className="w-full bg-black border border-white p-4 text-white text-2xl font-black font-mono rounded-sm outline-none focus:border-[var(--v-accent-glow)] shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-colors" required />
                            </div>

                            <div>
                                <label className="text-[9px] font-black uppercase tracking-widest text-[#555] mb-2 block">Histórico LCTO (Questor)</label>
                                <input type="text" value={formHistorico} onChange={e => setFormHistorico(e.target.value)} placeholder="VALOR REF. CUSTO OBRA..." className="w-full bg-[#0b0b0b] border border-[#333] p-3 text-[#aaa] font-bold rounded-sm outline-none focus:border-[var(--v-accent-2)] uppercase" required />
                            </div>

                            <button type="submit" disabled={submitting} className="mt-2 bg-[var(--v-accent-2)] hover:bg-[#ff6a00] text-black w-full py-4 text-[12px] font-black tracking-[0.2em] uppercase flex items-center justify-center gap-3 rounded-sm shadow-[0_0_20px_var(--v-accent-2)] active:scale-95 transition-all">
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
