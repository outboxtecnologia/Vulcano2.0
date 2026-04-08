import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  TrendingUp, Zap, AlertTriangle, Building2,
  ChevronDown, ChevronUp, RefreshCw
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const fmt = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 }).format(v || 0);
const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// ── helpers de período ───────────────────────────────────────────────────────
function gerarCompetencias(de, ate) {
  const res = [];
  let [y, m] = de.split('-').map(Number);
  const [ey, em] = ate.split('-').map(Number);
  while (y < ey || (y === ey && m <= em)) {
    res.push(`${y}-${String(m).padStart(2, '0')}`);
    m++; if (m > 12) { m = 1; y++; }
  }
  return res;
}
const labelMes = (comp) => {
  const [y, m] = comp.split('-').map(Number);
  return `${MESES_ABREV[m - 1]}/${String(y).slice(2)}`;
};

// ── classificação de conta virtual por tipo ──────────────────────────────────
// Os históricos injetados pelo backend seguem padrões reconhecíveis
const GRUPOS_VIRTUAL = [
  {
    key: 'receita',
    label: 'Receita Societária (POC)',
    cor: '#34c759',
    descricao: 'Receita auferida calculada com base no percentual de conclusão (POC)',
    test: (nome) => /receita|auferida/i.test(nome)
  },
  {
    key: 'custo',
    label: 'Custo Econômico (POC)',
    cor: '#ff4d00',
    descricao: 'CMV e custo de obra proporcional à fração POC e VGV vendido',
    test: (nome) => /custo poc|contrapartida reccusto/i.test(nome)
  },
  {
    key: 'clientes',
    label: 'Clientes / Adiantamento',
    cor: '#a259ff',
    descricao: 'Variação de clientes e adiantamentos de clientes sobre contratos',
    test: (nome) => /cliente|adiantamento|faturamento direito/i.test(nome)
  },
  {
    key: 'caixa',
    label: 'Caixa / Bancos',
    cor: '#30d158',
    descricao: 'Entradas de caixa por recebimentos de parcelas vendidas',
    test: (nome) => /caixa|recebimento caixa/i.test(nome)
  },
  {
    key: 'trib_dif',
    label: 'Tributos Diferidos / Antecipados',
    cor: '#ffcc00',
    descricao: 'Diferenças entre base caixa e base DRE (POC) — antecipados e diferidos',
    test: (nome) => /diferido|antecipado|passivo tributo|constituição adiant/i.test(nome)
  },
  {
    key: 'trib_dre',
    label: 'Despesa Tributária DRE',
    cor: '#ff9f0a',
    descricao: 'IRPJ, CSLL, PIS, COFINS, RET — pelo critério econômico (base POC)',
    test: (nome) => /despesa tribut|passivo.darf|darf exig/i.test(nome)
  },
  {
    key: 'outros',
    label: 'Outras Contas Societárias',
    cor: '#636366',
    descricao: 'Demais lançamentos gerados pelo motor societário',
    test: () => true
  },
];

function grupoVirtual(histNome) {
  for (const g of GRUPOS_VIRTUAL) if (g.test(histNome || '')) return g;
  return GRUPOS_VIRTUAL[GRUPOS_VIRTUAL.length - 1];
}

