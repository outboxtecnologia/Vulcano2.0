import React, { useState, useMemo, useCallback } from 'react';
import {
  TrendingUp, Zap, AlertTriangle, Building2, ChevronDown, ChevronUp,
  Filter, RefreshCw, Download
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const fmt  = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 }).format(v || 0);
const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// Gera array de competências "YYYY-MM" dentro de [de, ate]
function gerarCompetencias(de, ate) {
  const result = [];
  let [y, m] = de.split('-').map(Number);
  const [ey, em] = ate.split('-').map(Number);
  while (y < ey || (y === ey && m <= em)) {
    result.push(`${y}-${String(m).padStart(2, '0')}`);
    m++;
    if (m > 12) { m = 1; y++; }
  }
  return result;
}

// Converte "YYYY-MM" → label amigável
function labelMes(comp) {
  const [y, m] = comp.split('-').map(Number);
  return `${MESES_ABREV[m - 1]}/${String(y).substring(2)}`;
}

// ── Cor por grupo contábil ───────────────────────────────────────────────────
const GRUPOS = [
  { key: 'receita',   label: 'Receita Societária',        cor: '#34c759',  test: (c,n) => /^3/i.test(String(c)) || /receita|venda/i.test(n) },
  { key: 'custo',     label: 'Custos / POC',               cor: '#ff4d00',  test: (c,n) => /^4/i.test(String(c)) || /custo|obra|poc/i.test(n) },
  { key: 'clientes',  label: 'Clientes e Adiantamentos',   cor: '#a259ff',  test: (c,n) => /^1\.(02|03)/i.test(String(c)) || /cliente|adiant/i.test(n) },
  { key: 'tributos',  label: 'Tributos Societários',       cor: '#ffcc00',  test: (c,n) => /irpj|csll|diferido|tributo soc/i.test(n) },
  { key: 'fiscal',    label: 'DARF / PIS / COFINS / RET',  cor: '#ff9f0a',  test: (c,n) => /pis|cofins|darf|ret|iss/i.test(n) },
  { key: 'caixa',     label: 'Caixa e Bancos',             cor: '#30d158',  test: (c,n) => /^1\.01/i.test(String(c)) || /caixa|banco/i.test(n) },
  { key: 'outros',    label: 'Outras Contas',               cor: '#636366',  test: () => true },
];

function grupoDeContabOu(conta, nome) {
  for (const g of GRUPOS) if (g.test(conta, nome || '')) return g;
  return GRUPOS[GRUPOS.length - 1];
}

