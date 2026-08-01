import React, { useState, useEffect } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, Search, Loader2 } from 'lucide-react';
import { API_BASE } from './apiBase';

const fmt = (v) => (v ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const Th = ({ children, right }) => (
    <th className={`px-3 py-2 text-[9px] uppercase tracking-widest text-[#555] font-bold whitespace-nowrap ${right ? 'text-right' : 'text-left'}`}>
        {children}
    </th>
);

// Visão mensal legada: parcelas do mês de referência + abertas vencidas,
// com as colunas que o analista usava no sistema antigo.
export const RecebimentosMensalView = ({ selectedEmpresa }) => {
    const hoje = new Date();
    const [ano, setAno] = useState(hoje.getFullYear());
    const [mes, setMes] = useState(hoje.getMonth() + 1);
    const [empreendimentos, setEmpreendimentos] = useState([]);
    const [empreendimentoId, setEmpreendimentoId] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!selectedEmpresa) return;
        fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
            .then(r => r.json())
            .then(d => setEmpreendimentos(Array.isArray(d) ? d : (d.data || [])))
            .catch(() => setEmpreendimentos([]));
    }, [selectedEmpresa]);

    const mudaMes = (delta) => {
        let m = mes + delta, a = ano;
        if (m < 1) { m = 12; a -= 1; }
        if (m > 12) { m = 1; a += 1; }
        setMes(m); setAno(a);
    };

    const pesquisar = async () => {
        if (!selectedEmpresa) { alert('Selecione a empresa.'); return; }
        setLoading(true); setError(null);
        try {
            const emp = empreendimentoId ? `&empreendimento_id=${empreendimentoId}` : '';
            const res = await fetch(`${API_BASE}/api/vulcano/recebimentos-mensal?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}${emp}`);
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : res.statusText);
            setData(d);
        } catch (e) { setError(e.message); setData(null); }
        finally { setLoading(false); }
    };

    const rows = data?.data || [];
    const tot = data?.totais || {};
    const corStatus = (s) => s === 'PAGO' ? '#22c55e' : s === 'VENCIDA' ? '#f97316' : '#8a7a68';

    return (
        <div className="w-full flex flex-col gap-4 pt-4 pb-10 px-4">
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#22c55e]/10 border border-[#22c55e]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <CalendarDays size={16} className="text-[#22c55e]" />
                </div>
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase text-white">Recebimentos — Mensal</h2>
                    <p className="text-[10px] text-[#444] uppercase tracking-[0.25em]">Visão do analista · mês de referência + parcelas em aberto</p>
                </div>
            </div>

            <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-4 flex flex-wrap gap-3 items-end">
                <div className="min-w-64">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Empreendimento</label>
                    <select value={empreendimentoId} onChange={e => setEmpreendimentoId(e.target.value)}
                        className="w-full bg-[#111] border border-[#222] hover:border-[#333] text-white text-[11px] px-2 py-2 rounded-lg outline-none">
                        <option value="">Todos</option>
                        {empreendimentos.map(e => <option key={e.id} value={e.id}>{e.id} — {e.nome}</option>)}
                    </select>
                </div>
                <div>
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[#444] mb-1.5 font-bold">Período</label>
                    <div className="flex items-center gap-1">
                        <button onClick={() => mudaMes(-1)} className="p-2 bg-[#111] border border-[#222] rounded-lg text-[#888] hover:text-white"><ChevronLeft size={13} /></button>
                        <div className="px-3 py-2 bg-[#111] border border-[#222] rounded-lg text-white font-mono text-[12px] font-bold min-w-20 text-center">
                            {String(mes).padStart(2, '0')}/{ano}
                        </div>
                        <button onClick={() => mudaMes(1)} className="p-2 bg-[#111] border border-[#222] rounded-lg text-[#888] hover:text-white"><ChevronRight size={13} /></button>
                    </div>
                </div>
                <button onClick={pesquisar} disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#22c55e]/15 border border-[#22c55e]/30 text-[#22c55e] text-[11px] font-bold uppercase tracking-wider hover:bg-[#22c55e]/25 disabled:opacity-40">
                    {loading ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />} Pesquisar
                </button>
                {data && (
                    <div className="ml-auto text-right">
                        <div className="text-[9px] text-[#444] uppercase tracking-widest">Recebido no mês</div>
                        <div className="text-[15px] font-black font-mono text-[#22c55e]">{fmt(tot.total_pago)}</div>
                    </div>
                )}
            </div>

            {error && <div className="bg-red-950/30 text-red-400 border border-red-900/40 rounded-xl p-3 text-sm font-bold">{error}</div>}

            <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-[11px]">
                        <thead>
                            <tr className="bg-[#0e0e0e]">
                                <Th>Nº</Th><Th>CPF/CNPJ</Th><Th>Comprador</Th><Th>Unidade(s)</Th>
                                {!empreendimentoId && <Th>Empreendimento</Th>}
                                <Th right>Vlr Venda</Th><Th right>Saldo Ant.</Th>
                                <Th>Data Pagto</Th><Th right>Valor Parcela</Th><Th right>Desconto</Th>
                                <Th right>Variação</Th><Th right>Total Pago</Th><Th right>Saldo Atual</Th>
                                <Th>Parcela</Th><Th>Observação</Th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((r, i) => (
                                <tr key={r.id ?? i} className="border-b border-[#0f0f0f] hover:bg-[#111]">
                                    <td className="px-3 py-2 font-mono text-[#666]">{r.venda_id}</td>
                                    <td className="px-3 py-2 font-mono text-[#666] whitespace-nowrap">{r.cpf_cnpj}</td>
                                    <td className="px-3 py-2 text-[#bbb] whitespace-nowrap max-w-56 truncate">{r.comprador}</td>
                                    <td className="px-3 py-2 text-[#777] max-w-44 truncate">{(r.unidade || '').replace(/\s+/g, ' ')}</td>
                                    {!empreendimentoId && <td className="px-3 py-2 text-[#777] max-w-40 truncate">{r.empreendimento}</td>}
                                    <td className="px-3 py-2 font-mono text-right text-[#999]">{fmt(r.vlr_venda)}</td>
                                    <td className="px-3 py-2 font-mono text-right text-[#777]">{fmt(r.saldo_anterior)}</td>
                                    <td className="px-3 py-2 font-mono text-[#22c55e]">{r.data_pagto || ''}</td>
                                    <td className="px-3 py-2 font-mono text-right" style={{ color: corStatus(r.status), fontWeight: 700 }}>{fmt(r.valor_parcela)}</td>
                                    <td className="px-3 py-2 font-mono text-right text-[#666]">{fmt(r.desconto)}</td>
                                    <td className="px-3 py-2 font-mono text-right text-[#666]">{fmt(r.variacao)}</td>
                                    <td className="px-3 py-2 font-mono text-right text-white font-bold">{fmt(r.total_pago)}</td>
                                    <td className="px-3 py-2 font-mono text-right text-[#999]">{fmt(r.saldo_atual)}</td>
                                    <td className="px-3 py-2 font-mono whitespace-nowrap" style={{ color: r.status === 'VENCIDA' ? '#ef4444' : '#8a7a68' }}>{r.parcela}</td>
                                    <td className="px-3 py-2 text-[#8a7a68] whitespace-nowrap max-w-44 truncate">{r.obs}</td>
                                </tr>
                            ))}
                            {data && rows.length === 0 && (
                                <tr><td colSpan={15} className="py-16 text-center text-[#333] text-[10px] uppercase tracking-widest">
                                    Sem parcelas para o período selecionado.
                                </td></tr>
                            )}
                            {!data && !loading && (
                                <tr><td colSpan={15} className="py-16 text-center text-[#2a2a2a] text-[10px] uppercase tracking-widest">
                                    Selecione o mês de referência e pesquise.
                                </td></tr>
                            )}
                        </tbody>
                        {rows.length > 0 && (
                            <tfoot>
                                <tr className="bg-[#0e0e0e] border-t border-[#1e1e1e] font-mono font-bold">
                                    <td colSpan={empreendimentoId ? 7 : 8} className="px-3 py-2.5 text-[9px] uppercase tracking-widest text-[#444]">
                                        Totais · {rows.length} parcelas
                                    </td>
                                    <td className="px-3 py-2.5 text-right text-[#f97316]">{fmt(tot.valor_parcela)}</td>
                                    <td className="px-3 py-2.5 text-right text-[#666]">{fmt(tot.desconto)}</td>
                                    <td className="px-3 py-2.5 text-right text-[#666]">{fmt(tot.variacao)}</td>
                                    <td className="px-3 py-2.5 text-right text-[#22c55e]">{fmt(tot.total_pago)}</td>
                                    <td className="px-3 py-2.5 text-right text-[#999]">{fmt(tot.saldo_atual)}</td>
                                    <td colSpan={2}></td>
                                </tr>
                            </tfoot>
                        )}
                    </table>
                </div>
            </div>
        </div>
    );
};
