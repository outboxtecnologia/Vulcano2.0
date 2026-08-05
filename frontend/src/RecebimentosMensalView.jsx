import React, { useState, useEffect, useMemo } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, Search, Loader2, X, ShieldCheck } from 'lucide-react';
import { API_BASE } from './apiBase';
import { useSearchParamState } from './hooks/useSearchParamState';
import { useTableSort } from './hooks/useTableSort';
import SortIcon from './components/SortIcon';
import { normaliza, termosDeBusca } from './utils/texto';

const fmt = (v) => (v ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Sem sortKey renderiza o <th> simples de sempre — as colunas nao ordenaveis
// ficam intocadas.
const Th = ({ children, right, sortKey, sort, onSort }) => {
    const base = `px-3 py-2 text-[9px] uppercase tracking-widest font-bold whitespace-nowrap ${right ? 'text-right' : 'text-left'}`;
    if (!sortKey || !sort) {
        return <th className={`${base} text-[var(--v-text-faint)]`}>{children}</th>;
    }
    const { sortable, active, dir, ariaSort } = sort.headerProps(sortKey);
    if (!sortable) {
        return <th className={`${base} text-[var(--v-text-faint)]`}>{children}</th>;
    }
    return (
        <th className={base} aria-sort={ariaSort}>
            <button
                type="button"
                onClick={() => onSort(sortKey)}
                // w-full + justify-end: sem isso o text-right do <th> deixa de
                // alinhar quando o filho e flex, e as colunas de dinheiro saem
                // do prumo em relacao ao corpo.
                className={`group w-full inline-flex items-center gap-1 select-none uppercase tracking-widest cursor-pointer transition-colors focus-visible:outline-1 focus-visible:outline-[var(--v-accent)] ${right ? 'justify-end' : 'justify-start'} ${active ? 'text-[var(--v-accent)]' : 'text-[var(--v-text-faint)] hover:text-[var(--v-text-muted)]'}`}
                aria-label={`${children}${active ? (dir === 'asc' ? ' — ordenado crescente' : ' — ordenado decrescente') : ''}; ativar para ${active ? 'inverter' : 'ordenar'}`}
            >
                {children}
                <SortIcon active={active} dir={dir} />
            </button>
        </th>
    );
};

/**
 * Ordem visual das colunas e o que cada uma ordena.
 *
 * Saldo Ant./Saldo Atual NAO sao ordenaveis de proposito: sao atributos da VENDA
 * repetidos em todas as parcelas dela, entao ordenar por eles deixa a ordem
 * dentro da venda ao acaso; alem disso o saldo muda em varias linhas de uma vez
 * na baixa (reembaralhando a tabela sob o cursor) e o total do rodape e
 * deduplicado por venda — nao e a soma da coluna visivel.
 */
const COLUNAS = [
    { key: 'venda_id',       label: 'Nº',             type: 'number' },
    { key: 'cpf_cnpj',       label: 'CPF/CNPJ',       type: 'text' },
    { key: 'comprador',      label: 'Comprador',      type: 'text' },
    { key: 'unidade',        label: 'Unidade(s)',     type: 'text', get: (r) => (r.unidade || '').replace(/\s+/g, ' ') },
    { key: 'empreendimento', label: 'Empreendimento', type: 'text', when: (ctx) => !ctx.empreendimentoId },
    { key: 'vlr_venda',      label: 'Vlr Venda',      type: 'number', right: true, firstDir: 'desc', money: true },
    { key: 'saldo_anterior', label: 'Saldo Ant.',     right: true, money: true },
    { key: 'data_pagto',     label: 'Data Pagto',     type: 'date' },
    { key: 'valor_parcela',  label: 'Valor Parcela',  type: 'number', right: true, firstDir: 'desc', money: true },
    { key: 'desconto',       label: 'Desconto',       type: 'number', right: true, firstDir: 'desc', money: true },
    { key: 'variacao',       label: 'Variação',       type: 'number', right: true, firstDir: 'desc', money: true },
    { key: 'total_pago',     label: 'Total Pago',     type: 'number', right: true, firstDir: 'desc', money: true },
    { key: 'saldo_atual',    label: 'Saldo Atual',    right: true, money: true },
    { key: 'parcela',        label: 'Parcela',        type: 'parcela' },
    { key: 'obs',            label: 'Observação' },
];

/**
 * Texto pesquisavel de uma linha: tudo que aparece nas colunas visiveis.
 *
 * As colunas `money` entram DUAS vezes — o valor cru (2450.9) e o formatado
 * (2.450,90) — porque quem digita busca o que esta lendo na tela, mas quem cola
 * de uma planilha traz o numero cru.
 */
function textoDaLinha(linha, colunas) {
    const partes = [];
    for (const c of colunas) {
        const v = c.get ? c.get(linha) : linha[c.key];
        if (v === null || v === undefined || v === '') continue;
        partes.push(String(v));
        if (c.money) partes.push(fmt(v));
    }
    return normaliza(partes.join(' '));
}

// Visão mensal legada: parcelas do mês de referência + abertas vencidas,
// com as colunas que o analista usava no sistema antigo.
export const RecebimentosMensalView = ({ selectedEmpresa }) => {
    const hoje = new Date();
    // Competencia na URL: o mes navegado e compartilhavel e sobrevive ao F5.
    // parse: Number e obrigatorio — mudaMes() faz aritmetica com estes valores.
    const [ano, setAno] = useSearchParamState('ano', hoje.getFullYear(), { parse: Number });
    const [mes, setMes] = useSearchParamState('mes', hoje.getMonth() + 1, { parse: Number });
    const [empreendimentos, setEmpreendimentos] = useState([]);
    const [empreendimentoId, setEmpreendimentoId] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [editId, setEditId] = useState(null);
    const [baixa, setBaixa] = useState({ data_pagamento: '', valor: '', variacao: '', desconto: '' });
    const [salvando, setSalvando] = useState(false);

    useEffect(() => {
        if (!selectedEmpresa) return;
        const ac = new AbortController();
        fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`, { signal: ac.signal })
            .then(r => r.json())
            .then(d => setEmpreendimentos(Array.isArray(d) ? d : (d.data || [])))
            .catch(err => { if (err.name !== 'AbortError') setEmpreendimentos([]); });
        return () => ac.abort();
    }, [selectedEmpresa]);

    const mudaMes = (delta) => {
        let m = mes + delta, a = ano;
        if (m < 1) { m = 12; a -= 1; }
        if (m > 12) { m = 1; a += 1; }
        setMes(m); setAno(a);
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

    const pesquisar = async (signal) => {
        if (!selectedEmpresa) { alert('Selecione a empresa.'); return; }
        setLoading(true); setError(null);
        try {
            const emp = empreendimentoId ? `&empreendimento_id=${empreendimentoId}` : '';
            const res = await fetch(`${API_BASE}/api/vulcano/recebimentos-mensal?empresa_id=${selectedEmpresa}&ano=${ano}&mes=${mes}${emp}`, { signal });
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : res.statusText);
            setData(d);
        } catch (e) {
            if (e.name === 'AbortError') return;
            setError(e.message); setData(null);
        }
        finally { setLoading(false); }
    };

    // A competencia vem da URL, entao a consulta roda sozinha: sem isto um link
    // compartilhado abriria com os filtros certos e a tabela vazia. O filtro de
    // empreendimento nao entra aqui de proposito — ele nao esta na URL e continua
    // dependendo do botao Pesquisar.
    useEffect(() => {
        if (!selectedEmpresa || !ano || !mes) return;
        const ac = new AbortController();
        pesquisar(ac.signal);
        return () => ac.abort();
    }, [selectedEmpresa, ano, mes]);

    // Ordenacao na URL (?ord=&ordDir=): sobrevive ao F5, a troca de empresa (que
    // remonta a view) e vai junto num link compartilhado — mesma razao de ano/mes.
    const sort = useTableSort(COLUNAS, { persistKey: 'ord' });

    const colunasVisiveis = useMemo(
        () => COLUNAS.filter((c) => !c.when || c.when({ empreendimentoId })),
        [empreendimentoId]
    );

    // Busca em estado local, nao na URL — ao contrario de ano/mes/ord. Busca e
    // efemera (digita, olha, apaga) e com useSearchParamState cada tecla viraria
    // uma navegacao. E o que as outras telas do sistema fazem.
    const [busca, setBusca] = useState('');

    // Indice pesquisavel montado uma vez por resultado, nao a cada tecla.
    const linhasIndexadas = useMemo(() => {
        const base = data?.data || [];
        return base.map((linha) => ({ linha, texto: textoDaLinha(linha, colunasVisiveis) }));
    }, [data, colunasVisiveis]);

    // Todos os termos precisam casar: "maria 302" acha a Maria do apto 302, e nao
    // toda linha que tenha "maria" OU "302".
    const linhasFiltradas = useMemo(() => {
        const termos = termosDeBusca(busca);
        if (termos.length === 0) return data?.data || [];
        return linhasIndexadas
            .filter(({ texto }) => termos.every((t) => texto.includes(t)))
            .map(({ linha }) => linha);
    }, [linhasIndexadas, busca, data]);

    const buscando = termosDeBusca(busca).length > 0;

    // A coluna Empreendimento some quando um empreendimento e filtrado; se a
    // ordenacao estava nela, a ordem ficaria inexplicavel.
    useEffect(() => {
        if (empreendimentoId && sort.key === 'empreendimento') sort.clear();
    }, [empreendimentoId, sort]);

    const rows = sort.apply(linhasFiltradas);
    const totalDoMes = data?.data?.length || 0;

    /**
     * Totais: do backend quando nao ha busca, das linhas visiveis quando ha.
     *
     * Sem busca, preserva inclusive a mutacao otimista que a baixa faz em
     * data.totais. Com busca, `saldo_atual` precisa ser DEDUPLICADO por venda —
     * ele e atributo da venda repetido em cada parcela dela, entao somar a coluna
     * infla o numero (o backend faz a mesma deducao).
     */
    const tot = useMemo(() => {
        if (!buscando) return data?.totais || {};
        const soma = (campo) => linhasFiltradas.reduce((acc, r) => acc + (Number(r[campo]) || 0), 0);
        const saldoPorVenda = new Map();
        linhasFiltradas.forEach((r) => saldoPorVenda.set(r.venda_id, Number(r.saldo_atual) || 0));
        const arredonda = (v) => Math.round(v * 100) / 100;
        return {
            valor_parcela: arredonda(soma('valor_parcela')),
            desconto: arredonda(soma('desconto')),
            variacao: arredonda(soma('variacao')),
            total_pago: arredonda(soma('total_pago')),
            saldo_atual: arredonda([...saldoPorVenda.values()].reduce((a, b) => a + b, 0)),
        };
    }, [buscando, linhasFiltradas, data]);

    const corStatus = (s) => s === 'PAGO' ? 'var(--v-ok)' : s === 'VENCIDA' ? 'var(--v-accent)' : 'var(--v-text-muted)';

    // Reordenar sob uma edicao aberta faria a linha saltar; fechar o editor e a
    // mesma semantica do Escape que ja existe na linha.
    const ordenarPor = (key) => {
        if (editId !== null) setEditId(null);
        sort.toggle(key);
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
            // Com a tabela ordenada por Data Pagto ou Total Pago, a linha recem
            // baixada muda de lugar. Traz ela de volta ao campo de visao.
            if (sort.key) {
                requestAnimationFrame(() => {
                    document.getElementById(`row-${r.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                });
            }
        } catch (e) { alert(e.message); }
        finally { setSalvando(false); }
    };

    return (
        <div className="w-full flex flex-col gap-4 pt-4 pb-10 px-4">
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[var(--v-ok)]/10 border border-[var(--v-ok)]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <CalendarDays size={16} className="text-[var(--v-ok)]" />
                </div>
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase text-[var(--v-text-bold)]">Recebimentos — Mensal</h2>
                    <p className="text-[10px] text-[var(--v-text-ghost)] uppercase tracking-[0.25em]">Visão do analista · clique numa parcela em aberto para baixar (data, valor, variação, desconto)</p>
                </div>
            </div>

            <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl p-4 flex flex-wrap gap-3 items-end">
                <div className="min-w-64">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Empreendimento</label>
                    <select value={empreendimentoId} onChange={e => setEmpreendimentoId(e.target.value)}
                        className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] hover:border-[#333] text-[var(--v-text-bold)] text-[11px] px-2 py-2 rounded-lg outline-none">
                        <option value="">Todos</option>
                        {empreendimentos.map(e => <option key={e.id} value={e.id}>{e.id} — {e.nome}</option>)}
                    </select>
                </div>
                <div>
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Período</label>
                    <div className="flex items-center gap-1">
                        <button onClick={() => mudaMes(-1)} className="p-2 bg-[var(--v-bg)] border border-[var(--v-line)] rounded-lg text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)]"><ChevronLeft size={13} /></button>
                        <div className="px-3 py-2 bg-[var(--v-bg)] border border-[var(--v-line)] rounded-lg text-[var(--v-text-bold)] font-mono text-[12px] font-bold min-w-20 text-center">
                            {String(mes).padStart(2, '0')}/{ano}
                        </div>
                        <button onClick={() => mudaMes(1)} className="p-2 bg-[var(--v-bg)] border border-[var(--v-line)] rounded-lg text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)]"><ChevronRight size={13} /></button>
                    </div>
                </div>
                <button onClick={() => pesquisar()} disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--v-ok)]/15 border border-[var(--v-ok)]/30 text-[var(--v-ok)] text-[11px] font-bold uppercase tracking-wider hover:bg-[var(--v-ok)]/25 disabled:opacity-40">
                    {/* Rotulo em <span>: texto solto irmao de icone condicional vira no de referencia
                        do insertBefore e quebra o commit do React se algo (tradutor de pagina) tiver
                        embrulhado o texto. */}
                    {loading ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />} <span>Pesquisar</span>
                </button>
                <button onClick={sanearCronograma} disabled={saneando}
                    title="Marca como cobertas as parcelas antigas do cronograma que o Razão de recebimentos já pagou (elas somem das 'Previstas'). Mostra a prévia antes de gravar."
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/25 text-[var(--v-accent)] text-[11px] font-bold uppercase tracking-wider hover:bg-[var(--v-accent)]/20 disabled:opacity-40">
                    {saneando ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} <span>Sanear cronograma</span>
                </button>
                <div className="min-w-56">
                    <label htmlFor="busca-receb" className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">
                        Buscar na tabela
                    </label>
                    <div className="relative">
                        <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--v-text-ghost)] pointer-events-none" />
                        <input
                            id="busca-receb"
                            type="search"
                            value={busca}
                            onChange={(e) => setBusca(e.target.value)}
                            placeholder="Comprador, unidade, valor…"
                            className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] hover:border-[var(--v-border)] focus:border-[var(--v-accent)] text-[var(--v-text-bold)] text-[11px] pl-7 pr-7 py-2 rounded-lg outline-none placeholder-[var(--v-text-ghost)]"
                        />
                        {busca && (
                            <button onClick={() => setBusca('')} title="Limpar busca" aria-label="Limpar busca"
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--v-text-ghost)] hover:text-[var(--v-text-bold)]">
                                <X size={12} />
                            </button>
                        )}
                    </div>
                </div>
                {data && (
                    <div className="ml-auto text-right">
                        <div className="text-[9px] text-[var(--v-text-ghost)] uppercase tracking-widest">Recebido no mês</div>
                        <div className="text-[15px] font-black font-mono text-[var(--v-ok)]">{fmt(tot.total_pago)}</div>
                    </div>
                )}
            </div>

            {error && <div className="bg-red-950/30 text-red-400 border border-red-900/40 rounded-xl p-3 text-sm font-bold">{error}</div>}

            <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-[11px]">
                        <thead>
                            <tr className="bg-[var(--v-deep)]">
                                {colunasVisiveis.map((c) => (
                                    <Th key={c.key} right={c.right} sortKey={c.key} sort={sort} onSort={ordenarPor}>
                                        {c.label}
                                    </Th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((r) => {
                                const editando = editId === r.id;
                                const totalEdicao = Math.round(((parseFloat(baixa.valor) || 0) + (parseFloat(baixa.variacao) || 0) - (parseFloat(baixa.desconto) || 0)) * 100) / 100;
                                const inputCls = "w-24 bg-black border border-[var(--v-ok)]/40 text-white text-[11px] font-mono px-1.5 py-1 rounded outline-none text-right";
                                const onKey = (e) => { if (e.key === 'Enter') salvarBaixa(r); if (e.key === 'Escape') setEditId(null); };
                                // key por id, nunca por indice: com a tabela reordenavel o indice
                                // faria o React casar nos errados e o editId apontaria para outra
                                // linha. R.ID e PK e sempre existe.
                                return (
                                    <tr key={r.id} id={`row-${r.id}`}
                                        onClick={() => !editando && abrirBaixa(r)}
                                        className={`border-b border-[var(--v-line)] hover:bg-[var(--v-hover)] ${r.status !== 'PAGO' ? 'cursor-pointer' : ''} ${editando ? 'bg-[#101a10]' : ''}`}>
                                        <td className="px-3 py-2 font-mono text-[var(--v-text-muted)]">{r.venda_id}</td>
                                        <td className="px-3 py-2 font-mono text-[var(--v-text-muted)] whitespace-nowrap">{r.cpf_cnpj}</td>
                                        <td className="px-3 py-2 text-[var(--v-text-muted)] whitespace-nowrap max-w-56 truncate">{r.comprador}</td>
                                        <td className="px-3 py-2 text-[var(--v-text-muted)] max-w-44 truncate">{(r.unidade || '').replace(/\s+/g, ' ')}</td>
                                        {!empreendimentoId && <td className="px-3 py-2 text-[var(--v-text-muted)] max-w-40 truncate">{r.empreendimento}</td>}
                                        <td className="px-3 py-2 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.vlr_venda)}</td>
                                        <td className="px-3 py-2 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.saldo_anterior)}</td>
                                        <td className="px-3 py-2 font-mono text-[var(--v-ok)]">
                                            {editando ? (
                                                <input type="date" value={baixa.data_pagamento} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, data_pagamento: e.target.value }))}
                                                    onClick={e => e.stopPropagation()}
                                                    className="bg-[var(--v-deep)] border border-[var(--v-ok)]/40 text-[var(--v-text-bold)] text-[10px] font-mono px-1.5 py-1 rounded outline-none" />
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
                                        <td className="px-3 py-2 font-mono text-right text-[var(--v-text-muted)]">
                                            {editando ? (
                                                <input type="number" step="0.01" placeholder="0,00" value={baixa.desconto} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, desconto: e.target.value }))}
                                                    onClick={e => e.stopPropagation()} className={inputCls} />
                                            ) : fmt(r.desconto)}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-[var(--v-text-muted)]">
                                            {editando ? (
                                                <input type="number" step="0.01" placeholder="0,00" value={baixa.variacao} onKeyDown={onKey}
                                                    onChange={e => setBaixa(b => ({ ...b, variacao: e.target.value }))}
                                                    onClick={e => e.stopPropagation()} className={inputCls} />
                                            ) : fmt(r.variacao)}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-[var(--v-text-bold)] font-bold">
                                            {editando ? (
                                                <span className="flex items-center justify-end gap-2">
                                                    <span className="text-[var(--v-ok)]">{fmt(totalEdicao)}</span>
                                                    <button disabled={salvando}
                                                        onClick={e => { e.stopPropagation(); salvarBaixa(r); }}
                                                        className="px-2 py-1 rounded bg-[var(--v-ok)]/20 border border-[var(--v-ok)]/40 text-[var(--v-ok)] text-[9px] font-bold uppercase hover:bg-[var(--v-ok)]/30 disabled:opacity-40">
                                                        {salvando ? '...' : 'Baixar'}
                                                    </button>
                                                    <button onClick={e => { e.stopPropagation(); setEditId(null); }}
                                                        className="px-1.5 py-1 rounded border border-[var(--v-border)] text-[var(--v-text-muted)] text-[9px] font-bold uppercase hover:text-[var(--v-text-bold)]">✕</button>
                                                </span>
                                            ) : fmt(r.total_pago)}
                                        </td>
                                        <td className="px-3 py-2 font-mono text-right text-[var(--v-text-muted)]">{fmt(r.saldo_atual)}</td>
                                        <td className="px-3 py-2 font-mono whitespace-nowrap" style={{ color: r.status === 'VENCIDA' ? 'var(--v-err)' : 'var(--v-text-muted)' }}>{r.parcela}</td>
                                        <td className="px-3 py-2 text-[#8a7a68] whitespace-nowrap max-w-44 truncate">{r.obs}</td>
                                    </tr>
                                );
                            })}
                            {data && rows.length === 0 && (
                                <tr><td colSpan={colunasVisiveis.length} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                    {/* A mensagem antiga ("sem parcelas para o periodo") mentia
                                        quando o mes tinha linhas e era a busca que nao achava. */}
                                    {buscando ? (
                                        <span className="flex flex-col items-center gap-3">
                                            Nenhuma linha corresponde à busca.
                                            <button onClick={() => setBusca('')}
                                                className="px-3 py-1.5 rounded-lg border border-[var(--v-border)] text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)] text-[9px] font-bold uppercase tracking-widest">
                                                Limpar busca
                                            </button>
                                        </span>
                                    ) : 'Sem parcelas para o período selecionado.'}
                                </td></tr>
                            )}
                            {!data && !loading && (
                                <tr><td colSpan={colunasVisiveis.length} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                    Selecione o mês de referência e pesquise.
                                </td></tr>
                            )}
                        </tbody>
                        {rows.length > 0 && (
                            <tfoot>
                                <tr className="bg-[var(--v-deep)] border-t border-[var(--v-line)] font-mono font-bold">
                                    <td colSpan={colunasVisiveis.findIndex(c => c.key === 'valor_parcela')} className="px-3 py-2.5 text-[9px] uppercase tracking-widest text-[var(--v-text-ghost)]">
                                        {buscando
                                            ? <>Totais <span className="text-[var(--v-accent)]">(filtrado)</span> · {rows.length} de {totalDoMes} parcelas</>
                                            : <>Totais · {rows.length} parcelas</>}
                                    </td>
                                    <td className="px-3 py-2.5 text-right text-[var(--v-accent)]">{fmt(tot.valor_parcela)}</td>
                                    <td className="px-3 py-2.5 text-right text-[var(--v-text-muted)]">{fmt(tot.desconto)}</td>
                                    <td className="px-3 py-2.5 text-right text-[var(--v-text-muted)]">{fmt(tot.variacao)}</td>
                                    <td className="px-3 py-2.5 text-right text-[var(--v-ok)]">{fmt(tot.total_pago)}</td>
                                    <td className="px-3 py-2.5 text-right text-[var(--v-text-muted)]">{fmt(tot.saldo_atual)}</td>
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