// ── Linha de conta na tabela ─────────────────────────────────────────────────
function ContaRow({ contaId, contaNome, grupo, competencias, dadosPorMes }) {
  const [open, setOpen] = useState(false);

  // Para cada mês, somamos os movimentos desta conta (pode ter múltiplas unidades)
  const movPorMes = {};
  let saldoAnt = 0;
  let saldoFinal = 0;
  let primeiroMes = true;

  competencias.forEach(comp => {
    const registros = (dadosPorMes[comp] || []);
    const match = registros.find(r => String(r.conta) === String(contaId));
    if (match) {
      if (primeiroMes) {
        saldoAnt = match.saldo_anterior || 0;
        primeiroMes = false;
      }
      movPorMes[comp] = match.movimento_liquido || 0;
    } else {
      movPorMes[comp] = null; // sem dado para esse mês
    }
  });

  saldoFinal = saldoAnt + Object.values(movPorMes).reduce((s, v) => s + (v || 0), 0);

  // Detalhes do último mês com dado
  const ultimoMesComDado = [...competencias].reverse().find(c => dadosPorMes[c]?.find(r => String(r.conta) === String(contaId)));
  const detalhes = ultimoMesComDado
    ? (dadosPorMes[ultimoMesComDado].find(r => String(r.conta) === String(contaId))?.detalhes || [])
    : [];

  return (
    <>
      <tr
        className="border-b border-[#1a1a1a] hover:bg-[#141414] cursor-pointer transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        {/* Conta */}
        <td className="px-3 py-2.5 sticky left-0 z-10 bg-[#0d0d0d] min-w-[230px]">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] font-black shrink-0" style={{ color: grupo.cor }}>{contaId}</span>
            <span className="text-[10px] text-[#666] truncate" title={contaNome}>{contaNome}</span>
            {detalhes.length > 0 && (open ? <ChevronUp size={9} className="text-[#444] shrink-0"/> : <ChevronDown size={9} className="text-[#444] shrink-0"/>)}
          </div>
        </td>

        {/* Saldo anterior */}
        <td className="px-3 py-2.5 text-right font-mono text-[11px] text-[#555] whitespace-nowrap">{fmt(saldoAnt)}</td>

        {/* Movimento por mês */}
        {competencias.map(comp => {
          const v = movPorMes[comp];
          return (
            <td key={comp} className="px-3 py-2.5 text-right font-mono text-[11px] whitespace-nowrap">
              {v === null ? <span className="text-[#252525]">—</span>
               : v === 0  ? <span className="text-[#333]">-</span>
               : <span style={{ color: v > 0 ? '#34c759' : '#ff4d00' }}>
                   {v > 0 ? '+' : ''}{fmt(v)}
                 </span>}
            </td>
          );
        })}

        {/* Saldo final */}
        <td className="px-3 py-2.5 text-right font-mono text-sm font-black text-white whitespace-nowrap">{fmt(saldoFinal)}</td>
      </tr>

      {/* Detalhes */}
      {open && detalhes.length > 0 && (
        <tr>
          <td colSpan={competencias.length + 3} className="p-0 bg-[#070707]">
            <div className="px-4 py-1 text-[9px] font-black uppercase tracking-widest text-[#444] border-b border-[#111]">
              Lançamentos analíticos — {labelMes(ultimoMesComDado)}
            </div>
            <table className="w-full text-[10px] border-collapse">
              <tbody>
                {detalhes.map((d, i) => (
                  <tr key={i} className="border-b border-[#0e0e0e] hover:bg-[#0a0a0a]">
                    <td className="px-5 py-1.5 font-mono text-[#444] whitespace-nowrap w-24">{d.data}</td>
                    <td className="px-3 py-1.5 text-[#555] truncate max-w-[460px]" title={d.historico}>{d.historico}</td>
                    <td className="px-3 py-1.5 text-center font-bold w-8" style={{ color: d.natureza === 'D' ? '#34c759' : '#ff9f0a' }}>{d.natureza}</td>
                    <td className="px-5 py-1.5 text-right font-mono text-[#888] whitespace-nowrap w-32">{fmt(d.valor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </td>
        </tr>
      )}
    </>
  );
}

// ── MAIN VIEW ────────────────────────────────────────────────────────────────
export const ContabilizacoesView = ({ selectedEmpresa }) => {
  const now = new Date();
  const mesAtual = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

  const [periodoInicio, setPeriodoInicio] = useState(mesAtual);
  const [periodoFim,    setPeriodoFim]    = useState(mesAtual);
  const [filtroEmpId,   setFiltroEmpId]   = useState('');
  // empreendimentos para o select (carregados na montagem)
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [empsLoading,     setEmpsLoading]     = useState(false);

  // dados por competência: { 'YYYY-MM': [ conta_virtual ] }
  const [dadosPorMes, setDadosPorMes] = useState({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  // ── Carrega lista de empreendimentos disponíveis na montagem ──────────────
  useEffect(() => {
    if (!selectedEmpresa) return;
    setEmpsLoading(true);
    fetch(`${API_BASE}/api/empreendimentos/basico?empresa_id=${selectedEmpresa}`)
      .then(r => r.json())
      .then(j => { setEmpreendimentos(j.empreendimentos || []); setEmpsLoading(false); })
      .catch(() => setEmpsLoading(false));
  }, [selectedEmpresa]);

  // competências do intervalo selecionado
  const competencias = useMemo(() => {
    try { return gerarCompetencias(periodoInicio, periodoFim); }
    catch { return [periodoInicio]; }
  }, [periodoInicio, periodoFim]);

  const periodoValido = competencias.length <= 18;

  // ── Busca dados em paralelo para cada mês ────────────────────────────────
  const fetchTudo = useCallback(async () => {
    if (!selectedEmpresa || !periodoValido) return;
    setLoading(true);
    setError('');
    const novos = {};
    try {
      await Promise.all(competencias.map(async (comp) => {
        const [ano, mes] = comp.split('-').map(Number);
        let url = `${API_BASE}/api/questor/contabilizacoes?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}`;
        if (filtroEmpId) url += `&empreendimento_id=${filtroEmpId}`;
        const resp = await fetch(url);
        const json = await resp.json();
        // Consolida contas_virtuais de todos os empreendimentos da resposta
        const contasMerged = {};
        (json.data || []).forEach(emp => {
          (emp.contas_virtuais || []).forEach(c => {
            const key = String(c.conta);
            if (!contasMerged[key]) {
              contasMerged[key] = { ...c, detalhes: [...(c.detalhes || [])] };
            } else {
              contasMerged[key].saldo_anterior  = (contasMerged[key].saldo_anterior  || 0) + (c.saldo_anterior  || 0);
              contasMerged[key].movimento_debito = (contasMerged[key].movimento_debito || 0) + (c.movimento_debito || 0);
              contasMerged[key].movimento_credito = (contasMerged[key].movimento_credito || 0) + (c.movimento_credito || 0);
              contasMerged[key].movimento_liquido = (contasMerged[key].movimento_liquido || 0) + (c.movimento_liquido || 0);
              contasMerged[key].saldo_final = (contasMerged[key].saldo_final || 0) + (c.saldo_final || 0);
              contasMerged[key].detalhes.push(...(c.detalhes || []));
            }
          });
        });
        novos[comp] = Object.values(contasMerged);
      }));
      setDadosPorMes(novos);
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  }, [selectedEmpresa, competencias, filtroEmpId]);

  // ── index de contas (conta → { nome, grupoVirtual }) ─────────────────────
  const contasIndex = useMemo(() => {
    const map = {};
    Object.values(dadosPorMes).forEach(lista => {
      lista.forEach(c => {
        if (!map[c.conta]) {
          // O nome da conta vem do plano, mas os detalhes têm histórico descritivo
          const primeiroHist = (c.detalhes || [])[0]?.historico || c.nome || '';
          map[c.conta] = {
            conta:  c.conta,
            nome:   c.nome || `Conta ${c.conta}`,
            grupo:  grupoVirtual(primeiroHist),
            saldoAnt: c.saldo_anterior || 0
          };
        }
      });
    });
    return map;
  }, [dadosPorMes]);

  // ── Agrupa contas por grupo ───────────────────────────────────────────────
  const grupos = useMemo(() => {
    const gMap = {};
    Object.values(contasIndex).forEach(c => {
      const gk = c.grupo.key;
      if (!gMap[gk]) gMap[gk] = { grupo: c.grupo, contas: [] };
      gMap[gk].contas.push(c);
    });
    return Object.values(gMap);
  }, [contasIndex]);

  // totais globais por mês
  const totaisPorMes = useMemo(() => {
    const t = {};
    competencias.forEach(comp => {
      t[comp] = (dadosPorMes[comp] || []).reduce((s, c) => s + (c.movimento_liquido || 0), 0);
    });
    return t;
  }, [dadosPorMes, competencias]);

  const temDados = Object.keys(dadosPorMes).length > 0;

  return (
    <div className="flex flex-col gap-5 pb-10 text-[#e5e2e1] animate-in fade-in">
      {/* ── Header ── */}
      <div className="border-b border-[#222] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3 mb-1">
          <TrendingUp className="text-[#ff4d00]" size={36}/> Contabilizações
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#555] font-black">
          Visão Societária (IFRS 15) — Receita POC · Tributos · Clientes
        </p>
      </div>

      {/* ── Painel de filtros ── */}
      <div className="flex flex-wrap gap-3 items-end bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">

        {/* Período De */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Período De</span>
          <input type="month" value={periodoInicio}
            onChange={e => { const v = e.target.value; setPeriodoInicio(v); if (v > periodoFim) setPeriodoFim(v); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>

        {/* Período Até */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Até</span>
          <input type="month" value={periodoFim}
            onChange={e => { const v = e.target.value; setPeriodoFim(v); if (v < periodoInicio) setPeriodoInicio(v); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>

        {/* Empreendimento */}
        <div className="flex flex-col gap-1 min-w-[220px]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">
            Empreendimento {empsLoading ? '(carregando...)' : `(${empreendimentos.length})`}
          </span>
          <select value={filtroEmpId} onChange={e => setFiltroEmpId(e.target.value)}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-bold outline-none focus:border-[#ff4d00] transition-colors">
            <option value="">Todos os empreendimentos</option>
            {empreendimentos.map(e => (
              <option key={e.id} value={String(e.id)}>{e.nome}</option>
            ))}
          </select>
        </div>

        {/* Indicador de competências */}
        <div className="flex flex-col justify-end pb-0.5">
          <span className="text-[9px] font-bold text-[#444] uppercase tracking-wider">
            {competencias.length} mês{competencias.length !== 1 ? 'es' : ''}
            {!periodoValido && <span className="text-[#ff4d00] ml-2">⚠ máx. 18</span>}
          </span>
        </div>

        {/* Botão */}
        <button onClick={fetchTudo} disabled={loading || !periodoValido || !selectedEmpresa}
          className="ml-auto px-6 py-2.5 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? `Consultando ${competencias.length} meses...` : 'Carregar'}
        </button>
      </div>

      {/* Erro */}
      {error && (
        <div className="bg-[#ff4d00]/10 border border-[#ff4d00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={14} className="text-[#ff4d00] shrink-0"/>
          <p className="text-sm font-mono text-[#ff4d00]">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-12">
          <Zap className="animate-spin text-[#ff4d00]" size={28}/>
          <span className="text-xs font-black uppercase tracking-widest text-[#555]">
            Rodando motor POC para {competencias.length} competência{competencias.length > 1 ? 's' : ''}...
          </span>
        </div>
      )}

      {/* ── Totalizador rápido de meses ── */}
      {!loading && temDados && competencias.length > 1 && (
        <div className="overflow-x-auto">
          <div className="flex gap-2" style={{ minWidth: `${competencias.length * 130}px` }}>
            {competencias.map(comp => {
              const v = totaisPorMes[comp] || 0;
              return (
                <div key={comp} className="flex-1 bg-[#0d0d0d] border border-[#1e1e1e] rounded p-3 text-center min-w-[110px]">
                  <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-1">{labelMes(comp)}</p>
                  <p className="font-mono text-xs font-bold" style={{ color: v > 0 ? '#34c759' : v < 0 ? '#ff4d00' : '#444' }}>
                    {v > 0 ? '+' : ''}{fmt(v)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Tabelas por grupo ── */}
      {!loading && grupos.map(({ grupo, contas }) => (
        <div key={grupo.key} className="bg-[#0d0d0d] border border-[#1e1e1e] rounded-sm overflow-hidden">
          {/* Cabeçalho do grupo */}
          <div className="px-4 py-3 border-b border-[#1a1a1a] flex items-start gap-3" style={{ borderLeft: `3px solid ${grupo.cor}` }}>
            <Building2 size={13} style={{ color: grupo.cor }} className="mt-0.5 shrink-0"/>
            <div>
              <h3 className="text-[10px] font-black uppercase tracking-widest text-white">{grupo.label}</h3>
              <p className="text-[9px] text-[#444] mt-0.5">{grupo.descricao}</p>
            </div>
            <span className="ml-auto text-[9px] text-[#444] font-bold shrink-0">{contas.length} conta{contas.length !== 1 ? 's' : ''}</span>
          </div>

          {/* Tabela horizontal */}
          <div className="overflow-x-auto">
            <table
              className="w-full text-xs border-collapse"
              style={{ minWidth: `${240 + 120 + competencias.length * 120 + 140}px` }}
            >
              <thead>
                <tr className="bg-[#111]">
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#1a1a1a] sticky left-0 z-20 bg-[#111] min-w-[230px]">
                    Conta
                  </th>
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#1a1a1a] min-w-[110px]">
                    Saldo Ant.
                  </th>
                  {competencias.map(c => (
                    <th key={c} className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[#666] border-b border-[#1a1a1a] min-w-[110px]">
                      {labelMes(c)}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-white border-b border-[#1a1a1a] min-w-[130px]">
                    Saldo Final
                  </th>
                </tr>
              </thead>
              <tbody>
                {contas.map(c => (
                  <ContaRow key={c.conta}
                    contaId={c.conta}
                    contaNome={c.nome}
                    grupo={grupo}
                    competencias={competencias}
                    dadosPorMes={dadosPorMes}
                  />
                ))}

                {/* Linha totalizadora */}
                <tr className="bg-[#111]" style={{ borderTop: `1px solid #222` }}>
                  <td className="px-3 py-2 sticky left-0 z-10 bg-[#111] text-[9px] font-black uppercase tracking-widest" style={{ color: grupo.cor }}>
                    ∑ Total {grupo.label}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-[#777]">
                    {fmt(contas.reduce((s, c) => {
                      const primeiroDado = Object.values(dadosPorMes)[0]?.find(r => String(r.conta) === String(c.conta));
                      return s + (primeiroDado?.saldo_anterior || 0);
                    }, 0))}
                  </td>
                  {competencias.map(comp => {
                    const total = contas.reduce((s, ct) => {
                      const m = (dadosPorMes[comp] || []).find(r => String(r.conta) === String(ct.conta));
                      return s + (m?.movimento_liquido || 0);
                    }, 0);
                    return (
                      <td key={comp} className="px-3 py-2 text-right font-mono text-xs font-bold">
                        <span style={{ color: total > 0 ? '#34c759' : total < 0 ? '#ff4d00' : '#333' }}>
                          {total !== 0 ? `${total > 0 ? '+' : ''}${fmt(total)}` : '—'}
                        </span>
                      </td>
                    );
                  })}
                  <td className="px-3 py-2 text-right font-mono text-sm font-black" style={{ color: grupo.cor }}>
                    {fmt(contas.reduce((s, c) => {
                      let sf = 0;
                      Object.values(dadosPorMes)[0] && (sf = Object.values(dadosPorMes)[0]?.find(r => String(r.conta) === String(c.conta))?.saldo_anterior || 0);
                      competencias.forEach(comp => {
                        const m = (dadosPorMes[comp] || []).find(r => String(r.conta) === String(c.conta));
                        sf += m?.movimento_liquido || 0;
                      });
                      return s + sf;
                    }, 0))}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {/* Empty state após load */}
      {!loading && temDados && grupos.length === 0 && (
        <div className="text-center py-12 text-[#555]">
          <AlertTriangle size={36} className="mx-auto mb-3 opacity-20"/>
          <p className="font-black uppercase tracking-widest text-sm text-[#444]">
            Nenhum lançamento societário gerado para o período
          </p>
          <p className="text-[10px] text-[#333] mt-1 uppercase tracking-widest">
            Verifique se há POC, VGV e Receitas configurados para este empreendimento
          </p>
        </div>
      )}

      {/* Call-to-action inicial */}
      {!loading && !temDados && !error && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <div className="w-16 h-16 bg-[#ff4d00]/10 border border-[#ff4d00]/20 rounded flex items-center justify-center">
            <TrendingUp className="text-[#ff4d00]" size={28}/>
          </div>
          <p className="font-black uppercase tracking-widest text-white text-sm">
            Selecione o período e clique em Carregar
          </p>
          <p className="text-[10px] text-[#444] uppercase tracking-widest max-w-xs">
            O motor societário calcula receita POC, tributos diferidos/antecipados e variações de clientes
          </p>
          <button onClick={fetchTudo} disabled={!selectedEmpresa}
            className="mt-2 px-6 py-3 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40">
            <Zap size={13}/> Carregar Dados
          </button>
        </div>
      )}
    </div>
  );
};
