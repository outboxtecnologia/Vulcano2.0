import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  TrendingUp, Zap, AlertTriangle, Building2,
  ChevronDown, ChevronUp, RefreshCw, Download
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const fmt = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 }).format(v || 0);
const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// â”€â”€ helpers de período â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

// â”€â”€ classificação de conta virtual por tipo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    descricao: 'Diferenças entre base caixa e base DRE (POC) â€” antecipados e diferidos',
    test: (nome) => /diferido|antecipado|passivo tributo|constituição adiant/i.test(nome)
  },
  {
    key: 'trib_dre',
    label: 'Despesa Tributária DRE',
    cor: '#ff9f0a',
    descricao: 'IRPJ, CSLL, PIS, COFINS, RET â€” pelo critério econômico (base POC)',
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

// â”€â”€ Linha de conta na tabela â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        className="border-b border-[var(--v-border)] hover:bg-[var(--v-card)] cursor-pointer transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        {/* Conta */}
        <td className="px-3 py-2.5 sticky left-0 z-10 bg-[var(--v-deep)] min-w-[230px]">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] font-black shrink-0" style={{ color: grupo.cor }}>{contaId}</span>
            <span className="text-[10px] text-[var(--v-text-faint)] truncate" title={contaNome}>{contaNome}</span>
            {detalhes.length > 0 && (open ? <ChevronUp size={9} className="text-[var(--v-text-faint)] shrink-0"/> : <ChevronDown size={9} className="text-[var(--v-text-faint)] shrink-0"/>)}
          </div>
        </td>

        {/* Saldo anterior */}
        <td className="px-3 py-2.5 text-right font-mono text-[11px] text-[var(--v-text-faint)] whitespace-nowrap">{fmt(saldoAnt)}</td>

        {/* Movimento por mês */}
        {competencias.map(comp => {
          const v = movPorMes[comp];
          return (
            <td key={comp} className="px-3 py-2.5 text-right font-mono text-[11px] whitespace-nowrap">
              {v === null ? <span className="text-[#252525]">â€”</span>
               : v === 0  ? <span className="text-[#333]">-</span>
               : <span style={{ color: v > 0 ? '#34c759' : '#ff4d00' }}>
                   {v > 0 ? '+' : ''}{fmt(v)}
                 </span>}
            </td>
          );
        })}

        {/* Saldo final */}
        <td className="px-3 py-2.5 text-right font-mono text-sm font-black text-[var(--v-text-bold)] whitespace-nowrap">{fmt(saldoFinal)}</td>
      </tr>

      {/* Detalhes */}
      {open && detalhes.length > 0 && (
        <tr>
          <td colSpan={competencias.length + 3} className="p-0 bg-[#070707]">
            <div className="px-4 py-1 text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] border-b border-[var(--v-bg)]">
              Lançamentos analíticos â€” {labelMes(ultimoMesComDado)}
            </div>
            <table className="w-full text-[10px] border-collapse">
              <thead>
                <tr className="border-b border-[var(--v-bg)] text-left bg-[var(--v-deep)]">
                  <th className="px-4 py-1.5 font-normal text-[8px] text-[var(--v-text-faint)] uppercase tracking-widest w-24">Data</th>
                  <th className="px-3 py-1.5 font-normal text-[8px] text-[var(--v-text-faint)] uppercase tracking-widest">Histórico</th>
                  <th className="px-3 py-1.5 font-normal text-[8px] text-[var(--v-text-faint)] uppercase tracking-widest text-center w-8">Nat</th>
                  <th className="px-3 py-1.5 font-normal text-[8px] text-[var(--v-text-faint)] uppercase tracking-widest">C.Partida</th>
                  <th className="px-4 py-1.5 font-normal text-[8px] text-[var(--v-text-faint)] uppercase tracking-widest text-right w-28">Valor</th>
                </tr>
              </thead>
              <tbody>
                {detalhes.map((d, i) => (
                  <tr key={i} className="border-b border-[var(--v-bg)] hover:bg-[var(--v-deep)]">
                    <td className="px-4 py-1.5 font-mono text-[var(--v-text-faint)] whitespace-nowrap w-24">{d.data}</td>
                    <td className="px-3 py-1.5 text-[var(--v-text-faint)] w-full max-w-0 truncate" title={d.historico}>{d.historico}</td>
                    <td className="px-3 py-1.5 text-center font-bold w-8" style={{ color: d.natureza === 'D' ? '#34c759' : '#ff9f0a' }}>{d.natureza}</td>
                    <td className="px-3 py-1.5 font-mono text-[var(--v-text-muted)] max-w-[220px] truncate" title={d.contrapartida || ''}>{d.contrapartida || '-'}</td>
                    <td className="px-4 py-1.5 text-right font-mono text-[var(--v-text-muted)] whitespace-nowrap w-28">{fmt(d.valor)}</td>
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

// â”€â”€ MAIN VIEW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  // â”€â”€ Carrega lista de empreendimentos disponíveis na montagem â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  // â”€â”€ Busca dados em paralelo para cada mês â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  // â”€â”€ Gerador de Lote Questor (TXT) â”€â”€
  const gerarTxtQuestor = () => {
    if (!selectedEmpresa) return;
    let txt = `-- Geração Automática LCTOCTB (Vulcano 2.0)\n-- Empresa: ${selectedEmpresa}\n-- Período: ${periodoInicio} a ${periodoFim}\n\n`;
    
    // Collect all unique lotes to avoid duplicating the double-entry (since D and C are present for virtuals)
    // Actually, virtual entries are injected as a D and a C record. If we iterate all, we'd double the entries!
    // So we only generate the INSERT when we are on the DÉBITO side to ensure 1 insert per pair.
    // Lançamentos puramente de controle de saldo ('Geral' ou LOC_VIRTUAL) não devem ser exportados
    Object.keys(dadosPorMes).forEach(mes => {
      const contas = dadosPorMes[mes] || [];
      contas.forEach(c => {
        (c.detalhes || []).filter(d => d.virtual && d.natureza === 'D' && d.lote_id && d.lote_id !== 'Geral').forEach(d => {
           const cDeb = c.conta;
           const cCred = d.contrapartida ? d.contrapartida.split(' - ')[0].trim() : '0';
           const val = Number(d.valor || 0).toFixed(2);
           const hist = (d.historico || '').replace(/'/g, "''");
           
           // d.data format: "30/04/2025 (Sim)" -> extract date
           const matchDate = d.data.match(/(\d{2})\/(\d{2})\/(\d{4})/);
           let dataSQL = 'CURRENT_DATE';
           if (matchDate) {
               dataSQL = `'${matchDate[3]}-${matchDate[2]}-${matchDate[1]}'`;
           }
           
           txt += `INSERT INTO LCTOCTB (CODIGOEMPRESA, DATALCTOCTB, CONTACTBDEB, CONTACTBCRED, VALORLCTOGER, COMPLHIST, CODIGOORIGLCTOCTB) ` +
                  `VALUES (${selectedEmpresa}, ${dataSQL}, ${cDeb}, ${cCred}, ${val}, '${hist}', 'VU');\n`;
        });
      });
    });

    const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Contabilizacoes_Questor_${selectedEmpresa}_${periodoInicio}_a_${periodoFim}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // â”€â”€ index de contas (conta â†’ { nome, grupoVirtual }) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  // â”€â”€ Agrupa contas por grupo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    <div className="flex flex-col gap-5 pb-10 text-[var(--v-text)] animate-in fade-in">
      {/* â”€â”€ Header â”€â”€ */}
      <div className="border-b border-[var(--v-border)] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-[var(--v-text-bold)] flex items-center gap-3 mb-1">
          <TrendingUp className="text-[var(--v-accent)]" size={36}/> Contabilizações
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--v-text-faint)] font-black">
          Visão Societária (IFRS 15) â€” Receita POC · Tributos · Clientes
        </p>
      </div>

      {/* â”€â”€ Painel de filtros â”€â”€ */}
      <div className="flex flex-wrap gap-3 items-end bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-4">

        {/* Período De */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Período De</span>
          <input type="month" value={periodoInicio}
            onChange={e => { const v = e.target.value; setPeriodoInicio(v); if (v > periodoFim) setPeriodoFim(v); }}
            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text)] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>

        {/* Período Até */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Até</span>
          <input type="month" value={periodoFim}
            onChange={e => { const v = e.target.value; setPeriodoFim(v); if (v < periodoInicio) setPeriodoInicio(v); }}
            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text)] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>

        {/* Empreendimento */}
        <div className="flex flex-col gap-1 min-w-[220px]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">
            Empreendimento {empsLoading ? '(carregando...)' : `(${empreendimentos.length})`}
          </span>
          <select value={filtroEmpId} onChange={e => setFiltroEmpId(e.target.value)}
            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text)] text-xs font-bold outline-none focus:border-[#ff4d00] transition-colors">
            <option value="">Todos os empreendimentos</option>
            {empreendimentos.map(e => (
              <option key={e.id} value={String(e.id)}>{e.nome}</option>
            ))}
          </select>
        </div>

        {/* Indicador de competências */}
        <div className="flex flex-col justify-end pb-0.5">
          <span className="text-[9px] font-bold text-[var(--v-text-faint)] uppercase tracking-wider">
            {competencias.length} mês{competencias.length !== 1 ? 'es' : ''}
            {!periodoValido && <span className="text-[var(--v-accent)] ml-2">âš  máx. 18</span>}
          </span>
        </div>

        {/* Botão Carregar */}
        <button onClick={fetchTudo} disabled={loading || !periodoValido || !selectedEmpresa}
          className="ml-auto px-6 py-2.5 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? `Consultando ${competencias.length} meses...` : 'Carregar'}
        </button>

        {/* Botão Gerar TXT */}
        {temDados && (
          <button onClick={gerarTxtQuestor}
            className="px-6 py-2.5 bg-black/40 border border-white/10 text-[var(--v-text-bold)] text-[9px] font-black uppercase tracking-widest rounded hover:border-[var(--v-accent)] hover:text-[var(--v-accent)] transition-all flex items-center gap-2">
            <Download size={13}/> Gerar TXT (Questor)
          </button>
        )}
      </div>

      {/* Erro */}
      {error && (
        <div className="bg-[var(--v-accent)]/10 border border-[#ff4d00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={14} className="text-[var(--v-accent)] shrink-0"/>
          <p className="text-sm font-mono text-[var(--v-accent)]">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-12">
          <Zap className="animate-spin text-[var(--v-accent)]" size={28}/>
          <span className="text-xs font-black uppercase tracking-widest text-[var(--v-text-faint)]">
            Rodando motor POC para {competencias.length} competência{competencias.length > 1 ? 's' : ''}...
          </span>
        </div>
      )}

      {/* â”€â”€ Totalizador rápido de meses â”€â”€ */}
      {!loading && temDados && competencias.length > 1 && (
        <div className="overflow-x-auto">
          <div className="flex gap-2" style={{ minWidth: `${competencias.length * 130}px` }}>
            {competencias.map(comp => {
              const v = totaisPorMes[comp] || 0;
              return (
                <div key={comp} className="flex-1 bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-3 text-center min-w-[110px]">
                  <p className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-1">{labelMes(comp)}</p>
                  <p className="font-mono text-xs font-bold" style={{ color: v > 0 ? '#34c759' : v < 0 ? '#ff4d00' : '#444' }}>
                    {v > 0 ? '+' : ''}{fmt(v)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* â”€â”€ Tabelas por grupo â”€â”€ */}
      {!loading && grupos.map(({ grupo, contas }) => (
        <div key={grupo.key} className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
          {/* Cabeçalho do grupo */}
          <div className="px-4 py-3 border-b border-[var(--v-border)] flex items-start gap-3" style={{ borderLeft: `3px solid ${grupo.cor}` }}>
            <Building2 size={13} style={{ color: grupo.cor }} className="mt-0.5 shrink-0"/>
            <div>
              <h3 className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-bold)]">{grupo.label}</h3>
              <p className="text-[9px] text-[var(--v-text-faint)] mt-0.5">{grupo.descricao}</p>
            </div>
            <span className="ml-auto text-[9px] text-[var(--v-text-faint)] font-bold shrink-0">{contas.length} conta{contas.length !== 1 ? 's' : ''}</span>
          </div>

          {/* Tabela horizontal */}
          <div className="overflow-x-auto">
            <table
              className="w-full text-xs border-collapse"
              style={{ minWidth: `${240 + 120 + competencias.length * 120 + 140}px` }}
            >
              <thead>
                <tr className="bg-[var(--v-deep)]">
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] border-b border-[var(--v-border)] sticky left-0 z-20 bg-[var(--v-deep)] min-w-[230px]">
                    Conta
                  </th>
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] border-b border-[var(--v-border)] min-w-[110px]">
                    Saldo Ant.
                  </th>
                  {competencias.map(c => (
                    <th key={c} className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] border-b border-[var(--v-border)] min-w-[110px]">
                      {labelMes(c)}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[var(--v-text-bold)] border-b border-[var(--v-border)] min-w-[130px]">
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
                <tr className="bg-[var(--v-deep)]" style={{ borderTop: `1px solid #222` }}>
                  <td className="px-3 py-2 sticky left-0 z-10 bg-[var(--v-deep)] text-[9px] font-black uppercase tracking-widest" style={{ color: grupo.cor }}>
                    âˆ‘ Total {grupo.label}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-[var(--v-text-faint)]">
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
                          {total !== 0 ? `${total > 0 ? '+' : ''}${fmt(total)}` : 'â€”'}
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

      {/* ── Gran Totalizador (Partidas Dobradas) ── */}
      {!loading && temDados && grupos.length > 0 && (
        <div className="bg-[#0f0f0f] border border-[var(--v-border)] rounded overflow-hidden flex flex-col md:flex-row mt-2">
          {/* Box Header */}
          <div className="bg-[var(--v-deep)] px-6 py-4 flex flex-col justify-center border-b md:border-b-0 md:border-r border-[var(--v-border)] min-w-[240px]">
            <h3 className="text-[12px] font-black uppercase tracking-widest text-white flex items-center gap-2">
              <RefreshCw size={14} className="text-[#34c759]" />
              Prova Real (IFRS 15)
            </h3>
            <p className="text-[9px] text-[var(--v-text-faint)] mt-1 uppercase tracking-wider">Total de Partidas Dobradas</p>
          </div>
          
          <div className="flex-1 flex overflow-x-auto">
            {competencias.map(comp => {
              const mesLista = dadosPorMes[comp] || [];
              const totD = mesLista.reduce((s, c) => s + (c.movimento_debito || 0), 0);
              const totC = mesLista.reduce((s, c) => s + (c.movimento_credito || 0), 0);
              const diff = Math.abs(totD - totC);
              const isOk = diff < 0.05;
              
              return (
                <div key={comp} className="min-w-[200px] flex-1 p-3 border-r border-[#222] last:border-0 flex flex-col justify-start">
                   <p className="text-[9px] font-black uppercase tracking-widest text-[#aaa] mb-3 text-center">{labelMes(comp)}</p>
                   <div className="flex justify-between items-center text-[10px] mb-1">
                     <span className="text-[#34c759] font-black uppercase tracking-wider">Débitos</span>
                     <span className="font-mono text-[#34c759] font-bold" title={totD.toString()}>{fmt(totD)}</span>
                   </div>
                   <div className="flex justify-between items-center text-[10px] mb-2 pb-2 border-b border-[#333]">
                     <span className="text-[#ff9f0a] font-black uppercase tracking-wider">Créditos</span>
                     <span className="font-mono text-[#ff9f0a] font-bold" title={totC.toString()}>{fmt(totC)}</span>
                   </div>
                   <div className="flex justify-between items-center mt-1">
                     <span className="text-[8px] uppercase tracking-widest text-[#777] font-bold">Diferença</span>
                     <span className={`font-mono text-xs font-black ${isOk ? 'text-[#333]' : 'text-[#ff4d00]'}`}>
                       {isOk ? 'OK' : fmt(diff)}
                     </span>
                   </div>

                   <details className={`mt-3 text-[9px] group ${isOk ? 'text-[#555]' : 'text-[#ff4d00]'}`} open={!isOk}>
                     <summary className="cursor-pointer hover:text-white uppercase tracking-wider mb-2 font-bold focus:outline-none">
                       {isOk ? 'Ver Malha Fina (T-Accounts & Balancete)' : 'Detalhar Analítico & Contrapartidas'}
                     </summary>
                     
                     <div className="bg-[#151515] p-3 rounded overflow-y-auto max-h-[300px] border border-[#333] flex flex-col gap-4">
                       
                       {/* 1. Matriz de Contrapartidas */}
                       <div>
                         <h4 className="text-[10px] font-black uppercase tracking-widest text-[#bbb] mb-2 border-b border-[#333] pb-1">
                           Razão por Contrapartidas (Caminho do Dinheiro)
                         </h4>
                         <table className="w-full text-left font-mono text-[8px]">
                            <thead>
                               <tr className="border-b border-[#333] text-[#777]">
                                  <th className="font-normal pb-1 truncate max-w-[70px]">Conta Débito</th>
                                  <th className="font-normal pb-1 truncate max-w-[70px]">Conta Crédito</th>
                                  <th className="font-normal pb-1 text-right">Total Transacionado</th>
                               </tr>
                            </thead>
                            <tbody>
                               {(() => {
                                 // Agrupa detalhes de todas as contas por lote_id
                                 const lotes = {};
                                 mesLista.forEach(contaObj => {
                                   (contaObj.detalhes || []).forEach(det => {
                                     if (!det.lote_id || det.lote_id === 'Geral') return;
                                     if (!lotes[det.lote_id]) lotes[det.lote_id] = { debitos: [], creditos: [] };
                                     if (det.natureza === 'D') {
                                        lotes[det.lote_id].debitos.push({ conta: contaObj.conta, nome: contaObj.nome, valor: det.valor });
                                     } else {
                                        lotes[det.lote_id].creditos.push({ conta: contaObj.conta, nome: contaObj.nome, valor: det.valor });
                                     }
                                   });
                                 });

                                 // Cruza os pares e soma totais
                                 const matriz = {};
                                 Object.values(lotes).forEach(L => {
                                    if (L.debitos.length === 0 || L.creditos.length === 0) return;
                                    L.debitos.forEach(deb => {
                                       L.creditos.forEach(cred => {
                                          const val = Math.min(deb.valor, cred.valor); // Para 1x1, é o valor exato do par.
                                          if (val < 0.01) return;
                                          const key = `${deb.conta}|${cred.conta}`;
                                          if (!matriz[key]) matriz[key] = { d: deb, c: cred, valor: 0 };
                                          matriz[key].valor += val;
                                       });
                                    });
                                 });

                                 const linhas = Object.values(matriz).sort((a,b) => b.valor - a.valor);
                                 if (linhas.length === 0) {
                                   return <tr><td colSpan="3" className="text-center py-2 text-[#555]">Nenhum par rastreável neste mês</td></tr>;
                                 }
                                 
                                 return linhas.map((linha, idx) => (
                                   <tr key={idx} className="border-b border-[#222] hover:bg-[#222]">
                                      <td className="py-1 text-[#34c759] truncate max-w-[70px]" title={linha.d.nome}>{linha.d.conta}</td>
                                      <td className="py-1 text-[#ff9f0a] truncate max-w-[70px]" title={linha.c.nome}>{linha.c.conta}</td>
                                      <td className="py-1 pr-1 text-right text-gray-300 font-bold">{fmt(linha.valor)}</td>
                                   </tr>
                                 ));
                               })()}
                            </tbody>
                         </table>
                       </div>

                       {/* 2. Balancete Isolado Existente */}
                       <div>
                         <h4 className="text-[10px] font-black uppercase tracking-widest text-[#bbb] mb-2 border-b border-[#333] pb-1">
                           Balancete Analítico Geral
                         </h4>
                         <table className="w-full text-left font-mono text-[8px]">
                            <thead>
                               <tr className="border-b border-[#333] text-[#777]">
                                  <th className="font-normal pb-1">Conta</th>
                                  <th className="font-normal pb-1 text-right pr-2">Débito</th>
                                  <th className="font-normal pb-1 text-right">Crédito</th>
                               </tr>
                            </thead>
                            <tbody>
                               {mesLista.filter(c => Math.abs(c.movimento_debito) > 0.01 || Math.abs(c.movimento_credito) > 0.01).map(c => (
                                 <tr key={c.conta} className="border-b border-[#222] last:border-0 hover:bg-[#222]">
                                    <td className="py-1 text-[#aaa] truncate max-w-[80px]" title={c.nome}>{c.conta}</td>
                                    <td className="py-1 text-right pr-2 text-[#34c759]">{c.movimento_debito > 0.01 ? fmt(c.movimento_debito) : '-'}</td>
                                    <td className="py-1 text-right text-[#ff9f0a]">{c.movimento_credito > 0.01 ? fmt(c.movimento_credito) : '-'}</td>
                                 </tr>
                               ))}
                            </tbody>
                         </table>
                       </div>
                       
                     </div>
                   </details>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty state após load */}
      {!loading && temDados && grupos.length === 0 && (
        <div className="text-center py-12 text-[var(--v-text-faint)]">
          <AlertTriangle size={36} className="mx-auto mb-3 opacity-20"/>
          <p className="font-black uppercase tracking-widest text-sm text-[var(--v-text-faint)]">
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
          <div className="w-16 h-16 bg-[var(--v-accent)]/10 border border-[#ff4d00]/20 rounded flex items-center justify-center">
            <TrendingUp className="text-[var(--v-accent)]" size={28}/>
          </div>
          <p className="font-black uppercase tracking-widest text-[var(--v-text-bold)] text-sm">
            Selecione o período e clique em Carregar
          </p>
          <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest max-w-xs">
            O motor societário calcula receita POC, tributos diferidos/antecipados e variações de clientes
          </p>
          <button onClick={fetchTudo} disabled={!selectedEmpresa}
            className="mt-2 px-6 py-3 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40">
            <Zap size={13}/> Carregar Dados
          </button>
        </div>
      )}
    </div>
  );
};
