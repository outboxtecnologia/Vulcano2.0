import React, { useEffect, useState } from 'react';
import {
    AlertTriangle, CheckCircle2, ListPlus, Loader2, Play, RefreshCw, ShieldAlert,
} from 'lucide-react';
import { API_BASE } from './apiBase';
import { useSearchParamState } from './hooks/useSearchParamState';
import { useTableSort } from './hooks/useTableSort';
import SortIcon from './components/SortIcon';

const fmt = (v) => (v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const fmtInt = (v) => (v ?? 0).toLocaleString('pt-BR');

// Copia do Th de RecebimentosMensalView: sem componente de tabela compartilhado
// no projeto, o cabecalho ordenavel e replicado por view.
const Th = ({ children, right, sortKey, sort, onSort }) => {
    const base = `px-3 py-2 text-[9px] uppercase tracking-widest font-bold whitespace-nowrap ${right ? 'text-right' : 'text-left'}`;
    if (!sortKey || !sort) return <th className={`${base} text-[var(--v-text-faint)]`}>{children}</th>;
    const { sortable, active, dir, ariaSort } = sort.headerProps(sortKey);
    if (!sortable) return <th className={`${base} text-[var(--v-text-faint)]`}>{children}</th>;
    return (
        <th className={base} aria-sort={ariaSort}>
            <button
                type="button"
                onClick={() => onSort(sortKey)}
                className={`group w-full inline-flex items-center gap-1 select-none uppercase tracking-widest cursor-pointer transition-colors focus-visible:outline-1 focus-visible:outline-[var(--v-accent)] ${right ? 'justify-end' : 'justify-start'} ${active ? 'text-[var(--v-accent)]' : 'text-[var(--v-text-faint)] hover:text-[var(--v-text-muted)]'}`}
                aria-label={`${children}${active ? (dir === 'asc' ? ' — ordenado crescente' : ' — ordenado decrescente') : ''}; ativar para ${active ? 'inverter' : 'ordenar'}`}
            >
                {children}
                <SortIcon active={active} dir={dir} />
            </button>
        </th>
    );
};

const COLUNAS = [
    { key: 'empresa',  label: 'Empresa',     type: 'number' },
    { key: 'empreendimento', label: 'Empreendimento', type: 'text' },
    { key: 'idvenda',  label: 'Venda',       type: 'number' },
    { key: 'prazo_id', label: 'Prazo',       type: 'number' },
    { key: 'data',     label: 'Vencimento',  type: 'date' },
    { key: 'parcela',  label: 'Competência', type: 'parcela' },
    { key: 'valor',    label: 'Valor',       type: 'number', right: true, firstDir: 'desc' },
    { key: 'obs',      label: 'Descrição',   type: 'text' },
];

const MODOS = {
    A: {
        titulo: 'Vendas sem nenhuma parcela',
        ajuda: 'Gera a matriz inteira de prazos das vendas que não têm nenhuma linha em Receber. Venda que já tem qualquer parcela não é tocada.',
    },
    B: {
        titulo: 'Parcelas faltantes (órfãs)',
        ajuda: 'Repara buracos: gera prazos sem linha correspondente, inclusive em vendas já lançadas. Inclui tudo que o modo A faria.',
    },
};

const Card = ({ label, valor, cor }) => (
    <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl px-4 py-3">
        <div className="text-[9px] text-[var(--v-text-ghost)] uppercase tracking-widest">{label}</div>
        <div className="text-[15px] font-black font-mono mt-1" style={cor ? { color: cor } : undefined}>{valor}</div>
    </div>
);

export const GeracaoParcelasView = ({ selectedEmpresa }) => {
    const [modo, setModo] = useSearchParamState('modo', 'A');
    const [todas, setTodas] = useSearchParamState('todas', '0');
    const [emp, setEmp] = useSearchParamState('emp', '');
    const [de, setDe] = useSearchParamState('de', '');
    const [ate, setAte] = useSearchParamState('ate', '');
    const [limite, setLimite] = useState('');
    const [empreendimentos, setEmpreendimentos] = useState([]);

    const [previa, setPrevia] = useState(null);
    const [simulando, setSimulando] = useState(false);
    const [erro, setErro] = useState(null);
    const [executando, setExecutando] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [confirmar, setConfirmar] = useState(false);

    const sort = useTableSort(COLUNAS, { persistKey: 'ord' });
    const todasEmpresas = todas === '1';

    // Lista pela rota "gorda" de proposito: /api/empreendimentos/basico filtra
    // ATIVO = 'S', e obra concluida e justamente a que costuma ter prazos antigos
    // por materializar — o caso que esta tela existe para reparar.
    useEffect(() => {
        if (!selectedEmpresa) return undefined;
        const ac = new AbortController();
        fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`, { signal: ac.signal })
            .then((res) => res.json())
            .then((d) => setEmpreendimentos(Array.isArray(d) ? d : []))
            .catch((e) => { if (e.name !== 'AbortError') setEmpreendimentos([]); });
        return () => ac.abort();
    }, [selectedEmpresa]);

    const empId = todasEmpresas || !emp ? null : Number(emp);
    const empSelecionado = empId ? empreendimentos.find((e) => e.id === empId) : null;

    const payload = (dryRun) => ({
        modo,
        empresa_id: todasEmpresas ? null : Number(selectedEmpresa),
        empreendimento_id: empId,
        // O backend ignora datas no modo A, mas nao mandar deixa a intencao clara.
        data_inicio: modo === 'B' && de ? de : null,
        data_fim: modo === 'B' && ate ? ate : null,
        limite: limite ? Number(limite) : null,
        dry_run: dryRun,
    });

    // Qualquer mudanca de filtro invalida a previa: confirmar uma previa de outro
    // filtro grava o que o operador nao viu.
    const invalidar = (setter) => (valor) => {
        setter(valor);
        setPrevia(null);
        setResultado(null);
        setErro(null);
    };

    // Marcar "todas as empresas" desabilita o seletor de obra; deixar o id
    // pendurado na URL sob um campo desabilitado e o tipo de estado invisivel
    // que faz gravar o lote errado na proxima visita.
    const mudarAbrangencia = (marcado) => {
        if (marcado) setEmp('');
        invalidar(setTodas)(marcado ? '1' : '0');
    };

    const simular = async (signal) => {
        setSimulando(true);
        setErro(null);
        try {
            const res = await fetch(`${API_BASE}/api/vulcano/gerar-parcelas`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload(true)),
                signal,
            });
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : res.statusText);
            setPrevia(d);
        } catch (e) {
            if (e.name === 'AbortError') return;
            setErro(e.message);
            setPrevia(null);
        } finally {
            setSimulando(false);
        }
    };

    // Sem AbortController aqui de proposito: uma execucao no teto leva minutos e
    // abortar pelo cliente deixaria a carga pela metade sem ninguem saber onde parou.
    const executar = async () => {
        setConfirmar(false);
        setExecutando(true);
        setErro(null);
        try {
            const res = await fetch(`${API_BASE}/api/vulcano/gerar-parcelas`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload(false)),
            });
            const d = await res.json();
            if (!res.ok) throw new Error(typeof d.detail === 'string' ? d.detail : res.statusText);
            setResultado(d);
            // Re-simula: no modo A o total tem que cair para zero. E a prova de que gravou.
            await simular();
        } catch (e) {
            alert(e.message);
        } finally {
            setExecutando(false);
        }
    };

    const linhas = sort.apply(previa?.preview || []);
    const podeExecutar = previa && previa.total_parcelas > 0 && !previa.acima_do_teto && !executando && !simulando;

    return (
        <div className="w-full flex flex-col gap-4 pt-4 pb-10 px-4">
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <ListPlus size={16} className="text-[var(--v-accent)]" />
                </div>
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase text-[var(--v-text-bold)]">Geração de Parcelas</h2>
                    <p className="text-[10px] text-[var(--v-text-ghost)] uppercase tracking-[0.25em]">
                        Materializa prazos de venda em Receber · simule, confira e grave · o modo B inclui o modo A
                    </p>
                </div>
            </div>

            <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl p-4 flex flex-wrap gap-3 items-end">
                <div className="min-w-72">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Critério</label>
                    <select value={modo} onChange={(e) => invalidar(setModo)(e.target.value)}
                        className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] hover:border-[#333] text-[var(--v-text-bold)] text-[11px] px-2 py-2 rounded-lg outline-none">
                        <option value="A">A — {MODOS.A.titulo}</option>
                        <option value="B">B — {MODOS.B.titulo}</option>
                    </select>
                </div>

                <div>
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Abrangência</label>
                    <label className="flex items-center gap-2 px-3 py-2 bg-[var(--v-bg)] border border-[var(--v-line)] rounded-lg cursor-pointer">
                        <input type="checkbox" checked={todasEmpresas}
                            onChange={(e) => mudarAbrangencia(e.target.checked)} />
                        <span className="text-[11px] font-bold text-[var(--v-text-bold)]">
                            {todasEmpresas ? 'Todas as empresas' : `Empresa ${selectedEmpresa}`}
                        </span>
                    </label>
                </div>

                <div className="min-w-72"
                    title={todasEmpresas ? 'O empreendimento pertence a uma empresa só — desmarque “todas as empresas” para recortar por obra.' : undefined}>
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">
                        {/* Rotulo em <span>: como texto solto ele seria irmao do sufixo condicional,
                            e o React o usaria como referencia ao inserir/remover aquele span. Se um
                            tradutor de pagina embrulhar o texto, o commit estoura com NotFoundError. */}
                        <span>Empreendimento </span>{todasEmpresas && <span className="text-[var(--v-text-faint)]">(só por empresa)</span>}
                    </label>
                    <select value={todasEmpresas ? '' : emp} disabled={todasEmpresas}
                        onChange={(e) => invalidar(setEmp)(e.target.value)}
                        className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] hover:border-[#333] text-[var(--v-text-bold)] text-[11px] px-2 py-2 rounded-lg outline-none disabled:opacity-40">
                        <option value="">Todos os empreendimentos</option>
                        {empreendimentos.map((e) => (
                            <option key={e.id} value={String(e.id)}>{e.id} — {e.nome}</option>
                        ))}
                    </select>
                </div>

                <div title={modo === 'A' ? 'No modo A a venda recebe a matriz inteira de prazos — recortar por data deixaria a venda pela metade.' : undefined}>
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">
                        <span>Vencimento de / até </span>{modo === 'A' && <span className="text-[var(--v-text-faint)]">(só no modo B)</span>}
                    </label>
                    <div className="flex items-center gap-1">
                        <input type="date" value={de} disabled={modo === 'A'}
                            onChange={(e) => invalidar(setDe)(e.target.value)}
                            className="bg-[var(--v-bg)] border border-[var(--v-line)] text-[var(--v-text-bold)] text-[11px] px-2 py-2 rounded-lg outline-none disabled:opacity-40" />
                        <input type="date" value={ate} disabled={modo === 'A'}
                            onChange={(e) => invalidar(setAte)(e.target.value)}
                            className="bg-[var(--v-bg)] border border-[var(--v-line)] text-[var(--v-text-bold)] text-[11px] px-2 py-2 rounded-lg outline-none disabled:opacity-40" />
                    </div>
                </div>

                <div className="w-28">
                    <label className="block text-[9px] uppercase tracking-[0.2em] text-[var(--v-text-ghost)] mb-1.5 font-bold">Limite</label>
                    <input type="number" min="1" value={limite} placeholder="todas"
                        onChange={(e) => { setLimite(e.target.value); setPrevia(null); setResultado(null); }}
                        className="w-full bg-[var(--v-bg)] border border-[var(--v-line)] text-[var(--v-text-bold)] text-[11px] px-2 py-2 rounded-lg outline-none placeholder-[var(--v-text-ghost)]" />
                </div>

                <button onClick={() => simular()} disabled={simulando || executando}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--v-info)]/15 border border-[var(--v-info)]/30 text-[var(--v-info)] text-[11px] font-bold uppercase tracking-wider hover:bg-[var(--v-info)]/25 disabled:opacity-40">
                    {simulando ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />} <span>Simular</span>
                </button>
            </div>

            <p className="text-[10px] text-[var(--v-text-muted)] -mt-2 px-1">{MODOS[modo].ajuda}</p>

            {erro && <div className="bg-red-950/30 text-red-400 border border-red-900/40 rounded-xl p-3 text-sm font-bold">{erro}</div>}

            {previa?.acima_do_teto && (
                <div className="bg-[var(--v-warn-hi)]/10 border border-[var(--v-warn-hi)]/40 text-[var(--v-warn-hi)] rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle size={18} className="shrink-0 mt-0.5" />
                    <div>
                        <div className="font-bold text-[12px]">{previa.mensagem}</div>
                        <div className="text-[10px] mt-1 opacity-80">
                            Desmarque “todas as empresas” para gravar uma de cada vez, ou recorte por vencimento. A tabela por empresa abaixo mostra quais cabem no teto de {fmtInt(previa.teto)}.
                        </div>
                    </div>
                </div>
            )}

            {previa && previa.total_parcelas > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                    <Card label="Vendas alvo" valor={fmtInt(previa.total_vendas)} />
                    <Card label="Parcelas a gerar" valor={fmtInt(previa.total_parcelas)} cor="var(--v-accent)" />
                    <Card label="Valor total" valor={fmt(previa.valor_total)} />
                    <Card label="Empresas" valor={fmtInt(previa.empresas_afetadas)} />
                    <Card label="Vencimentos" valor={`${previa.venc_min || '—'} · ${previa.venc_max || '—'}`} />
                    <Card label="Período bloqueado"
                        valor={previa.bloqueadas == null ? '—' : fmtInt(previa.bloqueadas)}
                        cor={previa.bloqueadas ? 'var(--v-warn-hi)' : undefined} />
                </div>
            )}

            {previa?.bloqueadas > 0 && (
                <div className="bg-[var(--v-warn-hi)]/10 border border-[var(--v-warn-hi)]/30 text-[var(--v-warn-hi)] rounded-xl p-3 flex items-center gap-3 text-[11px] font-bold">
                    <ShieldAlert size={15} className="shrink-0" />
                    {fmtInt(previa.bloqueadas)} parcelas vencem dentro de período já bloqueado e vão ser rejeitadas pelo ERP. O restante do lote grava normalmente.
                </div>
            )}

            {previa && todasEmpresas && previa.por_empresa?.length > 1 && (
                <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl overflow-hidden">
                    <div className="px-4 py-2 border-b border-[var(--v-line)] text-[9px] uppercase tracking-widest text-[var(--v-text-ghost)] font-bold">
                        Por empresa — {previa.por_empresa.length} empresas
                    </div>
                    <div className="overflow-x-auto max-h-64 overflow-y-auto">
                        <table className="w-full text-[11px]">
                            <thead className="sticky top-0 bg-[var(--v-deep)]">
                                <tr>
                                    <Th>Empresa</Th><Th right>Vendas</Th><Th right>Parcelas</Th>
                                    <Th right>Valor</Th><Th>Vencimentos</Th>
                                </tr>
                            </thead>
                            <tbody>
                                {previa.por_empresa.map((e) => (
                                    <tr key={e.empresa} className="border-b border-[var(--v-line)] hover:bg-[var(--v-hover)]">
                                        <td className="px-3 py-2 font-mono">{e.empresa}</td>
                                        <td className="px-3 py-2 font-mono text-right">{fmtInt(e.vendas)}</td>
                                        <td className={`px-3 py-2 font-mono text-right ${e.parcelas > previa.teto ? 'text-[var(--v-warn-hi)]' : ''}`}>{fmtInt(e.parcelas)}</td>
                                        <td className="px-3 py-2 font-mono text-right">{fmt(e.valor)}</td>
                                        <td className="px-3 py-2 font-mono text-[var(--v-text-muted)]">{e.venc_min} · {e.venc_max}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            <div className="bg-[var(--v-deep)] border border-[var(--v-line)] rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-[11px]">
                        <thead>
                            <tr className="bg-[var(--v-deep)]">
                                {COLUNAS.map((c) => (
                                    <Th key={c.key} right={c.right} sortKey={c.key} sort={sort} onSort={sort.toggle}>{c.label}</Th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {linhas.map((r) => (
                                <tr key={r.prazo_id} className="border-b border-[var(--v-line)] hover:bg-[var(--v-hover)]">
                                    <td className="px-3 py-2 font-mono">{r.empresa}</td>
                                    <td className="px-3 py-2 max-w-48 truncate text-[var(--v-text-muted)]" title={r.empreendimento || undefined}>
                                        {r.empreendimento || '—'}
                                    </td>
                                    <td className="px-3 py-2 font-mono">{r.idvenda}</td>
                                    <td className="px-3 py-2 font-mono text-[var(--v-text-muted)]">{r.prazo_id}</td>
                                    <td className="px-3 py-2 font-mono">
                                        <span>{r.data}</span>
                                        {r.bloqueada && <span className="ml-2 text-[8px] font-black uppercase tracking-widest text-[var(--v-warn-hi)]">bloqueada</span>}
                                    </td>
                                    <td className="px-3 py-2 font-mono">{r.parcela}</td>
                                    <td className="px-3 py-2 font-mono text-right">{fmt(r.valor)}</td>
                                    <td className="px-3 py-2 text-[var(--v-text-muted)]">{r.obs}</td>
                                </tr>
                            ))}
                            {previa && previa.total_parcelas === 0 && (
                                <tr><td colSpan={COLUNAS.length} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                    Nenhuma parcela a gerar — o banco já está completo para este filtro.
                                </td></tr>
                            )}
                            {!previa && !simulando && (
                                <tr><td colSpan={COLUNAS.length} className="py-16 text-center text-[var(--v-text-ghost)] text-[10px] uppercase tracking-widest">
                                    Escolha o critério e clique em Simular.
                                </td></tr>
                            )}
                        </tbody>
                        {previa && previa.total_parcelas > 0 && (
                            <tfoot>
                                <tr className="bg-[var(--v-deep)] border-t border-[var(--v-line)] font-mono font-bold">
                                    <td colSpan={COLUNAS.length} className="px-3 py-2.5 text-[9px] uppercase tracking-widest text-[var(--v-text-ghost)]">
                                        {previa.preview_truncado
                                            ? `Amostra de ${fmtInt(linhas.length)} de ${fmtInt(previa.total_parcelas)} parcelas`
                                            : `${fmtInt(previa.total_parcelas)} parcelas`}
                                        {' · Total '}
                                        <span className="text-[var(--v-accent)]">{fmt(previa.valor_total)}</span>
                                    </td>
                                </tr>
                            </tfoot>
                        )}
                    </table>
                </div>

                {(podeExecutar || resultado) && (
                    <div className="border-t border-[var(--v-line)] px-4 py-3 flex items-center gap-4 flex-wrap">
                        {podeExecutar && (
                            <button onClick={() => setConfirmar(true)} disabled={executando}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--v-accent)]/15 border border-[var(--v-accent)]/40 text-[var(--v-accent)] text-[10px] font-black uppercase tracking-widest hover:bg-[var(--v-accent)]/25 disabled:opacity-40">
                                {executando ? <RefreshCw size={12} className="animate-spin" /> : <ListPlus size={12} />}
                                {executando ? 'Gravando…' : `Gerar ${fmtInt(previa.total_parcelas)} parcelas`}
                            </button>
                        )}
                        {resultado && (
                            <div className="flex items-center gap-2 text-[10px] font-bold flex-wrap">
                                <CheckCircle2 size={13} className="text-[var(--v-ok)]" />
                                <span className="text-[var(--v-ok)]">{fmtInt(resultado.inseridos)} parcelas gravadas.</span>
                                {resultado.erros > 0 && <span className="text-[var(--v-accent)]">{fmtInt(resultado.erros)} com erro.</span>}
                                {resultado.log_rollback && (
                                    <span className="text-[var(--v-text-faint)] text-[9px] font-mono">log: {resultado.log_rollback}</span>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {resultado?.erros_detalhe?.length > 0 && (
                <div className="bg-[var(--v-deep)] border border-[var(--v-accent)]/30 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 border-b border-[var(--v-line)] text-[9px] uppercase tracking-widest text-[var(--v-accent)] font-bold">
                        Erros — primeiros {resultado.erros_detalhe.length} de {fmtInt(resultado.erros)}
                    </div>
                    <div className="max-h-56 overflow-y-auto">
                        {resultado.erros_detalhe.map((e) => (
                            <div key={e.prazo_id} className="px-4 py-2 border-b border-[var(--v-line)] text-[10px] font-mono text-[var(--v-text-muted)]">
                                <span className="text-[var(--v-text-bold)]">venda {e.idvenda} · prazo {e.prazo_id}</span> — {e.erro}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {confirmar && previa && (
                <div className="fixed inset-0 bg-[var(--v-overlay)] backdrop-blur-sm flex items-center justify-center z-[100] p-6">
                    <div className="w-full max-w-md rounded-xl shadow-2xl flex flex-col p-6"
                        style={{ background: 'var(--v-shell)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                        role="dialog" aria-modal="true">
                        <h3 className="text-red-500 text-lg font-black uppercase tracking-widest flex items-center gap-3 mb-4">
                            <AlertTriangle size={22} /> Confirmar geração
                        </h3>
                        <p className="text-[12px] mb-2" style={{ color: 'var(--v-text-muted)' }}>
                            Serão gravadas <strong style={{ color: 'var(--v-text-bold)' }}>{fmtInt(previa.total_parcelas)} parcelas</strong> de{' '}
                            <strong style={{ color: 'var(--v-text-bold)' }}>{fmtInt(previa.total_vendas)} vendas</strong>, totalizando{' '}
                            <strong style={{ color: 'var(--v-text-bold)' }}>{fmt(previa.valor_total)}</strong>, em{' '}
                            {todasEmpresas ? 'todas as empresas' : `na empresa ${selectedEmpresa}`}
                            {empId && (
                                <>, apenas no empreendimento{' '}
                                    <strong style={{ color: 'var(--v-text-bold)' }}>
                                        {empSelecionado ? `${empSelecionado.id} — ${empSelecionado.nome}` : empId}
                                    </strong>
                                </>
                            )}.
                        </p>
                        <p className="text-[11px] mb-6" style={{ color: 'var(--v-text-muted)' }}>
                            Modo {modo} — {MODOS[modo].titulo}. Todas entram <strong>em aberto</strong> (total pago zero)
                            {previa.bloqueadas > 0 && <>, e {fmtInt(previa.bloqueadas)} devem ser rejeitadas por período bloqueado</>}.
                            A gravação pode levar alguns minutos e <span className="text-red-500 font-bold">não deve ser interrompida</span>.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setConfirmar(false)}
                                className="px-4 py-2 text-[11px] font-bold uppercase tracking-widest rounded text-[var(--v-text-muted)] hover:text-[var(--v-text-bold)]">
                                Cancelar
                            </button>
                            <button onClick={executar}
                                className="px-6 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-900/50 text-red-500 rounded text-[11px] font-bold uppercase tracking-widest">
                                Gerar parcelas
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