// ── Linha de conta (horizontal por mês) ─────────────────────────────────────
function ContaRow({ conta, nome, grupo, meses, dadosPorMes, saldoAnt, isExpanded, onToggle }) {
  const acum = { saldoAnt };
  const movPorMes = {};
  let saldoFinalTotal = saldoAnt;

  meses.forEach(m => {
    const d = dadosPorMes[m];
    if (!d) { movPorMes[m] = null; return; }
    const c = d.find(x => String(x.conta) === String(conta));
    movPorMes[m] = c ? c.movimento_liquido : 0;
    saldoFinalTotal += movPorMes[m] || 0;
  });

  const multiMes = meses.length > 1;

  return (
    <>
      <tr className="border-b border-[#1a1a1a] hover:bg-[#141414] cursor-pointer" onClick={onToggle}>
        {/* Conta + descrição */}
        <td className="px-3 py-2.5 sticky left-0 z-10 bg-[#0d0d0d] min-w-[220px]">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold" style={{ color: grupo.cor }}>{conta}</span>
            <span className="text-[10px] text-[#666] truncate max-w-[130px]" title={nome}>{nome}</span>
            {isExpanded ? <ChevronUp size={10} className="text-[#555] shrink-0"/> : <ChevronDown size={10} className="text-[#555] shrink-0"/>}
          </div>
        </td>

        {/* Saldo anterior (sempre primeiro) */}
        <td className="px-3 py-2.5 text-right font-mono text-xs text-[#666] whitespace-nowrap">{fmt(saldoAnt)}</td>

        {/* Colunas por mês  */}
        {meses.map(m => {
          const val = movPorMes[m];
          return (
            <td key={m} className="px-3 py-2.5 text-right font-mono text-xs whitespace-nowrap">
              {val === null ? (
                <span className="text-[#2a2a2a]">—</span>
              ) : val === 0 ? (
                <span className="text-[#333]">-</span>
              ) : (
                <span className={val > 0 ? 'text-[#34c759]' : 'text-[#ff4d00]'}>
                  {val > 0 ? '+' : ''}{fmt(val)}
                </span>
              )}
            </td>
          );
        })}

        {/* Saldo final */}
        <td className="px-3 py-2.5 text-right font-mono text-sm font-bold text-white whitespace-nowrap">{fmt(saldoFinalTotal)}</td>
      </tr>

      {/* Detalhes expandidos (lançamentos do último mês com dados) */}
      {isExpanded && (() => {
        const ultimoMesComDados = [...meses].reverse().find(m => dadosPorMes[m]?.find(x => String(x.conta) === String(conta)));
        if (!ultimoMesComDados) return null;
        const contaData = dadosPorMes[ultimoMesComDados]?.find(x => String(x.conta) === String(conta));
        if (!contaData?.detalhes?.length) return null;
        return (
          <tr key={`det-${conta}`}>
            <td colSpan={meses.length + 3} className="p-0 bg-[#070707]">
              <table className="w-full text-[10px] border-collapse">
                <thead>
                  <tr className="bg-[#0c0c0c]">
                    <th className="px-5 py-1.5 text-left text-[8px] uppercase tracking-widest font-black text-[#333] border-b border-[#111]">Data</th>
                    <th className="px-5 py-1.5 text-left text-[8px] uppercase tracking-widest font-black text-[#333] border-b border-[#111]">Histórico</th>
                    <th className="px-5 py-1.5 text-center text-[8px] uppercase tracking-widest font-black text-[#333] border-b border-[#111] w-8">N</th>
                    <th className="px-5 py-1.5 text-right text-[8px] uppercase tracking-widest font-black text-[#333] border-b border-[#111] w-28">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {contaData.detalhes.map((d, i) => (
                    <tr key={i} className="border-b border-[#0f0f0f] hover:bg-[#0a0a0a]">
                      <td className="px-5 py-1.5 font-mono text-[#444]">{d.data}</td>
                      <td className="px-5 py-1.5 text-[#555] truncate max-w-[400px]" title={d.historico}>{d.historico}</td>
                      <td className="px-5 py-1.5 text-center font-bold text-[10px]" style={{ color: d.natureza === 'D' ? '#34c759' : '#ff4d00' }}>{d.natureza}</td>
                      <td className="px-5 py-1.5 text-right font-mono text-[#777]">{fmt(d.valor)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </td>
          </tr>
        );
      })()}
    </>
  );
}

// ── MAIN ────────────────────────────────────────────────────────────────────
export const ContabilizacoesView = ({ selectedEmpresa }) => {
  // State: filtros
  const now = new Date();
  const mesAtual = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const [periodoInicio, setPeriodoInicio] = useState(mesAtual);
  const [periodoFim,    setPeriodoFim]    = useState(mesAtual);
  const [filtroEmpId,   setFiltroEmpId]   = useState('');   // '' = todos
  const [tipoVisao, setTipoVisao] = useState('fisico');     // 'fisico' | 'virtual'

  // State: dados carregados por competência
  //  estrutura: { 'YYYY-MM': [ { conta, nome, saldo_anterior, movimento_liquido, detalhes, ... } ] }
  const [dadosPorMes, setDadosPorMes] = useState({});
  // lista de empreendimentos disponíveis (names e IDs) para o select
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [expandedContas, setExpandedContas] = useState({});

  // Competências selecionadas
  const competencias = useMemo(() => {
    try { return gerarCompetencias(periodoInicio, periodoFim); }
    catch { return [periodoInicio]; }
  }, [periodoInicio, periodoFim]);

  // Busca dados para todas as competências do intervalo
  const fetchTudo = useCallback(async () => {
    if (!selectedEmpresa) return;
    setLoading(true);
    setError('');
    const novoDadosPorMes = {};
    const empSet = {};
    try {
      await Promise.all(competencias.map(async (comp) => {
        const [ano, mes] = comp.split('-');
        let url = `${API_BASE}/api/questor/contabilizacoes?empresa_id=${selectedEmpresa}&mes=${+mes}&ano=${+ano}`;
        if (filtroEmpId) url += `&empreendimento_id=${filtroEmpId}`;
        const resp = await fetch(url);
        const json = await resp.json();
        const registros = [];
        (json.data || []).forEach(emp => {
          // Coleta lista de empreendimentos para o select
          empSet[emp.empreendimento_id] = emp.empreendimento_nome;
          const source = tipoVisao === 'fisico' ? (emp.contas_fisicas || []) : (emp.contas_virtuais || []);
          source.forEach(c => registros.push({ ...c }));
        });
        novoDadosPorMes[comp] = registros;
      }));
      // Extrai lista única de empreendimentos
      setEmpreendimentos(Object.entries(empSet).map(([id, nome]) => ({ id: String(id), nome })));
      setDadosPorMes(novoDadosPorMes);
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  }, [selectedEmpresa, competencias, filtroEmpId, tipoVisao]);

  // Mapeia conta → { nome, grupo, saldoAnt }  usando o primeiro mês
  const contasIndex = useMemo(() => {
    const map = {};
    competencias.forEach(comp => {
      (dadosPorMes[comp] || []).forEach(c => {
        if (!map[c.conta]) {
          map[c.conta] = {
            conta: c.conta,
            nome:  c.nome || '',
            grupo: grupoDeContabOu(c.conta, c.nome),
            // Saldo anterior vem do primeiro mês com dado
            saldoAnt: c.saldo_anterior || 0
          };
        }
      });
    });
    return map;
  }, [dadosPorMes, competencias]);

  // Agrupa contas por grupo contábil
  const grupos = useMemo(() => {
    const gMap = {};
    Object.values(contasIndex).forEach(c => {
      const gk = c.grupo.key;
      if (!gMap[gk]) gMap[gk] = { grupo: c.grupo, contas: [] };
      gMap[gk].contas.push(c);
    });
    return Object.values(gMap);
  }, [contasIndex]);

  const toggleConta = (conta) =>
    setExpandedContas(prev => ({ ...prev, [conta]: !prev[conta] }));

  // Período longo demais? Limitamos a 12 meses
  const periodoValido = competencias.length <= 18;

  return (
    <div className="flex flex-col gap-5 pb-10 text-[#e5e2e1] animate-in fade-in">
      {/* ── Header ── */}
      <div className="border-b border-[#222] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3 mb-1">
          <TrendingUp className="text-[#ff4d00]" size={36}/> Contabilizações
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#555] font-black">
          Evolução Mensal de Contas por Período — Físico × Societário
        </p>
      </div>

      {/* ── Filtros ── */}
      <div className="flex flex-wrap gap-3 items-end bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">
        {/* Período de */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Período De</span>
          <input type="month" value={periodoInicio}
            onChange={e => { setPeriodoInicio(e.target.value); if (e.target.value > periodoFim) setPeriodoFim(e.target.value); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors"/>
        </div>

        {/* Período até */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Até</span>
          <input type="month" value={periodoFim}
            onChange={e => { setPeriodoFim(e.target.value); if (e.target.value < periodoInicio) setPeriodoInicio(e.target.value); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors"/>
        </div>

        {/* Empreendimento */}
        <div className="flex flex-col gap-1 min-w-[200px]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Empreendimento</span>
          <select value={filtroEmpId} onChange={e => setFiltroEmpId(e.target.value)}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-bold outline-none focus:border-[#ff4d00] transition-colors">
            <option value="">Todos os empreendimentos</option>
            {empreendimentos.map(e => (
              <option key={e.id} value={e.id}>{e.nome}</option>
            ))}
          </select>
        </div>

        {/* Tipo */}
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Visão</span>
          <div className="flex gap-1">
            {[['fisico','Físico'],['virtual','Societário']].map(([v,l]) => (
              <button key={v} onClick={() => setTipoVisao(v)}
                className={`px-3 py-2 text-[9px] font-black uppercase tracking-widest border rounded transition-all ${
                  tipoVisao === v ? 'bg-[#ff4d00] text-black border-[#ff4d00]' : 'text-[#888] border-[#333] hover:border-[#555]'
                }`}>{l}</button>
            ))}
          </div>
        </div>

        {/* Botão buscar */}
        <button onClick={fetchTudo} disabled={loading || !periodoValido}
          className="px-5 py-2.5 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed ml-auto">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? 'Buscando...' : 'Carregar'}
        </button>
      </div>

      {/* Aviso período longo */}
      {!periodoValido && (
        <div className="bg-[#ffcc00]/10 border border-[#ffcc00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={16} className="text-[#ffcc00] shrink-0"/>
          <p className="text-[10px] font-bold text-[#ffcc00] uppercase tracking-wider">
            Período máximo de 18 meses. Ajuste o intervalo para continuar.
          </p>
        </div>
      )}

      {/* Erro */}
      {error && (
        <div className="bg-[#ff4d00]/10 border border-[#ff4d00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={16} className="text-[#ff4d00] shrink-0"/>
          <p className="text-sm font-mono text-[#ff4d00]">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-12">
          <Zap className="animate-spin text-[#ff4d00]" size={28}/>
          <span className="text-xs font-black uppercase tracking-widest text-[#555]">
            Consultando {competencias.length} competência{competencias.length > 1 ? 's' : ''}...
          </span>
        </div>
      )}

      {/* ── Tabela principal ── */}
      {!loading && grupos.length > 0 && grupos.map(({ grupo, contas }) => (
        <div key={grupo.key} className="bg-[#0d0d0d] border border-[#1e1e1e] rounded-sm overflow-hidden">
          {/* Cabeçalho do grupo */}
          <div className="px-4 py-3 flex items-center gap-3 border-b border-[#1a1a1a]"
            style={{ borderLeft: `3px solid ${grupo.cor}` }}>
            <Building2 size={13} style={{ color: grupo.cor }}/>
            <h3 className="text-[10px] font-black uppercase tracking-widest text-white">{grupo.label}</h3>
            <span className="text-[9px] text-[#444] font-bold ml-1">({contas.length} conta{contas.length !== 1 ? 's' : ''})</span>
          </div>

          {/* Tabela */}
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-xs border-collapse" style={{ minWidth: `${220 + 120 + competencias.length * 120 + 140}px` }}>
              <thead>
                <tr className="bg-[#111]">
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#1a1a1a] sticky left-0 z-10 bg-[#111] min-w-[220px]">
                    Conta / Descrição
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
                    conta={c.conta}
                    nome={c.nome}
                    grupo={grupo}
                    meses={competencias}
                    dadosPorMes={dadosPorMes}
                    saldoAnt={c.saldoAnt}
                    isExpanded={!!expandedContas[c.conta]}
                    onToggle={() => toggleConta(c.conta)}
                  />
                ))}
                {/* Linha totalizadora do grupo */}
                <tr className="bg-[#111] font-bold">
                  <td className="px-3 py-2 sticky left-0 z-10 bg-[#111] text-[9px] font-black uppercase tracking-widest" style={{ color: grupo.cor }}>
                    Total {grupo.label}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-[#888]">
                    {fmt(contas.reduce((s, c) => s + (c.saldoAnt || 0), 0))}
                  </td>
                  {competencias.map(comp => {
                    const total = contas.reduce((s, c) => {
                      const d = dadosPorMes[comp];
                      const match = d?.find(x => String(x.conta) === String(c.conta));
                      return s + (match?.movimento_liquido || 0);
                    }, 0);
                    return (
                      <td key={comp} className="px-3 py-2 text-right font-mono text-xs font-bold">
                        <span className={total > 0 ? 'text-[#34c759]' : total < 0 ? 'text-[#ff4d00]' : 'text-[#333]'}>
                          {total !== 0 ? (total > 0 ? '+' : '') + fmt(total) : '—'}
                        </span>
                      </td>
                    );
                  })}
                  <td className="px-3 py-2 text-right font-mono text-sm font-black" style={{ color: grupo.cor }}>
                    {fmt(contas.reduce((s, c) => {
                      let sf = c.saldoAnt || 0;
                      competencias.forEach(comp => {
                        const d = dadosPorMes[comp];
                        const match = d?.find(x => String(x.conta) === String(c.conta));
                        sf += match?.movimento_liquido || 0;
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

      {/* Empty state */}
      {!loading && grupos.length === 0 && Object.keys(dadosPorMes).length > 0 && (
        <div className="text-center py-16 text-[#555]">
          <TrendingUp size={40} className="mx-auto mb-4 opacity-20"/>
          <p className="font-black uppercase tracking-widest text-[#444] text-sm">Nenhum lançamento no período selecionado</p>
        </div>
      )}

      {/* Call-to-action inicial */}
      {!loading && Object.keys(dadosPorMes).length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <div className="w-16 h-16 bg-[#ff4d00]/10 border border-[#ff4d00]/20 rounded flex items-center justify-center">
            <TrendingUp className="text-[#ff4d00]" size={28}/>
          </div>
          <p className="font-black uppercase tracking-widest text-white text-sm">Selecione o período e clique em Carregar</p>
          <p className="text-[10px] text-[#444] uppercase tracking-widest">
            Use um intervalo de meses para visualizar a evolução horizontal das contas
          </p>
          <button onClick={fetchTudo}
            className="mt-2 px-6 py-3 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2">
            <Zap size={13}/> Carregar Dados
          </button>
        </div>
      )}
    </div>
  );
};
