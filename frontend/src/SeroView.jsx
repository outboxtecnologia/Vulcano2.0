import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API_BASE = "http://127.0.0.1:8000";

const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

export const SeroView = ({ selectedEmpresa }) => {
    const [ano, setAno] = useState((new Date().getFullYear() - (new Date().getMonth() < 3 ? 1 : 0)).toString());
    const [mes, setMes] = useState(new Date().getMonth() < 3 ? '12' : (new Date().getMonth()).toString().padStart(2, '0'));
    const [seroData, setSeroData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [obras, setObras] = useState([]);
    const [selectedObraId, setSelectedObraId] = useState('');

    useEffect(() => {
        if (!selectedEmpresa) return;
        console.log('[SeroView] Carregando obras para empresa:', selectedEmpresa);
        fetch(`${API_BASE}/api/sero/obras?empresa_id=${selectedEmpresa}`, { cache: 'no-cache' })
           .then(res => {
               const ct = res.headers.get('content-type') || '';
               if (!ct.includes('application/json')) {
                   console.error('[SeroView] Obras endpoint retornou não-JSON:', res.status, ct);
                   return [];
               }
               return res.json();
           })
           .then(data => {
               const lista = Array.isArray(data) ? data : [];
               console.log('[SeroView] Obras carregadas:', lista.length);
               setObras(lista);
           })
           .catch(err => console.error('[SeroView] Erro obras:', err));
    }, [selectedEmpresa]);


    const fetchSero = async () => {
        if (!selectedEmpresa || !ano || !mes) {
            console.warn('[SeroView] fetchSero bloqueado:', { selectedEmpresa, ano, mes });
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const endpoint = selectedObraId 
                ? `${API_BASE}/api/sero/maodeobra?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}&cno=${selectedObraId}` 
                : `${API_BASE}/api/sero/maodeobra?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}`;
            console.log('[SeroView] Chamando:', endpoint);
            const res = await fetch(endpoint);
            if (!res.ok) {
                const txt = await res.text();
                throw new Error(`HTTP ${res.status}: ${txt}`);
            }
            const data = await res.json();
            console.log('[SeroView] Dados recebidos:', data?.resumo);
            setSeroData(data);
        } catch (err) {
            console.error('[SeroView] Erro:', err);
            setError(err.message);
            setSeroData(null);
        } finally {
            setLoading(false);
        }
    };

    // Auto-dispara quando empresa/obra/ano/mes mudam
    useEffect(() => {
        if (selectedEmpresa && ano && mes) fetchSero();
    }, [selectedEmpresa, selectedObraId, ano, mes]);


    return (
        <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
                        <Activity className="text-[var(--v-accent-2)]" size={32}/> 
                        Painel SERO / INSS
                    </h2>
                    <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Auditoria de Mão de Obra e CNO</p>
                </div>
            </div>

            <div className="magma-card border border-[var(--v-border)] rounded-[var(--v-radius)] p-4 shrink-0 flex flex-wrap gap-4 items-end bg-[var(--v-surface-container)]">
                <div className="flex-1 min-w-[200px]">
                    <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Obra (CEI/CNO)</label>
                    <select value={selectedObraId} onChange={e => setSelectedObraId(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-2)] text-white text-[11px] font-mono px-3 py-2 rounded outline-none transition-colors">
                        <option value="">Todas as Obras (Consolidado)</option>
                        {obras.map(o => (
                            <option key={o.id} value={String(o.id)}>
                                {o.inscricao ? `${o.inscricao} — ${o.nome}` : o.nome}
                            </option>
                        ))}
                    </select>
                </div>
                <div className="w-24">
                    <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Ano</label>
                    <select value={ano} onChange={e => setAno(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-2)] text-white text-[11px] font-mono px-3 py-2 rounded outline-none transition-colors">
                        {[2023, 2024, 2025, 2026, 2027].map(y => <option key={y} value={String(y)}>{y}</option>)}
                    </select>
                </div>
                <div className="w-24">
                    <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Mês</label>
                    <select value={mes} onChange={e => setMes(e.target.value)} className="w-full bg-[#111] border border-[#333] hover:border-[#555] focus:border-[var(--v-accent-2)] text-white text-[11px] font-mono px-3 py-2 rounded outline-none transition-colors">
                        {Array.from({length: 12}, (_, i) => String(i + 1).padStart(2, '0')).map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>
                <button onClick={fetchSero} disabled={loading} className="flex items-center gap-2 bg-[var(--v-accent-2)]/10 border border-[var(--v-accent-2)]/30 text-[var(--v-accent-2)] hover:bg-[var(--v-accent-2)] hover:text-black transition-all font-black text-[10px] tracking-widest uppercase rounded px-6 py-2 h-[34px]">
                    {loading ? <RefreshCw size={14} className="animate-spin" /> : <ShieldCheck size={14}/>} Processar Auditoria INSS
                </button>
            </div>

            {error && !seroData && (
                <div className="bg-[var(--v-error)]/10 text-[var(--v-error)] border border-[var(--v-error)]/30 p-4 rounded-[var(--v-radius)] flex items-center gap-3">
                    <AlertCircle size={20} /> <span className="text-sm font-bold">{error}</span>
                </div>
            )}

            {seroData && (
                <>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="magma-card p-6 border-l-4 border-[var(--v-accent-2)]">
                            <span className="text-[10px] font-bold text-[var(--v-text-faint)] uppercase tracking-widest">Base Mão de Obra Total</span>
                            <h3 className="text-2xl font-black text-[var(--v-text-bold)] mt-2">{formatCurrency(seroData.resumo?.mao_de_obra || 0)}</h3>
                            <p className="text-[10px] text-[var(--v-text-faint)] mt-1">Folha + Terceiros/GPS</p>
                        </div>
                        <div className="magma-card p-6 border-l-4 border-[#60a5fa]">
                            <span className="text-[10px] font-bold text-[#60a5fa] uppercase tracking-widest">↳ Folha (CALCULORATEIO)</span>
                            <h3 className="text-xl font-black text-[#60a5fa] mt-2">{formatCurrency(seroData.resumo?.mao_de_obra_folha || 0)}</h3>
                        </div>
                        <div className="magma-card p-6 border-l-4 border-[#34d399]">
                            <span className="text-[10px] font-bold text-[#34d399] uppercase tracking-widest">↳ Terceiros/GPS (VALORORIGEMGPS)</span>
                            <h3 className="text-xl font-black text-[#34d399] mt-2">{formatCurrency(seroData.resumo?.mao_de_obra_terceiros_gps || 0)}</h3>
                        </div>
                        <div className="magma-card p-6 border-l-4 border-[var(--v-accent-5)] bg-[var(--v-accent-5)]/10">
                            <span className="text-[10px] font-bold text-[var(--v-accent-5)] uppercase tracking-widest">Apuração INSS A Recolher</span>
                            <h3 className="text-2xl font-black text-[var(--v-accent-5)] mt-2 drop-shadow-[0_0_10px_rgba(255,166,0,0.5)]">{formatCurrency(seroData.resumo?.total_inss || 0)}</h3>
                        </div>
                        <div className="magma-card p-6 border-l-4 border-white/20">
                            <span className="text-[10px] font-bold text-[var(--v-text-faint)] uppercase tracking-widest">CUB Padrão/Vigente</span>
                            <h3 className="text-2xl font-black text-[var(--v-text-bold)] mt-2">{formatCurrency(seroData.resumo?.cub_vigente || 0)}</h3>
                        </div>
                        <div className="magma-card p-6 border-l-4 border-[#00ff88]">
                            <span className="text-[10px] font-bold text-[#00ff88] uppercase tracking-widest">Área Obra (m²) Acumulada</span>
                            <h3 className="text-2xl font-black text-[#00ff88] mt-2 drop-shadow-[0_0_10px_rgba(0,255,136,0.5)]">
                                {Number(seroData.resumo?.area_total || (selectedObraId ? obras.find(o => o.cno === selectedObraId)?.metragem : obras.reduce((a,b)=>a+(b.metragem||0),0)) || 0).toLocaleString('pt-BR')} m²
                            </h3>
                        </div>
                    </div>

                    {/* Tabela Terceiros/GPS */}
                    {seroData.alocacoes_terceiros?.length > 0 && (
                        <div className="magma-card p-5 border border-[var(--v-border)]">
                            <h4 className="text-[10px] tracking-widest uppercase font-bold text-[#34d399] mb-3">
                                Mão de Obra Alocada — Terceiros GPS ({seroData.alocacoes_terceiros.length} registros)
                            </h4>
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="border-b border-[var(--v-border)] text-[var(--v-text-faint)]">
                                            <th className="text-left pb-2 pr-4">Competência</th>
                                            <th className="text-left pb-2 pr-4">Tomador/Obra</th>
                                            <th className="text-left pb-2 pr-4">CNO/CNPJ</th>
                                            <th className="text-right pb-2">VALORORIGEMGPS</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {seroData.alocacoes_terceiros.slice(0, 50).map((t, i) => (
                                            <tr key={i} className="border-b border-[var(--v-border)]/30 hover:bg-white/5">
                                                <td className="py-1.5 pr-4 font-mono text-[var(--v-text-faint)]">{t.compet}</td>
                                                <td className="py-1.5 pr-4 text-[var(--v-text-bold)]">{t.nome_obra}</td>
                                                <td className="py-1.5 pr-4 font-mono text-[var(--v-text-faint)]">{t.cno}</td>
                                                <td className="py-1.5 text-right font-bold text-[#34d399]">{formatCurrency(t.valor_recolhido)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    <div className="flex-1 min-h-[300px] magma-card p-6 border border-[var(--v-border)] relative">
                        <h4 className="text-[10px] tracking-widest uppercase font-bold text-[var(--v-text-faint)] mb-4">Avanço Físico-Financeiro (% de Obra)</h4>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={seroData.curva_s || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                                <XAxis dataKey="mes" stroke="#444" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="#444" fontSize={10} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: '#131313', border: '1px solid #333' }} />
                                <Line type="monotone" dataKey="previsto" stroke="#888" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                                <Line type="monotone" dataKey="realizado" stroke="var(--v-accent-2)" strokeWidth={3} dot={{ fill: 'var(--v-accent-2)' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </>
            )}
        </div>
    );
};
