import React, { useState, useEffect } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, Search, Loader2, ShieldCheck } from 'lucide-react';
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
    const [editId, setEditId] = useState(null);
    const [baixa, setBaixa] = useState({ data_pagamento: '', valor: '', variacao: '', desconto: '' });
    const [salvando, setSalvando] = useState(false);
    const [editParcela, setEditParcela] = useState(null);
    const [salvandoEd, setSalvandoEd] = useState(false);

    const abrirEdicaoParcela = (r) => setEditParcela({
        row: r, venc: r.vencimento || '', valor: r.valor_parcela != null ? String(r.valor_parcela) : '',
        rotulo: r.parcela || '', obs: r.obs || ''
    });

    const salvarEdicaoParcela = async () => {
        const m = editParcela;
        if (!m) return;
        if (m.venc && m.venc < '1990-01-01') { alert('Data inválida.'); return; }
        if (m.valor !== '' && !(parseFloat(m.valor) > 0)) { alert('Valor deve ser maior que zero.'); return; }
        setSalvandoEd(true);
        try {
            const idStr = String(m.row.id);
            const isPrazo = idStr.startsWith('prazo_');
            const url = isPrazo
                ? `${API_BASE}/api/vulcano/cronograma/prazo/${idStr.replace('prazo_', '')}`
                : `${API_BASE}/api/vulcano/receber/${idStr}`;
            const payload = isPrazo
                ? { data: m.venc || undefined, valor: m.valor !== '' ? parseFloat(m.valor) : undefined, referencia: m.rotulo }
                : { data: m.venc || undefined, valor_parcela: m.valor !== '' ? parseFloat(m.valor) : undefined, parcela: m.rotulo, obs: m.obs };
            const res = await fetch(url, {
                method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const body = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
            setEditParcela(null);
            pesquisar();
        } catch (e) { alert('Falha ao salvar edição: ' + e.message); }
        finally { setSalvandoEd(false); }
    };

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
        // a seta ja navega de verdade: rebusca o novo periodo na hora (com os
        // valores explicitos — o estado ainda nao foi aplicado neste tick)
        if (selectedEmpresa) pesquisar(a, m);
    };

    const [saneando, setSaneando] = useState(false);
    const sanearCronograma = async () => {
        if (!selectedEmpresa) { alert('Selecione a empresa.'); return; }
        setSaneando(true);
        try {
            const emp = empreendimentoId ? `&empreendimento_id=${empreendimentoId}` : '';
            const base = `${API_BASE}/api/vulcano/cronograma/sanear?empresa_id=${selectedEmpresa}${emp}`;
            const prev = await (await fetch(`${base}&dry_run=true`, { method: 'POST' })).json();
            if (prev.success === false) throw new Error(prev.detail || 'Prévia do saneamento falhou.');
            if (!prev.parcelas_a_marcar) { alert('Nada a sanear: o cronograma já está em dia com o Razão de recebimentos.'); return; }
            const escopo = empreendimentoId ? 'do empreendimento selecionado' : 'da empresa TODA';
            if (!window.confirm(
                `Saneamento do cronograma ${escopo}:\n\n` +
                `• ${prev.parcelas_a_marcar} parcela(s) antigas em ${prev.vendas} venda(s)\n` +
                `• ${(prev.valor_a_marcar || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })} já cobertos pelo Razão de recebimentos\n\n` +
                `Elas serão marcadas como pagas no cronograma e saem das "Previstas". Confirmar?`)) return;
            const res = await (await fetch(`${base}&dry_run=false`, { method: 'POST' })).json();
            if (res.success === false) throw new Error(res.detail || 'Saneamento falhou.');
            alert(res.message || 'Saneamento concluído.');
            if (data) pesquisar();
        } catch (e) { alert(e.message); }
        finally { setSaneando(false); }
    };

    const pesquisar = async (a = ano, m = mes) => {
        if (!selectedEmpresa) { alert('Selecione a empresa.'); return; }
        setLoading(true); setError(null);
        try {
            const emp = empreendimentoId ? `&empreendimento_id=${empreendimentoId}` : '';
            const res = await fetch(`${API_BASE}/api/vulcano/recebimentos-mensal?empresa_id=${selectedEmpresa}&ano=${a}&mes=${m}${emp}`);
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : res.statusText);
            setData(d);
        } catch (e) { setError(e.message); setData(null); }
        finally { setLoading(false); }
    };

    const rows = data?.data || [];
    const tot = data?.totais || {};
    const corStatus = (s) => s === 'PAGO' ? '#22c55e' : s === 'VENCIDA' ? '#f97316' : '#8a7a68';

    const desfazerBaixa = async (r) => {
        if (!window.confirm(`Desfazer a baixa da parcela de ${fmt(r.valor_parcela)} (${r.comprador})?\nEla volta a ficar em aberto.`)) return;
        try {
            const res = await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa/desfazer`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_receber: String(r.id), empresa_id: parseInt(selectedEmpresa, 10) })
            });
            const d = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(d?.detail || `HTTP ${res.status}`);
            pesquisar();
        } catch (e) { alert('Falha ao desfazer: ' + e.message); }
    };

    const abrirBaixa = (r) => {
        if (r.status === 'PAGO') return;
        setEditId(r.id);
        setBaixa({
            data_pagamento: new Date().toISOString().slice(0, 10),
            valor: String(r.valor_parcela ?? ''),
            variacao: '', desconto: '',
        });
    };

    const salvarBaixa = async (r) => {
        const valor = parseFloat(baixa.valor) || 0;
        const variacao = parseFloat(baixa.variacao) || 0;
        const desconto = parseFloat(baixa.desconto) || 0;
        const total = Math.round((valor + variacao - desconto) * 100) / 100;
        if (total <= 0) { alert('Informe o valor da baixa.'); return; }
        // trava: a data do recebimento tem que estar DENTRO da competência aberta
        const compet = `${ano}-${String(mes).padStart(2, '0')}`;
        if (!String(baixa.data_pagamento || '').startsWith(compet)) {
            alert(`Data de recebimento ${baixa.data_pagamento || '(vazia)'} fora da competência ${String(mes).padStart(2, '0')}/${ano}.\nNavegue para o mês correto com as setas ‹ › antes de baixar, ou ajuste a data.`);
            return;
        }
        setSalvando(true);
        try {
            const res = await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id_receber: r.id.toString(),
                    empresa_id: parseInt(selectedEmpresa, 10),
                    valor_pago: total,
                    data_pagamento: baixa.data_pagamento,
                    acrescimos: variacao,
                    descontos: desconto,
                }),
            });
            const d = await res.json();
            if (!res.ok || d.success === false) throw new Error(d.detail || d.error || 'Falha na baixa.');
            // atualização otimista: linha + saldo das linhas da mesma venda + totais.
            // O saldo devedor cai pelo PRINCIPAL (valor-base da parcela) — a variação
            // é receita financeira e não amortiza o contrato.
            const principal = Math.round((total - variacao + desconto) * 100) / 100;
            setData(prev => {
                const novas = prev.data.map(x => {
                    let y = { ...x };
                    if (x.venda_id === r.venda_id) y.saldo_atual = Math.round((y.saldo_atual - principal) * 100) / 100;
                    if (x.id === r.id) y = { ...y, status: 'PAGO', total_pago: total, variacao, desconto, data_pagto: baixa.data_pagamento };
                    return y;
                });
                const t = { ...prev.totais };
                t.total_pago = Math.round((t.total_pago + total) * 100) / 100;
                t.variacao = Math.round((t.variacao + variacao) * 100) / 100;
                t.desconto = Math.round((t.desconto + desconto) * 100) / 100;
                t.saldo_atual = Math.round((t.saldo_atual - principal) * 100) / 100;
                return { ...prev, data: novas, totais: t };
            });
            setEditId(null);
        } catch (e) { alert(e.message); }
        finally { setSalvando(false); }
    };

    return (
        <div className="w-full flex flex-col gap-4 pt-4 pb-10 px-4">
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#22c55e]/10 border border-[#22c55e]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <CalendarDays size={16} className="text-[#22c55e]" />
                </div>
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase text-white">Recebimentos — Mensal</h2>
                    <p className="text-[10px] text-[#444] uppercase tracking-[0.25em]">Visão do analista · clique numa parcela em aberto para baixar (data, valor, variação, desconto)</p>
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
                <button onClick={() => pesquisar()} disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#22c55e]/15 border border-[#22c55e]/30 text-[#22c55e] text-[11px] font-bold uppercase tracking-wider hover:bg-[#22c55e]/25 disabled:opacity-40">
                    {loading ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />} Pesquisar
                </button>
                <button onClick={sanearCronograma} disabled={saneando}
                    title="Marca como cobertas as parcelas antigas do cronograma que o Razão de recebimentos já pagou (elas somem das 'Previstas'). Mostra a prévia antes de gravar."
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#f97316]/10 border border-[#f97316]/25 text-[#f97316] text-[11px] font-bold uppercase tracking-wider hover:bg-[#f97316]/20 disabled:opacity-40">
                    {saneando ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Sanear cronograma
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
                                <Th>Parcela</Th><Th>Observação</Th><Th></Th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((r, i) => {
                                const editando = editId === r.id;
                                const totalEdicao = Math.round(((parseFloat(baixa.valor) || 0) + (parseFloat(baixa.variacao) || 0) - (parseFloat(baixa.desconto) || 0)) * 100) / 100;
                                const inputCls = "w-24 bg-black border border-[#22c55e]/40 text-white text-[11px] font-mono px-1.5 py-1 rounded outline-none text-right";
                                const onKey = (e) => { if (e.key === 'Enter') salvarBaixa(r); if (e.key === 'Escape') setEditId(null); };
                                return (
                                    <tr key={r.id ?? i}
                                        onClick={() => !editando && abrirBaixa(r)}
                                        className={`border-b border-[#0f0f0f] hover:bg-[#111] ${r.status !== 'PAGO' ? 'cursor-pointer' : ''} ${editando ? 'bg-[#101a10]' : ''}`}>
                                        <td className="px-3 py-2 font-mono text-[#666]">{r.venda_id}</td>
                                        <td className="px-3 py-2 font-mono text-[#666] whitespace-nowrap">{r.cpf_cnpj}</td>
                                        <td className="px-3 py-2 text-[#bbb] whitespace-nowrap max-w-56 truncate">{r.comprador}</td>
                                        <td className="px-3 py-2 text-[#777] max-w-44 truncate">{(r.unidade || '').replace(/\s+/g, ' ')}</td>
                                        {!empreendimentoId && <td className="px-3 py-2 text-[#777] max-w-40 truncate">{r.empreendimento}</td>}
                                        <td className="px-3 py-2 font-mono text-right text-[#999]">{fmt(r.vlr_venda)}</td>
                                        <td className="px-3 py-2 font-mono text-right text-[#777]">{fmt(r.saldo_anterior)}</td>
                                        <td className="px-3 py-2 font-mono text-[#22c55e]">
                                            {editando ? (
                                                <input type="date" value={baixa.data_pagamento} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, data_pagamento: e.target.value }))}
                                                    onClick={e => e.stopPropagation()}
                                                    className="bg-black border border-[#22c55e]/40 text-white text-[10px] font-mono px-1.5 py-1 rounded outline-none" />
                                            ) : (r.data_pagto || '')}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right" style={{ color: corStatus(r.status), fontWeight: 700 }}>
                                            {editando ? (
                                                <input type="number" step="0.01" autoFocus value={baixa.valor} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, valor: e.target.value }))}
                                                    onFocus={e => e.target.select()} onClick={e => e.stopPropagation()}
                                                    className={inputCls} />
                                            ) : fmt(r.valor_parcela)}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-[#666]">
                                            {editando ? (
                                                <input type="number" step="0.01" placeholder="0,00" value={baixa.desconto} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, desconto: e.target.value }))}
                                                    onClick={e => e.stopPropagation()} className={inputCls} />
                                            ) : fmt(r.desconto)}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-[#666]">
                                            {editando ? (
                                                <input type="number" step="0.01" placeholder="0,00" value={baixa.variacao} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, variacao: e.target.value }))}
                                                    onClick={e => e.stopPropagation()} className={inputCls} />
                                            ) : fmt(r.variacao)}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-white font-bold">
                                            {editando ? (
                                                <span className="flex items-center justify-end gap-2">
                                                    <span className="text-[#22c55e]">{fmt(totalEdicao)}</span>
                                                    <button disabled={salvando}
                                                        onClick={e => { e.stopPropagation(); salvarBaixa(r); }}
                                                        className="px-2 py-1 rounded bg-[#22c55e]/20 border border-[#22c55e]/40 text-[#22c55e] text-[9px] font-bold uppercase hover:bg-[#22c55e]/30 disabled:opacity-40">
                                                        {salvando ? '...' : 'Baixar'}
                                                    </button>
                                                    <button onClick={e => { e.stopPropagation(); setEditId(null); }}
                                                        className="px-1.5 py-1 rounded border border-[#333] text-[#666] text-[9px] font-bold uppercase hover:text-white">✕</button>
                                                </span>
                                            ) : (
                                                <span className="flex items-center justify-end gap-1.5">
                                                    {fmt(r.total_pago)}
                                                    {r.status === 'PAGO' && r.baixa_local && (
                                                        <button title="Desfazer esta baixa (feita pelo Vulcano 2.0) — a parcela volta a ficar em aberto"
                                                            onClick={e => { e.stopPropagation(); desfazerBaixa(r); }}
                                                            className="px-1 py-0.5 rounded border border-[#ef4444]/40 text-[#ef4444] text-[9px] font-bold hover:bg-[#ef4444]/15">✕</button>
                                                    )}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-[#999]">{fmt(r.saldo_atual)}</td>
                                        <td className="px-3 py-2 font-mono whitespace-nowrap" style={{ color: r.status === 'VENCIDA' ? '#ef4444' : '#8a7a68' }}>{r.parcela}</td>
                                        <td className="px-3 py-2 text-[#8a7a68] whitespace-nowrap max-w-44 truncate">{r.obs}</td>
                                        <td className="px-2 py-2">
                                            <button title="Editar parcela (vencimento, valor, rótulo)"
                                                onClick={e => { e.stopPropagation(); abrirEdicaoParcela(r); }}
                                                className="px-1.5 py-0.5 rounded border border-[#333] text-[#8a7a68] text-[10px] hover:text-white hover:border-[#666]">✎</button>
                                        </td>
                                    </tr>
                                );
                            })}
                            {data && rows.length === 0 && (
                                <tr><td colSpan={16} className="py-16 text-center text-[#333] text-[10px] uppercase tracking-widest">
                                    Sem parcelas para o período selecionado.
                                </td></tr>
                            )}
                            {!data && !loading && (
                                <tr><td colSpan={16} className="py-16 text-center text-[#2a2a2a] text-[10px] uppercase tracking-widest">
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
                                    <td colSpan={3}></td>
                                </tr>
                            </tfoot>
                        )}
                    </table>
                </div>
            </div>

            {/* MODAL EDITAR PARCELA */}
            {editParcela && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[110] p-6">
                    <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6 bg-[#0a0a0a] border border-[#2a2a2a]">
                        <h3 className="text-[13px] font-black uppercase tracking-widest text-white mb-1">✎ Editar Parcela</h3>
                        <p className="text-[11px] text-[#8a7a68] mb-5">
                            <b className="text-white">#{String(editParcela.row.id).replace('prazo_', 'pr_')}</b> — {editParcela.row.comprador} · {(editParcela.row.unidade || '').replace(/\s+/g, ' ')}
                            {String(editParcela.row.id).startsWith('prazo_') && <> <span className="text-[#ffd28a]">(cronograma ainda não efetivado)</span></>}
                        </p>
                        <div className="grid grid-cols-2 gap-3 mb-4">
                            <div>
                                <label className="text-[9px] uppercase font-bold mb-1 block text-[#555] tracking-widest">Vencimento</label>
                                <input type="date" min="1990-01-01" value={editParcela.venc} onChange={e => setEditParcela({ ...editParcela, venc: e.target.value })}
                                    className="w-full bg-black border border-[#333] text-white text-[11px] font-mono px-2 py-1.5 rounded outline-none" />
                            </div>
                            <div>
                                <label className="text-[9px] uppercase font-bold mb-1 block text-[#555] tracking-widest">Valor da parcela</label>
                                <input type="number" step="0.01" value={editParcela.valor} onChange={e => setEditParcela({ ...editParcela, valor: e.target.value })}
                                    className="w-full bg-black border border-[#333] text-white text-[11px] font-mono px-2 py-1.5 rounded outline-none text-right" />
                            </div>
                            <div>
                                <label className="text-[9px] uppercase font-bold mb-1 block text-[#555] tracking-widest">Parcela (rótulo)</label>
                                <input value={editParcela.rotulo} onChange={e => setEditParcela({ ...editParcela, rotulo: e.target.value })}
                                    className="w-full bg-black border border-[#333] text-white text-[11px] font-mono px-2 py-1.5 rounded outline-none" />
                            </div>
                            {!String(editParcela.row.id).startsWith('prazo_') && (
                                <div>
                                    <label className="text-[9px] uppercase font-bold mb-1 block text-[#555] tracking-widest">Observação</label>
                                    <input value={editParcela.obs} onChange={e => setEditParcela({ ...editParcela, obs: e.target.value })}
                                        className="w-full bg-black border border-[#333] text-white text-[11px] px-2 py-1.5 rounded outline-none" />
                                </div>
                            )}
                        </div>
                        {editParcela.row.status === 'PAGO' && (
                            <p className="text-[10px] text-[#f97316] mb-3">Parcela já paga: o valor não pode ficar menor que o total pago.</p>
                        )}
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setEditParcela(null)} className="px-4 py-2 hover:bg-white/5 text-[10px] font-bold uppercase tracking-widest rounded text-[#8a7a68]">Cancelar</button>
                            <button onClick={salvarEdicaoParcela} disabled={salvandoEd}
                                className="px-6 py-2 rounded text-[10px] font-bold uppercase tracking-widest bg-[#22c55e]/20 border border-[#22c55e]/40 text-[#22c55e] hover:bg-[#22c55e]/30 disabled:opacity-40">
                                {salvandoEd ? 'Gravando...' : 'Salvar'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
