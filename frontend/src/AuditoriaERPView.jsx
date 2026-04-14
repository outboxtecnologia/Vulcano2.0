import React, { useState, useEffect, useMemo, useCallback } from 'react';
import * as XLSX from 'xlsx';
import {
  ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle,
  RefreshCw, Building2, ChevronDown, ChevronUp, ArrowRight,
  Download, GitCompare, List, Link2
} from 'lucide-react';
import { createPortal } from 'react-dom';

const API_BASE = "http://127.0.0.1:8000";
const fmt = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 }).format(v || 0);
const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// ── helpers ──────────────────────────────────────────────────────────────────
function gerarCompetencias(de, ate) {
  if (!de || !ate || de.length !== 7 || ate.length !== 7) return [de || ""];
  const res = [];
  let [y, m] = de.split('-').map(Number);
  const [ey, em] = ate.split('-').map(Number);
  
  if (isNaN(y) || isNaN(m) || isNaN(ey) || isNaN(em)) return [de || ""];
  if (y > ey || (y === ey && m > em)) return [de || ""];
  
  let loops = 0;
  while ((y < ey || (y === ey && m <= em)) && loops < 120) {
    res.push(`${y}-${String(m).padStart(2, '0')}`);
    m++; if (m > 12) { m = 1; y++; }
    loops++;
  }
  return res;
}
const labelMes = (comp) => {
  const [y, m] = comp.split('-').map(Number);
  return `${MESES_ABREV[m - 1]}/${String(y).slice(2)}`;
};

const abs = (v) => Math.abs(v || 0);
const DIVERGENCIA_CORTE = 0.5; // abaixo disso, considera ok

// Contas que usam movimentação do período para conciliação (não delta de saldo)
const CONTAS_USA_MOVIMENTO = new Set([
  '1545','1552','1553','1556',
  '2829','2830',
  '4828','4829','4958','4995'
]);

// Contas do grupo APTO: só fazem cross-match entre si, indexadas por APTO+número.
const CONTAS_GRUPO_APTO = new Set([5653, 5665, 5666]);

/**
 * Extrai 'APTO_<num>' do texto histórico usando a ÚLTIMA ocorrência.
 * Históricos como "APTO 277 ... - APTO 302" têm dois APTOs:
 *   - 1º = número do contrato (ignorar)
 *   - 2º = número real do apartamento (usar como indexador)
 * Retorna null se não encontrar nenhum.
 */
function extractAptoNum(texto) {
  const matches = [...(texto || '').toUpperCase().matchAll(/\bAPT[O]?[\s\-]*(\d+)/g)];
  if (matches.length === 0) return null;
  return `APTO_${matches[matches.length - 1][1]}`; // sempre a última ocorrência
}

// ── Matching de órfãos ────────────────────────────────────────────────────────
// Retorna { fisicosOrfaos, virtuaisOrfaos } — lançamentos sem par no lado oposto.
// Matching por natureza + valor (tolerância R$0,01).
function calcularOrfaos(todosFisico, todosVirtual) {
  const usados = new Set();
  const fisicosOrfaos = [];

  todosFisico.forEach((f, fi) => {
    const idx = todosVirtual.findIndex((v, vi) =>
      !usados.has(vi) &&
      v.natureza === f.natureza &&
      Math.abs((v.valor || 0) - (f.valor || 0)) < 0.01
    );
    if (idx === -1) {
      fisicosOrfaos.push({ ...f, _side: 'Q' });
    } else {
      usados.add(idx);
    }
  });

  const virtuaisOrfaos = todosVirtual
    .filter((_, vi) => !usados.has(vi))
    .map(v => ({ ...v, _side: 'V' }));

  return { fisicosOrfaos, virtuaisOrfaos };
}

// ── Exportação XLSX ───────────────────────────────────────────────────────────
function exportarRazaoXLSX({ contaId, contaNome, todosFisico, todosVirtual, fisicosOrfaos, virtuaisOrfaos }) {
  const wb = XLSX.utils.book_new();

  const toRow = (d, origem) => ({
    Origem: origem,
    Data: d.data || '',
    Historico: d.historico || '',
    Natureza: d.natureza || '',
    Valor: d.valor || 0,
  });

  // Aba 1 — Órfãos
  const orfaosRows = [
    ...fisicosOrfaos.map(d => toRow(d, 'Questor (órfão)')),
    ...virtuaisOrfaos.map(d => toRow(d, 'Vulcano (órfão)')),
  ];
  const wsOrfaos = XLSX.utils.json_to_sheet(
    orfaosRows.length > 0 ? orfaosRows : [{ Origem: '', Data: '', Historico: 'Nenhum órfão encontrado', Natureza: '', Valor: 0 }]
  );
  XLSX.utils.book_append_sheet(wb, wsOrfaos, 'Orfaos');

  // Aba 2 — Razão Completo (intercalado Q e V)
  const razaoRows = [
    ...todosFisico.map(d => toRow(d, 'Questor')),
    ...todosVirtual.map(d => toRow(d, 'Vulcano')),
  ];
  const wsRazao = XLSX.utils.json_to_sheet(razaoRows.length > 0 ? razaoRows : [{ Origem: '' }]);
  XLSX.utils.book_append_sheet(wb, wsRazao, 'Razao_Completo');

  XLSX.writeFile(wb, `Razao_${contaId}_${contaNome.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 30)}.xlsx`);
}

// Semáforo de status
function Status({ diff }) {
  if (abs(diff) < DIVERGENCIA_CORTE) return <CheckCircle2 size={14} className="text-[var(--v-accent-3)] shrink-0"/>;
  if (abs(diff) < 5000)             return <AlertTriangle size={14} className="text-[var(--v-accent-6)] shrink-0"/>;
  return <XCircle size={14} className="text-[var(--v-accent)] shrink-0"/>;
}

// Cor da divergência
function corDiff(diff) {
  if (abs(diff) < DIVERGENCIA_CORTE) return '#34c759';
  if (abs(diff) < 5000)             return '#ffcc00';
  return '#ff4d00';
}

// ── Tabela de lançamentos interna ────────────────────────────────────────────
function TabelaLancs({ itens, corNaturezaD, corNaturezaC, semLabel }) {
  if (itens.length === 0)
    return <p className="px-4 py-2 text-[11px] font-bold text-[#333] uppercase italic">{semLabel}</p>;
  return (
    <table className="w-full text-[11px] table-fixed" style={{ tableLayout: 'fixed' }}>
      <colgroup>
        <col style={{ width: '72px' }}/>
        <col/>{/* historico — ocupa o restante */}
        <col style={{ width: '24px' }}/>
        <col style={{ width: '92px' }}/>
      </colgroup>
      <tbody>
        {itens.map((d, i) => {
          const hist = (d.historico || '').trim() || (d.logica || '').trim() || (d.chave ? `Lçto ${d.chave}` : '—');
          return (
            <tr key={i} className="border-b border-[var(--v-bg)] hover:bg-[var(--v-deep)]">
              <td className="px-2 py-1 font-mono font-bold text-[var(--v-text-faint)] whitespace-nowrap overflow-hidden">
                <div>{d.data}</div>
                {d.origem && <span className={`text-[8px] px-1 py-0 rounded ${d.origem === 'VU' ? 'bg-[#a259ff]/20 text-[var(--v-accent-5)] border border-[#a259ff]/30' : 'bg-[var(--v-accent)]/20 text-[var(--v-accent)] border border-[var(--v-accent)]/30'}`}>{d.origem}</span>}
              </td>
              <td className="px-2 py-1 overflow-hidden" title={hist}>
                <div className="truncate font-bold text-[var(--v-text-faint)]">{hist}</div>
              </td>
              <td className="px-2 py-1 text-center font-black text-[12px] overflow-hidden" style={{ color: d.natureza === 'D' ? corNaturezaD : corNaturezaC }}>{d.natureza}</td>
              <td className="px-2 py-1 text-right font-mono font-black text-[var(--v-text-muted)] whitespace-nowrap overflow-hidden">{fmt(d.valor)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// ── Painel de orfaos (expande ao clicar na linha da conta) ───────────────────
function DetalheOrfaos({ porComp, contaId, contaNome, todosVirtualLogica, onRacional, onAgent }) {
  const [aba, setAba] = useState('orfaos');

  const todosFisico  = porComp.flatMap(c => c.detalhesFisico);
  const todosVirtual = porComp.flatMap(c => c.detalhesVirtual);

  const { fisicosOrfaos, virtuaisOrfaos } = useMemo(
    () => calcularOrfaos(todosFisico, todosVirtual),
    [todosFisico.length, todosVirtual.length]
  );
  
  const questorManual = todosFisico;
  const vulcano1 = porComp.flatMap(c => c.legadoDetalhes);
  const vulcano2 = todosVirtual;

  const totalOrfaos = fisicosOrfaos.length + virtuaisOrfaos.length;

  const handleXLSX = (e) => {
    e.stopPropagation();
    exportarRazaoXLSX({ contaId, contaNome, todosFisico, todosVirtual, fisicosOrfaos, virtuaisOrfaos });
  };

  // O <td colSpan=999> herda a largura enorme da tabela de meses.
  // O div interno com position sticky + left 0 + maxWidth gruda a esquerda
  // e limita a largura a 820px, eliminando o espacamento excessivo.
  return (
    <tr>
      <td colSpan={999} className="p-0 bg-[var(--v-bg)]">
        <div style={{ position: 'sticky', left: 0, maxWidth: '820px', minWidth: 0 }}>

          {/* Barra de abas e acoes */}
          <div className="px-3 py-1.5 border-b border-[var(--v-bg)] flex items-center gap-2 flex-wrap bg-[var(--v-bg)]">
            <button
              onClick={e => { e.stopPropagation(); setAba('orfaos'); }}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest border transition-all ${aba === 'orfaos' ? 'bg-[var(--v-accent)]/20 border-[#ff4d00]/40 text-[var(--v-accent)]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent)]/70'}`}
            >
              <GitCompare size={10}/> Orfaos
              {totalOrfaos > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-[var(--v-accent)] text-black rounded-[var(--v-radius)] text-[8px] font-black">{totalOrfaos}</span>
              )}
            </button>
            <button
              onClick={e => { e.stopPropagation(); setAba('razao'); }}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest border transition-all ${aba === 'razao' ? 'bg-[#a259ff]/20 border-[#a259ff]/40 text-[var(--v-accent-5)]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent-5)]/70'}`}
            >
              <List size={10}/> Razao
              <span className="ml-1 text-[9px] font-bold text-[#333]">({todosFisico.length}Q/{todosVirtual.length}V)</span>
            </button>
            <button
              onClick={e => { e.stopPropagation(); setAba('mapa'); }}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest border transition-all ${aba === 'mapa' ? 'bg-[#34c759]/20 border-[#34c759]/40 text-[#34c759]' : 'bg-transparent border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[#34c759]/70'}`}
            >
              <CheckCircle2 size={10}/> Mapa Tabular
            </button>
            <button
              onClick={e => { e.stopPropagation(); onAgent(); }}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-[var(--v-accent)]/10 border border-[var(--v-accent)]/30 rounded text-[10px] font-black uppercase tracking-widest text-[var(--v-accent)] hover:bg-[var(--v-accent)]/20 transition-all font-mono"
            >
              <Zap size={10} className="animate-pulse"/> AGENTE IA
            </button>
            <div className="flex-1"/>
            {todosVirtualLogica.length > 0 && (
              <button
                onClick={e => { e.stopPropagation(); onRacional(); }}
                className="flex items-center gap-1.5 px-2.5 py-1 bg-[#a259ff]/15 border border-[#a259ff]/30 rounded text-[10px] font-black uppercase tracking-widest text-[var(--v-accent-5)] hover:bg-[#a259ff]/25 transition-all"
              >
                <Zap size={10}/> Racional
              </button>
            )}
            <button
              onClick={handleXLSX}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-[#34c759]/10 border border-[#34c759]/30 rounded text-[10px] font-black uppercase tracking-widest text-[var(--v-accent-3)] hover:bg-[#34c759]/20 transition-all"
            >
              <Download size={10}/> XLSX
            </button>
          </div>

          {/* Conteudo da aba */}
          {aba === 'orfaos' && (
            totalOrfaos === 0 ? (
              <div className="flex items-center gap-2 px-4 py-3 text-[var(--v-accent-3)]">
                <CheckCircle2 size={12}/>
                <span className="text-[10px] font-black uppercase tracking-widest">Nenhum orfao encontrado</span>
              </div>
            ) : (
              <div className="grid grid-cols-2 divide-x divide-[#111]">
                <div>
                  <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] flex items-center gap-2">
                    <span className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent)]">Questor s/ par no Vulcano</span>
                    {fisicosOrfaos.length > 0 && <span className="px-1 py-0.5 bg-[var(--v-accent)] text-black rounded text-[8px] font-black">{fisicosOrfaos.length}</span>}
                  </div>
                  <TabelaLancs itens={fisicosOrfaos} corNaturezaD="#34c759" corNaturezaC="#ff4d00" semLabel="Nenhum orfao no Questor"/>
                </div>
                <div>
                  <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] flex items-center gap-2">
                    <span className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-5)]">Vulcano s/ par no Questor</span>
                    {virtuaisOrfaos.length > 0 && <span className="px-1 py-0.5 bg-[#a259ff] text-black rounded text-[8px] font-black">{virtuaisOrfaos.length}</span>}
                  </div>
                  <TabelaLancs itens={virtuaisOrfaos} corNaturezaD="#a259ff" corNaturezaC="#ff9f0a" semLabel="Nenhum orfao no Vulcano"/>
                </div>
              </div>
            )
          )}

          {aba === 'razao' && (
            <div className="grid grid-cols-2 divide-x divide-[#111]">
              <div>
                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)]">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent)]">Questor ({todosFisico.length})</span>
                </div>
                <TabelaLancs itens={todosFisico} corNaturezaD="#34c759" corNaturezaC="#ff4d00" semLabel="Sem lancamentos fisicos"/>
              </div>
              <div>
                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)]">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-5)]">Vulcano ({todosVirtual.length})</span>
                </div>
                <TabelaLancs itens={todosVirtual} corNaturezaD="#a259ff" corNaturezaC="#ff9f0a" semLabel="Sem lancamentos societarios"/>
              </div>
            </div>
          )}

          {aba === 'mapa' && (
            <div className="grid grid-cols-3 divide-x divide-[#111]">
              <div>
                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] text-center">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent)]">Questor Legado ({questorManual.length})</span>
                </div>
                <TabelaLancs itens={questorManual} corNaturezaD="#34c759" corNaturezaC="#ff4d00" semLabel="—"/>
              </div>
              <div>
                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] text-center">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#a259ff]">Vulcano 1.0 (VU) ({vulcano1.length})</span>
                </div>
                <TabelaLancs itens={vulcano1} corNaturezaD="#a259ff" corNaturezaC="#ff9f0a" semLabel="—"/>
              </div>
              <div>
                <div className="px-3 py-1 bg-[var(--v-deep)] border-b border-[var(--v-bg)] text-center">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#34c759]">Vulcano 2.0 (IFRS 15) ({vulcano2.length})</span>
                </div>
                <TabelaLancs itens={vulcano2} corNaturezaD="#34c759" corNaturezaC="#a259ff" semLabel="—"/>
              </div>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

// ── Modal Agente LangGraph ───────────────────────────────────────
function AgentTerminalModal({ contaId, contaNome, onClose }) {
  const [status, setStatus] = useState('IDLE'); // IDLE, RUNNING, PAUSED, FINISHED, ERROR
  const [threadId, setThreadId] = useState(null);
  const [agentState, setAgentState] = useState(null);
  const [feedback, setFeedback] = useState('');

  // Auto trigger
  useEffect(() => {
    iniciarAgente();
  }, []);

  const iniciarAgente = async () => {
    setStatus('RUNNING');
    try {
        const res = await fetch(`${API_BASE}/api/agentes/iniciar_auditoria`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conta_alvo: `Conta ${contaId} - ${contaNome}` })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setThreadId(data.thread_id);
        setAgentState(data.state);
        setStatus(data.status === 'PAUSED_FOR_HUMAN' ? 'PAUSED' : 'FINISHED');
    } catch (err) {
        setStatus('ERROR');
    }
  };

  const enviarFeedback = async (aprovado) => {
    setStatus('RUNNING');
    try {
        const res = await fetch(`${API_BASE}/api/agentes/resumir_auditoria`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thread_id: threadId, aprovado, feedback_usuario: feedback })
        });
        const data = await res.json();
        setAgentState(data.state);
        setStatus('FINISHED');
    } catch (err) {
        setStatus('ERROR');
    }
  };

  return createPortal(
      <div className="fixed inset-0 z-[9999] bg-black/90 backdrop-blur-md flex flex-col items-center justify-center animate-in fade-in duration-300" onClick={onClose}>
        <div className="bg-[var(--v-deep)] border border-[var(--v-accent)]/50 shadow-[0_0_50px_rgba(255,77,0,0.15)] w-full h-full flex flex-col pointer-events-auto overflow-hidden" onClick={e => e.stopPropagation()}>
           {/* HEADER */}
           <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--v-accent)]/20 bg-[var(--v-accent)]/5 shrink-0">
             <div className="flex items-center gap-3">
               <Zap size={20} className="text-[var(--v-accent)] animate-pulse"/>
               <div>
                 <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-accent)]">Auditoria Autônoma — Cortex Agent</p>
                 <p className="font-mono text-xs text-[var(--v-text-bold)] mt-0.5">{contaId} <span className="font-body text-[var(--v-text-faint)]">{contaNome}</span></p>
               </div>
             </div>
             <button onClick={onClose} className="text-[var(--v-accent)] hover:text-white font-black px-2 py-1 uppercase tracking-widest text-[10px] transition-colors border border-transparent hover:border-[var(--v-accent)]/40 rounded">✕ ENCERRAR</button>
           </div>
           
           {/* BODY */}
           <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 custom-scrollbar">
              {status === 'RUNNING' && (
                <div className="flex-1 flex flex-col items-center justify-center gap-6">
                   <RefreshCw size={40} className="text-[var(--v-accent)] animate-spin"/>
                   <div className="text-center">
                       <p className="text-[var(--v-accent)] font-black uppercase tracking-widest text-[14px] animate-pulse mb-2">Agente Investigador Ativo</p>
                       <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-[var(--v-text-faint)]">Inspecionando assinaturas no Firebird SQL...</p>
                   </div>
                </div>
              )}

              {status === 'ERROR' && (
                <div className="text-[var(--v-accent)] border border-[var(--v-accent)] p-6 rounded bg-[var(--v-accent)]/10 text-center font-bold">
                   <p className="text-xs uppercase tracking-widest font-black">SYSTEM FAILURE: Connection Refused</p>
                   <p className="text-[10px] mt-2 opacity-60">Ocorreu um erro ao comunicar com a malha de agentes.</p>
                </div>
              )}

              {(status === 'PAUSED' || status === 'FINISHED') && agentState && (
                <div className="flex-1 flex flex-col gap-8 animate-in slide-in-from-bottom-4 duration-500">
                    {/* Status Message */}
                    <div className="bg-[var(--v-bg)] border border-[var(--v-border)] p-5 rounded flex flex-col gap-3">
                       <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--v-accent-3)]">Rastro de Execução (Trace Log)</h3>
                       <ul className="text-[11px] font-mono text-[var(--v-text-faint)] flex flex-col gap-1.5 opacity-80">
                           {agentState.passos_executados?.map((p, i) => (
                             <li key={i} className="flex gap-2">
                                 <span className="text-[var(--v-accent)]">›</span>
                                 <span>{p}</span>
                             </li>
                           ))}
                       </ul>
                    </div>

                    {agentState.sugestao_correcao && Object.keys(agentState.sugestao_correcao).length > 0 && (
                        <div className="bg-[var(--v-card)] border border-[var(--v-accent)]/30 p-6 rounded shadow-lg">
                           <div className="flex items-center gap-2 mb-4">
                              <div className="w-2 h-2 rounded-[var(--v-radius)] bg-[var(--v-accent-6)] animate-pulse"/>
                              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-[var(--v-accent-6)]">Veredito da IA (Human-in-the-Loop)</h3>
                           </div>
                           <p className="text-[14px] text-[var(--v-text-bold)] font-bold mb-6 leading-relaxed bg-[var(--v-deep)] p-4 rounded border border-[var(--v-border)]">{agentState.sugestao_correcao.descricao}</p>
                           <div className="grid grid-cols-2 gap-4">
                              <div className="bg-[#34c759]/5 border border-[#34c759]/20 p-4 rounded">
                                 <p className="text-[9px] font-black uppercase tracking-widest text-[#34c759] mb-1.5">Ação Recomendada</p>
                                 <p className="font-mono text-sm font-bold text-[#34c759]">{agentState.sugestao_correcao.acao}</p>
                              </div>
                              <div className="bg-[#a259ff]/5 border border-[#a259ff]/20 p-4 rounded">
                                 <p className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-5)] mb-1.5">Contrapartida (Auto-Mapping)</p>
                                 <p className="font-mono text-sm font-bold text-[var(--v-accent-5)]">{agentState.sugestao_correcao.conta_contrapartida}</p>
                              </div>
                           </div>
                        </div>
                    )}
                </div>
              )}
           </div>

           {/* FOOTER (HITL Input) */}
           {status === 'PAUSED' && (
             <div className="border-t border-[var(--v-border)] bg-[var(--v-bg)] p-6 flex flex-col gap-4 sticky bottom-0 shrink-0">
                <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-muted)]">Aguardando Avaliação Humana (HITL)</p>
                <input 
                  autoFocus
                  type="text" 
                  placeholder="Algum feedback, correção ou contexto adicional para o aprendizado do agente? (Opcional)" 
                  value={feedback} 
                  onChange={e => setFeedback(e.target.value)}
                  onKeyDown={e => e.stopPropagation()}
                  className="w-full bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-4 py-3 text-xs font-bold font-mono text-[var(--v-text-bold)] outline-none focus:border-[var(--v-accent-6)] transition-all"
                />
                <div className="flex gap-4">
                    <button onClick={() => enviarFeedback(true)} className="flex-1 bg-[#34c759]/10 hover:bg-[#34c759]/20 border border-[#34c759]/50 text-[#34c759] py-3.5 rounded-[var(--v-radius)] font-black text-xs uppercase tracking-widest transition-colors shadow-lg shadow-[#34c759]/5">
                       ✓ APROVAR TRATATIVA
                    </button>
                    <button onClick={() => enviarFeedback(false)} className="flex-1 bg-[#ff4d00]/10 hover:bg-[#ff4d00]/20 border border-[#ff4d00]/50 text-[#ff4d00] py-3.5 rounded-[var(--v-radius)] font-black text-xs uppercase tracking-widest transition-colors shadow-lg shadow-[#ff4d00]/5">
                       ✗ REJEITAR / CORRIGIR
                    </button>
                </div>
             </div>
           )}
           {status === 'FINISHED' && (
             <div className="border-t border-[#34c759]/20 bg-[#34c759]/5 p-6 text-center shrink-0">
                <p className="text-[#34c759] font-black uppercase tracking-widest text-[13px] flex justify-center items-center gap-2">
                   <CheckCircle2 size={18}/> Auditoria Deste Nodo Finalizada (Estado Persistido)
                </p>
             </div>
           )}
        </div>
      </div>,
      document.body
  );
}

// ── Linha de conta na tabela de confronto ────────────────────────────────────
function ContaConfronto({ contaId, contaNome, competencias, dadosPorMes }) {
  const [open, setOpen] = useState(false);
  const [racionalOpen, setRacionalOpen] = useState(false);
  const [agentOpen, setAgentOpen] = useState(false);

  // Contas especiais usam movimento do período (não delta de saldo) para conciliação
  const usaMovimento = CONTAS_USA_MOVIMENTO.has(String(contaId));

  // Para cada competência: soma fisico e virtual desta conta
  const porComp = competencias.map(comp => {
    const lista = dadosPorMes[comp] || {};
    const fisico   = lista.fisico?.find(r => String(r.conta) === String(contaId));
    const legado   = lista.legado?.find(r => String(r.conta) === String(contaId));
    const virtual  = lista.virtual?.find(r => String(r.conta) === String(contaId));
    // Para contas especiais, movimento físico = movimento_liquido do Questor
    // Para demais contas, movimento físico = delta de saldo (saldo_final - saldo_anterior)
    const movFisicoCalc = usaMovimento
      ? (fisico?.movimento_liquido || 0)
      : fisico ? ((fisico.saldo_final || 0) - (fisico.saldo_anterior || 0)) : 0;
    return {
      comp,
      temFisico:       !!fisico,
      usaMovimento,
      movFisico:       movFisicoCalc,
      saldoFisico:     fisico?.saldo_final          || 0,
      movVirtual:      virtual?.movimento_liquido   || 0,
      movVirtualDeb:   virtual?.movimento_debito    || 0,
      movVirtualCred:  virtual?.movimento_credito   || 0,
      saldoVirtual:    virtual?.saldo_final         || 0,
      diffMov:         (virtual?.movimento_liquido  || 0) - movFisicoCalc,
      diffSaldo:       (virtual?.saldo_final        || 0) - (fisico?.saldo_final || 0),
      detalhesFisico:  fisico?.detalhes  || [],
      detalhesVirtual: virtual?.detalhes || [],
      legadoDetalhes:  legado?.detalhes || [],
    };
  });

  // Totais do período
  const totalMovFisico   = porComp.reduce((s, c) => s + c.movFisico, 0);
  const totalMovVirtual  = porComp.reduce((s, c) => s + c.movVirtual, 0);
  const totalDiffMov     = totalMovVirtual - totalMovFisico;
  // Saldo final = último mês
  const ultimo           = porComp[porComp.length - 1] || {};
  const totalDiffSaldo   = ultimo.diffSaldo || 0;

  // Para contas especiais: divergência calculada sobre movimento; para demais: sobre saldo
  const diffParaStatus   = usaMovimento ? totalDiffMov : totalDiffSaldo;
  const temDivergencia   = abs(diffParaStatus) >= DIVERGENCIA_CORTE ||
    (!usaMovimento && abs(totalDiffMov) >= DIVERGENCIA_CORTE);

  // Só mostra contas que têm qualquer movimento em algum lado, incluindo legado
  const temQualquerDado = porComp.some(c => abs(c.movFisico) > 0 || abs(c.movVirtual) > 0 || c.saldoFisico || c.saldoVirtual || c.legadoDetalhes?.length > 0);
  if (!temQualquerDado) return null;

  // Lançamentos virtuais com logica agrupados para o Racional Global
  const racionaisAgrupados = useMemo(() => {
    const grupos = {};
    const regexVGV = /VGV \((.*?)\) \* POC \((.*?)\%\) = (.*?) - Ant \[(.*?)\]/;
    const regexCusto = /Custo Acum CC \((.*?)\) \* Fração Área \((.*?)\%\) = (.*?) - Ant \[(.*?)\]/;
    // Para simplificar, consideramos o formato US (1,000.00) fixo do backend Python.
    const pFloat = (v) => parseFloat(v.replace(/,/g, ''));
    const fmtN = (v) => v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    porComp.forEach(({ comp, detalhesVirtual }) => {
      detalhesVirtual.filter(d => d.logica).forEach(d => {
        let tipoLogica = (d.historico || '').replace(/- Unid .*$/, '').trim();
        tipoLogica = tipoLogica.replace(/\[.*?\]/g, '').trim();
        const tagNova = d.historico?.includes('[NOVA VENDA MÊS]') ? '  [NOVAS VENDAS MÊS]' : '';
        const key = `${comp}_${d.natureza}_${tipoLogica}${tagNova}`;

        if (!grupos[key]) {
          grupos[key] = {
            comp,
            natureza: d.natureza,
            historicoBase: tipoLogica,
            tag: tagNova,
            valorTotal: 0,
            qtd: 0,
            sumVgv: 0, pocFix: 0, sumRecAtual: 0, sumRecAnt: 0,
            costoAcumFix: 0, sumFracao: 0, sumCustoAtual: 0, sumCustoAnt: 0,
            isPOC: false, isCusto: false, fallbackLogica: ''
          };
        }

        const g = grupos[key];
        g.valorTotal += d.valor;
        g.qtd += 1;
        if (!g.fallbackLogica) g.fallbackLogica = d.logica.replace(/Unid .*?:/, `Exemplo Unidade:`).trim();

        if (d.logica.includes('VGV (')) {
          g.isPOC = true;
          const m = d.logica.match(regexVGV);
          if (m) {
            g.sumVgv += pFloat(m[1]);
            g.pocFix = pFloat(m[2]);
            g.sumRecAtual += pFloat(m[3]);
            g.sumRecAnt += pFloat(m[4]);
          }
        } else if (d.logica.includes('Custo Acum CC (')) {
          g.isCusto = true;
          const m = d.logica.match(regexCusto);
          if (m) {
            g.costoAcumFix = pFloat(m[1]);
            g.sumFracao += pFloat(m[2]);
            g.sumCustoAtual += pFloat(m[3]);
            g.sumCustoAnt += pFloat(m[4]);
          }
        }
      });
    });

    // Formata logika agregada
    return Object.values(grupos).map(g => {
      let logicaGlobal = '';
      if (g.isPOC && g.sumVgv > 0) {
        logicaGlobal = `Global: VGV (${fmtN(g.sumVgv)}) * POC (${g.pocFix}%) = ${fmtN(g.sumRecAtual)} - Ant [${fmtN(g.sumRecAnt)}]${g.tag}`;
      } else if (g.isCusto && g.sumFracao > 0) {
        logicaGlobal = `Global: Custo Acum CC (${fmtN(g.costoAcumFix)}) * Fração Área (${fmtN(g.sumFracao)}%) = ${fmtN(g.sumCustoAtual)} - Ant [${fmtN(g.sumCustoAnt)}]${g.tag}`;
      } else {
        logicaGlobal = `Global (Soma de ${g.qtd} Lançamentos): Lógica equivalente vista abaixo.`;
      }
      return { ...g, logicaGlobal };
    });
  }, [porComp]);

  return (
    <>
      <tr
        className={`border-b transition-colors cursor-pointer ${temDivergencia ? 'border-[#ff4d00]/10 hover:bg-[var(--v-magma-glow)]' : 'border-[var(--v-border)] hover:bg-[var(--v-card)]'}`}
        onClick={() => setOpen(o => !o)}
      >
        {/* Conta + nome */}
        <td className="px-3 py-2.5 sticky left-0 z-10 bg-[var(--v-deep)] min-w-[220px]">
          <div className="flex items-center gap-2">
            <Status diff={diffParaStatus}/>
            <span className="font-mono text-[13px] font-black text-[var(--v-accent)] shrink-0">{contaId}</span>
            <span className="text-[12px] font-bold text-[var(--v-text-faint)] truncate" title={contaNome}>{contaNome}</span>
            {usaMovimento && <span title="Conciliação por Movimento do Período" className="text-[8px] font-black uppercase tracking-widest text-[var(--v-accent-6)] border border-[#ffcc00]/30 px-1 py-0.5 rounded">MOV</span>}
            <ChevronDown size={10} className={`text-[var(--v-text-faint)] shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}/>
          </div>
        </td>

        {/* Por competência: mov fisico / mov virtual / diff */}
        {porComp.map(({ comp, movFisico, movVirtual, movVirtualDeb, movVirtualCred, diffMov, saldoFisico, saldoVirtual, temFisico }) => (
          <td key={comp} className="px-1 py-0" style={{ minWidth: '270px' }}>
            <div className="flex gap-0 h-full">
              {/* Questor */}
              <div className="flex-1 px-2 py-2.5 text-right border-r border-[var(--v-border)] flex flex-col justify-center">
                <div className="font-mono text-[12px] font-black">
                  {temFisico || abs(movFisico) > 0.01 ? (
                    <span className={movFisico == 0 ? 'text-[var(--v-text-muted)]' : movFisico >= 0 ? 'text-[var(--v-accent-3)]/80' : 'text-[var(--v-accent)]/80'}>
                      {movFisico > 0 ? '+' : ''}{fmt(movFisico)}
                    </span>
                  ) : <span className="text-[#252525]">—</span>}
                </div>
                {abs(saldoFisico) > 0.01 && (
                  <div className="text-[10px] font-bold font-mono text-[var(--v-text-faint)] mt-0.5" title="Saldo Final no Mês">
                    S: {fmt(saldoFisico)}
                  </div>
                )}
              </div>
              {/* Vulcano */}
              <div className="flex-1 px-2 py-2.5 text-right border-r border-[var(--v-border)] flex flex-col justify-center">
                <div className="font-mono text-[12px] font-black">
                  {abs(movVirtual) > 0.01 ? (
                    <span className={movVirtual >= 0 ? 'text-[var(--v-accent-5)]' : 'text-[var(--v-accent-2)]'}>
                      {movVirtual > 0 ? '+' : ''}{fmt(movVirtual)}
                    </span>
                  ) : (abs(movVirtualDeb) > 0.01 || abs(movVirtualCred) > 0.01) ? (
                    // Movimento bruto existe mas líquido = 0 (ex: reconhecimento + recebimento no mesmo mês)
                    <span className="text-[var(--v-text-faint)] text-[10px] leading-tight">
                      <span className="text-[var(--v-accent-5)]/60">D:{fmt(movVirtualDeb)}</span>
                      <br/>
                      <span className="text-[var(--v-accent-2)]/60">C:{fmt(movVirtualCred)}</span>
                    </span>
                  ) : <span className="text-[#252525]">—</span>}
                </div>
                {abs(saldoVirtual) > 0.01 && (
                  <div className="text-[10px] font-bold font-mono text-[var(--v-text-faint)] mt-0.5" title="Saldo Final no Mês (Virtual)">
                    S: {fmt(saldoVirtual)}
                  </div>
                )}
              </div>
              {/* Delta */}
              <div className="flex-1 px-2 py-2.5 text-right font-mono text-[13px] font-black">
                {abs(diffMov) < DIVERGENCIA_CORTE ? (
                  <span className="text-[#333]">✓</span>
                ) : (
                  <span style={{ color: corDiff(diffMov) }}>
                    {diffMov > 0 ? '+' : ''}{fmt(diffMov)}
                  </span>
                )}
              </div>
            </div>
          </td>
        ))}

        {/* Status Final: para contas especiais usa diffMov; para demais usa diffSaldo */}
        <td className="px-3 py-2.5 text-right min-w-[130px]">
          {abs(diffParaStatus) < DIVERGENCIA_CORTE ? (
            <div>
              <span className="text-[12px] font-black text-[var(--v-accent-3)] uppercase tracking-wider">Conciliado</span>
              {usaMovimento && <p className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-6)]/60 mt-0.5">via movimento</p>}
            </div>
          ) : (
            <div>
              <span className="font-mono text-[14px] font-black" style={{ color: corDiff(diffParaStatus) }}>
                {diffParaStatus > 0 ? '+' : ''}{fmt(diffParaStatus)}
              </span>
              <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mt-0.5">
                {usaMovimento ? 'divergência movement' : 'divergência saldo'}
              </p>
            </div>
          )}
        </td>
      </tr>

      {/* Detalhe expandido — Órfãos + Razão Completo */}
      {open && (
        <DetalheOrfaos
          porComp={porComp}
          contaId={contaId}
          contaNome={contaNome}
          todosVirtualLogica={racionaisAgrupados}
          onRacional={() => setRacionalOpen(true)}
          onAgent={() => setAgentOpen(true)}
        />
      )}

      {/* ── Modal Agente ── */}
      {agentOpen && (
         <AgentTerminalModal 
            contaId={contaId}
            contaNome={contaNome}
            onClose={() => setAgentOpen(false)}
         />
      )}

      {/* ── Modal Racional ── */}
      {racionalOpen && (
        <tr>
          <td colSpan={porComp.length + 2} className="p-0">
            <div
              className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6"
              onClick={() => setRacionalOpen(false)}
            >
              <div
                className="bg-[var(--v-deep)] border border-[#a259ff]/30 rounded-[var(--v-radius)] w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl shadow-[#a259ff]/10"
                onClick={e => e.stopPropagation()}
              >
                <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--v-border)]">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-[var(--v-accent-5)] mb-0.5">Racional de Cálculo — Vulcano Motor Societário</p>
                    <p className="text-[var(--v-text-bold)] font-black text-[15px]">
                      <span className="text-[var(--v-accent)] font-mono mr-2">{contaId}</span>{contaNome}
                    </p>
                  </div>
                  <button
                    onClick={() => setRacionalOpen(false)}
                    className="w-8 h-8 rounded bg-[var(--v-hover)] hover:bg-[var(--v-hover)] text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] font-black text-[18px] flex items-center justify-center transition-all"
                  >×</button>
                </div>
                <div className="overflow-y-auto flex-1 px-6 py-4 flex flex-col gap-3">
                  {racionaisAgrupados.map((d, i) => (
                    <div key={i} className="border border-[var(--v-border)] rounded p-4 bg-[var(--v-deep)] hover:border-[#a259ff]/20 transition-colors">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-[10px] font-black uppercase tracking-widest text-[#a259ff]">{d.comp}</span>
                        <span className="text-[10px] font-bold text-[var(--v-text-faint)]">Agregado global de {d.qtd} unidades</span>
                        <span
                          className="ml-auto text-[10px] font-black px-2 py-0.5 rounded"
                          style={{ background: d.natureza === 'D' ? '#a259ff22' : '#ff9f0a22', color: d.natureza === 'D' ? '#a259ff' : '#ff9f0a' }}
                        >
                          TOTAL {d.natureza === 'D' ? 'DÉBITO' : 'CRÉDITO'}: {fmt(d.valorTotal)}
                        </span>
                      </div>
                      <p className="text-[14px] font-black text-[var(--v-text-muted)] mb-2 mt-2">{d.historicoBase}</p>
                      
                      {d.logicaGlobal && (
                        <p className="text-[12px] font-mono text-[var(--v-accent-5)] bg-[#a259ff]/10 rounded px-3 py-2.5 border-l-2 border-[#a259ff] mb-2 leading-relaxed">
                          {d.logicaGlobal}
                        </p>
                      )}
                      
                      {!d.isPOC && !d.isCusto && d.fallbackLogica && (
                         <p className="text-[10px] font-mono text-[var(--v-text-faint)] bg-black/20 rounded px-3 py-2 border-l-2 border-[#555] opacity-70">
                           {d.fallbackLogica}
                         </p>
                      )}
                    </div>
                  ))}
                  
                  {racionaisAgrupados.length === 0 && (
                    <div className="text-center py-10 text-[var(--v-text-faint)] text-[11px] font-bold uppercase tracking-widest">
                      Nenhum racional matemático complexo para esta conta.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Painel de Conciliação Cross-Account ──────────────────────────────────────
function CrossMatchPanel({ result, onClose, empresaId }) {
  if (!result) return null;

  const [fb, setFb] = React.useState({});  // { index: {veredicto, obs, saved, loading, showObs} }
  const [kbStats, setKbStats] = React.useState(null);

  const corScore = (s) => {
    if (s >= 0.85) return '#34c759';
    if (s >= 0.65) return '#ffcc00';
    if (s >= 0.45) return '#ff9f0a';
    return '#ff4d00';
  };

  const labelScore = (s) => {
    if (s >= 0.85) return 'ALTA';
    if (s >= 0.65) return 'MÉDIA';
    if (s >= 0.45) return 'BAIXA';
    return 'RESIDUAL';
  };

  const sendFeedback = async (i, match, veredicto, obs = '', useContrapartida = false) => {
    setFb(prev => ({ ...prev, [i]: { ...prev[i], loading: true } }));
    const baseQ = match.questor_detalhe?.[0] || match.questor || {};
    const v = match.vulcano_detalhe?.[0]  || match.vulcano  || {};
    const q_conta = useContrapartida ? (match.questor_contrapartida?.conta || baseQ.conta) : baseQ.conta;
    const q_valor = useContrapartida ? (match.questor_contrapartida?.valor || baseQ.valor) : baseQ.valor;
    const q_natureza = useContrapartida ? (match.questor_contrapartida?.natureza || baseQ.natureza) : baseQ.natureza;
    
    try {
      const r = await fetch(`${API_BASE}/api/auditoria/cross-match-feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id:      parseInt(empresaId) || 959,
          veredicto,
          obs,
          score_algoritmo: match.score || 0,
          q_conta:    parseInt(q_conta || 0),
          q_historico: baseQ.historico || baseQ.chave || '',
          q_valor:    parseFloat(q_valor || 0),
          q_data:     baseQ.data || '',
          q_natureza: q_natureza || '',
          v_conta:    parseInt(v.conta || 0),
          v_historico: v.historico || v.logica || '',
          v_valor:    parseFloat(v.valor || 0),
          v_data:     v.data || '',
          v_natureza: v.natureza || '',
        })
      });
      const j = await r.json();
      setFb(prev => ({ ...prev, [i]: { veredicto, obs, saved: true, loading: false, showObs: false, obsFor: null } }));
      setKbStats({ match: j.total_match, no_match: j.total_no_match, total: j.total_feedback });
    } catch (e) {
      setFb(prev => ({ ...prev, [i]: { ...prev[i], loading: false, error: String(e) } }));
    }
  };

  const handleMatchClick = (i, match, useContrapartida = false) => {
    const q = match.questor_detalhe?.[0] || match.questor || {};
    const v = match.vulcano_detalhe?.[0]  || match.vulcano  || {};
    const q_val = useContrapartida ? parseFloat(match.questor_contrapartida?.valor || 0) : parseFloat(q.valor || 0);
    const v_val = parseFloat(v.valor || 0);
    
    // Se o valor difere, exige justificativa
    if (Math.abs(q_val - v_val) > 0.01) {
      setFb(prev => ({ ...prev, [i]: { ...prev[i], showObs: true, obsFor: 'MATCH', useContra: useContrapartida, obs: '' } }));
    } else {
      sendFeedback(i, match, 'MATCH', '', useContrapartida);
    }
  };

  return (
    <div className="bg-[var(--v-bg)] border border-[#34c759]/25 rounded-[var(--v-radius)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#34c759]/15 bg-[#34c759]/5">
        <div className="flex items-center gap-3">
          <Link2 size={16} className="text-[var(--v-accent-3)]"/>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-accent-3)]">Conciliação Cross-Account — Órfãos</p>
            <p className="text-[9px] text-[var(--v-text-faint)] mt-0.5">
              {result.total_matches} par{result.total_matches !== 1 ? 'es' : ''} encontrado{result.total_matches !== 1 ? 's' : ''}
              {' '}·{' '}{result.total_orfaos_questor}Q + {result.total_orfaos_vulcano}V órfãos analisados
              {' '}· Scoring: Valor 50% + Histórico 25% + Data 15% + Conta 10%
              {kbStats && <span className="ml-2 text-[#34c759]">· KB: {kbStats.match}✓ {kbStats.no_match}✗</span>}
            </p>
          </div>
        </div>
        <button onClick={onClose} className="text-[#333] hover:text-[var(--v-text-bold)] text-xs px-2 py-1 transition-colors">✕ Fechar</button>
      </div>

      {/* Matches */}
      {result.error ? (
        <p className="p-4 text-[var(--v-accent)] text-xs font-mono">{result.error}</p>
      ) : result.matches?.length === 0 ? (
        <div className="flex items-center gap-2 px-5 py-6 text-[var(--v-text-faint)]">
          <CheckCircle2 size={14}/>
          <span className="text-[10px] font-black uppercase tracking-widest">Nenhum par candidato encontrado acima do threshold (38%)</span>
        </div>
      ) : (
        <div className="divide-y divide-[#111] max-h-[580px] overflow-y-auto">
          {result.matches.map((m, i) => {
            const cor = corScore(m.score);
            const pct = Math.round(m.score * 100);
            const state = fb[i] || {};
            const isSaved  = state.saved;
            const isMatch  = isSaved && state.veredicto === 'MATCH';
            const isNoMatch = isSaved && state.veredicto === 'NO_MATCH';
            // se veio com override do backend
            const fbVeredicto = m.feedback_veredicto;
            return (
              <div key={i} className={`px-4 py-3 hover:bg-[var(--v-deep)] transition-colors ${isMatch ? 'bg-[#34c759]/5' : isNoMatch ? 'bg-[#ff4d00]/5' : ''}`}>
                {/* Top row: score bar + badges + sugestão */}
                <div className="flex items-center gap-3 mb-2">
                  {/* Score indicator */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div className="w-[60px] h-[6px] bg-[var(--v-deep)] rounded-[var(--v-radius)] overflow-hidden">
                      <div className="h-full rounded-[var(--v-radius)]" style={{ width: `${pct}%`, backgroundColor: cor }}/>
                    </div>
                    <span className="text-[10px] font-black font-mono" style={{ color: cor }}>{pct}%</span>
                    <span className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded" style={{ color: cor, border: `1px solid ${cor}40`, background: `${cor}15` }}>{labelScore(m.score)}</span>
                  </div>

                  {/* Tipo badge */}
                  {m.tipo === 'CROSS_ACCOUNT' && (
                    <span className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 bg-[#a259ff]/15 border border-[#a259ff]/40 text-[var(--v-accent-5)] rounded">
                      ⇄ Cross-Account
                    </span>
                  )}
                  {!m.nat_match && (
                    <span className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 bg-[#ff9f0a]/15 border border-[#ff9f0a]/40 text-[var(--v-accent-2)] rounded">
                      ⚠ Nat. Invertida
                    </span>
                  )}
                  {fbVeredicto && (
                    <span className={`text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded ${fbVeredicto === 'MATCH' ? 'bg-[#34c759]/15 border border-[#34c759]/40 text-[#34c759]' : 'bg-[#ff4d00]/15 border border-[#ff4d00]/40 text-[var(--v-accent)]'}`}>
                      {fbVeredicto === 'MATCH' ? '✓ Confirmado' : '✗ Rejeitado'}
                    </span>
                  )}

                  {/* Score breakdown */}
                  <span className="text-[9px] text-[#333] font-mono ml-auto shrink-0">
                    V:{Math.round(m.score_valor*100)}% H:{Math.round(m.score_hist*100)}% D:{Math.round(m.score_data*100)}% C:{Math.round(m.score_conta*100)}%
                  </span>
                </div>

                {/* Par lado a lado */}
                  <div className="grid grid-cols-2 gap-2 text-[10px] mb-2">
                    <div className="bg-[var(--v-deep)] border border-[#ff4d00]/15 rounded p-2 flex flex-col gap-1 max-h-[140px] overflow-y-auto">
                      <p className="text-[8px] font-black uppercase tracking-widest text-[var(--v-accent)] ml-1">Questor</p>
                      {(m.questor_detalhe && m.questor_detalhe.length > 0 ? m.questor_detalhe : [m.questor]).map((q, idx) => (
                          <div key={idx} className="bg-[var(--v-deep)] p-1.5 rounded border border-[#ff4d00]/10">
                            <p className="font-mono font-bold text-[var(--v-text-faint)] text-[8px]">
                              {q.data} | c/<span className="text-[var(--v-accent)]">{q.conta}</span>
                              {q.conta_nome && <span className="text-[var(--v-text-muted)] ml-1">— {q.conta_nome}</span>}
                            </p>
                            <p className="font-bold text-[var(--v-text-muted)] truncate" title={q.historico || q.chave}>{(q.historico || q.chave || '?').slice(0,50)}</p>
                            <p className="font-black text-[var(--v-accent-3)] mt-0.5">{fmt(q.valor)} <span className="text-[var(--v-text-faint)]">{q.natureza}</span></p>
                          </div>
                      ))}
                    </div>
                    <div className="bg-[var(--v-deep)] border border-[#a259ff]/15 rounded p-2 flex flex-col gap-1 max-h-[140px] overflow-y-auto">
                      <p className="text-[8px] font-black uppercase tracking-widest text-[var(--v-accent-5)] ml-1">Vulcano</p>
                      {(m.vulcano_detalhe && m.vulcano_detalhe.length > 0 ? m.vulcano_detalhe : [m.vulcano]).map((v, idx) => (
                          <div key={idx} className="bg-[var(--v-deep)] p-1.5 rounded border border-[#a259ff]/10">
                            <p className="font-mono font-bold text-[var(--v-text-faint)] text-[8px]">
                              {v.data} | c/<span className="text-[var(--v-accent-5)]">{v.conta}</span>
                              {v.conta_nome && <span className="text-[var(--v-text-muted)] ml-1">— {v.conta_nome}</span>}
                            </p>
                            <p className="font-bold text-[var(--v-text-muted)] truncate" title={v.historico || v.logica}>{(v.historico || v.logica || '?').slice(0,50)}</p>
                            <p className="font-black text-[var(--v-accent-5)] mt-0.5">{fmt(v.valor)} <span className="text-[var(--v-text-faint)]">{v.natureza}</span></p>
                          </div>
                      ))}
                    </div>
                  </div>

                {/* Contrapartida Questor para NAT.INVERTIDA */}
                {!m.nat_match && m.questor_contrapartida && (
                  <div className="mb-2 px-1">
                    <div className="bg-[#ff9f0a]/5 border border-[#ff9f0a]/30 rounded p-2 flex justify-between items-center flex-wrap gap-2">
                      <div>
                        <p className="text-[8px] font-black uppercase tracking-widest text-[var(--v-accent-2)] mb-1">
                          ⇄ Contrapartida Questor (outro lado da partida dobrada)
                        </p>
                        <p className="text-[9px] font-mono text-[var(--v-text-muted)]">
                          c/<span className="font-black text-[var(--v-accent-2)]">{m.questor_contrapartida.conta}</span>
                          {m.questor_contrapartida.conta_nome && <span className="ml-1 text-[var(--v-text-faint)]">— {m.questor_contrapartida.conta_nome}</span>}
                          <span className="ml-3 font-black text-[var(--v-accent-3)]">{fmt(m.questor_contrapartida.valor)}</span>
                          <span className="ml-1 text-[var(--v-text-faint)]">{m.questor_contrapartida.natureza}</span>
                        </p>
                      </div>
                      {!isSaved && !fbVeredicto && (
                        <button
                          onClick={() => handleMatchClick(i, m, true)}
                          disabled={state.loading}
                          className="shrink-0 px-2 py-1 text-[8px] font-black uppercase text-[#34c759] bg-[#34c759]/10 border border-[#34c759]/40 rounded hover:bg-[#34c759]/20 transition-all disabled:opacity-40"
                        >✓ Match pela Contrapartida</button>
                      )}
                    </div>
                  </div>
                )}

                {/* Sugestão */}
                <p className="text-[9px] font-bold text-[var(--v-text-faint)] italic px-1 mb-2">{m.sugestao}</p>

                {/* ── FEEDBACK BUTTONS ──────────────────────────────────── */}
                {!isSaved && !fbVeredicto ? (
                  <div className="flex flex-col gap-2 mt-1 w-full relative">
                    <div className="flex items-center gap-2">
                      <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] shrink-0">Auditor:</span>
                      <button
                        onClick={() => handleMatchClick(i, m, false)}
                        disabled={state.loading}
                        className="flex items-center gap-1 px-3 py-1 text-[9px] font-black uppercase tracking-wider rounded bg-[#34c759]/15 border border-[#34c759]/40 text-[#34c759] hover:bg-[#34c759]/30 transition-all disabled:opacity-40"
                      >
                        {state.loading ? '...' : '✓ Match'}
                      </button>
                      <button
                        onClick={() => setFb(prev => ({ ...prev, [i]: { ...prev[i], showObs: true, obsFor: 'NO_MATCH', useContra: false } }))}
                        disabled={state.loading}
                        className="flex items-center gap-1 px-3 py-1 text-[9px] font-black uppercase tracking-wider rounded bg-[#ff4d00]/15 border border-[#ff4d00]/40 text-[var(--v-accent)] hover:bg-[#ff4d00]/30 transition-all disabled:opacity-40"
                      >
                        ✗ Não Match
                      </button>
                    </div>

                    {state.showObs && (
                      <div className="flex items-center gap-2 w-full mt-1 bg-[var(--v-deep)] p-2 rounded border border-[#111]">
                        <input
                          autoFocus
                          type="text"
                          placeholder={state.obsFor === 'MATCH' ? "Justifique a diferença de valores..." : "Observação (opcional)..."}
                          value={state.obs || ''}
                          onChange={e => setFb(prev => ({ ...prev, [i]: { ...prev[i], obs: e.target.value } }))}
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                              if (state.obsFor === 'MATCH' && !(state.obs || '').trim()) return;
                              sendFeedback(i, m, state.obsFor || 'NO_MATCH', state.obs || '', state.useContra);
                            }
                          }}
                          className={`flex-1 bg-[var(--v-bg)] border rounded px-2 py-1 text-[10px] text-[var(--v-text-muted)] outline-none ${state.obsFor === 'MATCH' ? 'border-[#34c759]/40 focus:border-[#34c759]' : 'border-[#ff4d00]/30 focus:border-[#ff4d00]/60'}`}
                        />
                        <button
                          disabled={state.obsFor === 'MATCH' && !(state.obs || '').trim()}
                          onClick={() => sendFeedback(i, m, state.obsFor || 'NO_MATCH', state.obs || '', state.useContra)}
                          className={`px-2 py-1 text-[9px] font-black uppercase tracking-widest rounded transition-all disabled:opacity-40 ${state.obsFor === 'MATCH' ? 'text-[#34c759] bg-[#34c759]/20 border border-[#34c759]/40 hover:bg-[#34c759]/40' : 'text-[var(--v-accent)] bg-[#ff4d00]/20 border border-[#ff4d00]/40 hover:bg-[#ff4d00]/40'}`}
                        >
                          Salvar
                        </button>
                        <button
                          onClick={() => setFb(prev => ({ ...prev, [i]: { ...prev[i], showObs: false, obsFor: null } }))}
                          className="px-1.5 py-1 text-[9px] text-[#333] hover:text-[var(--v-text-bold)] transition-colors"
                        >✕</button>
                      </div>
                    )}
                  </div>
                ) : isSaved ? (
                  <div className={`flex items-center gap-2 px-2 py-1 rounded text-[9px] font-black ${isMatch ? 'bg-[#34c759]/10 text-[#34c759]' : 'bg-[#ff4d00]/10 text-[var(--v-accent)]'}`}>
                    {isMatch ? '✓ Salvo como MATCH' : '✗ Salvo como NÃO MATCH'}
                    {state.obs && <span className="font-normal text-[var(--v-text-faint)] ml-1">— {state.obs}</span>}
                    <span className="ml-auto text-[#333] font-normal">na base de conhecimento</span>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── MAIN VIEW ────────────────────────────────────────────────────────────────
export const AuditoriaERPView = ({ selectedEmpresa }) => {
  const now = new Date();
  const mesAtual = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

  const [periodoInicio, setPeriodoInicio] = useState(mesAtual);
  const [periodoFim,    setPeriodoFim]    = useState(mesAtual);
  const [filtroEmpId,   setFiltroEmpId]   = useState('');
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [empsLoading,     setEmpsLoading]     = useState(false);
  // dados: { 'YYYY-MM': { fisico: [...contas], virtual: [...contas] } }
  const [dadosPorMes, setDadosPorMes] = useState({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  // ── Diagnóstico IA (PyOD + DuckDB + KMeans + LevelShift) ──────────────────
  const [diagData,    setDiagData]    = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [showDiag,    setShowDiag]    = useState(false);

  // ── Conciliação Cross-Account (Fuzzy Orphan Matching) ────────────────────
  const [crossData,    setCrossData]    = useState(null);
  const [crossLoading, setCrossLoading] = useState(false);
  const [usePgVector, setUsePgVector] = useState(true);
  const [showCross,    setShowCross]    = useState(false);

  // ── Carrega empreendimentos na montagem ──────────────────────────────────
  useEffect(() => {
    if (!selectedEmpresa) return;
    setEmpsLoading(true);
    fetch(`${API_BASE}/api/empreendimentos/basico?empresa_id=${selectedEmpresa}`)
      .then(r => r.json())
      .then(j => { setEmpreendimentos(j.empreendimentos || []); setEmpsLoading(false); })
      .catch(() => setEmpsLoading(false));
  }, [selectedEmpresa]);

  const competencias = useMemo(() => {
    try { return gerarCompetencias(periodoInicio, periodoFim); }
    catch { return [periodoInicio]; }
  }, [periodoInicio, periodoFim]);

  const periodoValido = competencias.length <= 18;

  // ── Fetch: virtual via contabilizacoes, fisico via saldo-contas direto no LCTOCTB ──
  const fetchTudo = useCallback(async () => {
    if (!selectedEmpresa || !periodoValido) return;
    setLoading(true);
    setError('');
    const novos = {};
    try {
      const virtuaisPorMes = {};
      const legadosPorMes = {};
      const contasGlobais = new Set();

      // PASS 1: Busca Virtual para todos os meses (SEQUENCIAL PARA EVITAR LOCK DO FIREBIRD)
      for (const comp of competencias) {
        const [ano, mes] = comp.split('-').map(Number);

        // 1. Busca virtual (motor societário Vulcano)
        let urlV = `${API_BASE}/api/questor/contabilizacoes?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}`;
        if (filtroEmpId) urlV += `&empreendimento_id=${filtroEmpId}`;
        const respV = await fetch(urlV);
        const jsonV = await respV.json();

        const accVirtual = {};
        const accLegado = {};
        const mergeConta = (source, acc) => {
          (source || []).forEach(c => {
            const k = String(c.conta);
            if (!acc[k]) {
              acc[k] = { ...c, detalhes: [...(c.detalhes || [])] };
            } else {
              acc[k].saldo_anterior    = (acc[k].saldo_anterior    || 0) + (c.saldo_anterior    || 0);
              acc[k].movimento_debito  = (acc[k].movimento_debito  || 0) + (c.movimento_debito  || 0);
              acc[k].movimento_credito = (acc[k].movimento_credito || 0) + (c.movimento_credito || 0);
              acc[k].movimento_liquido = (acc[k].movimento_liquido || 0) + (c.movimento_liquido || 0);
              acc[k].saldo_final       = (acc[k].saldo_final       || 0) + (c.saldo_final       || 0);
              acc[k].detalhes.push(...(c.detalhes || []));
            }
          });
        };
        (jsonV.data || []).forEach(emp => {
          mergeConta(emp.contas_virtuais, accVirtual);
          mergeConta(emp.contas_legado, accLegado);
          
          (emp.contas_virtuais || []).forEach(c => { if (!c.is_caixa) contasGlobais.add(c.conta); });
          (emp.contas_legado || []).forEach(c => contasGlobais.add(c.conta));
        });
        const virtualList = Object.values(accVirtual);
        const legadoList = Object.values(accLegado);
        
        virtualList.forEach(c => { if (!c.is_caixa) contasGlobais.add(c.conta); });
        virtuaisPorMes[comp] = virtualList;
        legadosPorMes[comp] = legadoList;
      }

      // PASS 2: Busca Físico (Questor) para todos os meses usando a união de todas as contas
      const contasCsv = Array.from(contasGlobais).join(',');
      
      if (contasGlobais.size > 0) {
        for (const comp of competencias) {
          const [ano, mes] = comp.split('-').map(Number);
          
          let fisicoList = [];
          let urlF = `${API_BASE}/api/questor/saldo-contas?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}&contas=${contasCsv}`;
          // NÃO passar empreendimento_id aqui: as contas em contasGlobais já são
          // específicas do empreendimento (ex: 5665=RECEITA STUTTGART). Filtrar por CC no
          // Questor LCTOGER causa perda de dados quando o Questor não taggeia por CC.
          
          try {
            const respF = await fetch(urlF);
            const jsonF = await respF.json();
            fisicoList = jsonF.data || [];
          } catch (ef) {
            console.warn('saldo-contas error:', ef);
          }

          novos[comp] = {
            fisico:  fisicoList,
            virtual: virtuaisPorMes[comp],
            legado:  legadosPorMes[comp],
          };
        }
      } else {
        competencias.forEach(comp => {
          novos[comp] = { fisico: [], virtual: [], legado: [] };
        });
      }

      setDadosPorMes(novos);
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  }, [selectedEmpresa, competencias, filtroEmpId]);

  const fetchDiagnostico = async () => {
    if (!selectedEmpresa) return;

    // Converte os dados carregados na auditoria para a lista de DiagnosticoRow
    const linhasMap = {};
    Object.entries(dadosPorMes).forEach(([comp, data]) => {
      // 1. Processa virtuais
      (data.virtual || []).forEach(v => {
        const key = `${v.conta}_${comp}`;
        if (!linhasMap[key]) {
          linhasMap[key] = { conta_id: parseInt(v.conta), competencia: comp, saldo_q: 0, saldo_v: 0, n_lanc_q: 0, n_lanc_v: 0 };
        }
        linhasMap[key].saldo_v += (v.movimento_liquido || 0);
        linhasMap[key].n_lanc_v += 1;
      });
      // 2. Processa físicos
      (data.fisico || []).forEach(f => {
        const key = `${f.conta}_${comp}`;
        if (!linhasMap[key]) {
          linhasMap[key] = { conta_id: parseInt(f.conta), competencia: comp, saldo_q: 0, saldo_v: 0, n_lanc_q: 0, n_lanc_v: 0 };
        }
        linhasMap[key].saldo_q += (f.movimento_liquido || 0);
        linhasMap[key].n_lanc_q += 1;
      });
    });

    const linhas = Object.values(linhasMap).filter(r => r.conta_id > 0);

    if (linhas.length === 0) {
      setDiagData({ error: 'Nenhum dado carregado. Clique em "Auditar" primeiro.' });
      setShowDiag(true);
      return;
    }

    setDiagLoading(true);
    setShowDiag(true);
    try {
      const r = await fetch(`${API_BASE}/api/auditoria/diagnostico`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa),
          linhas: linhas,
          top_n: 20
        })
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Erro no diagnóstico');
      setDiagData(j);
    } catch (e) {
      setDiagData({ error: String(e) });
    }
    setDiagLoading(false);
  };

  // ── Coleta TODOS os orfaos de TODAS as contas e chama o backend ────────────
  const fetchCrossMatch = async () => {
    if (!selectedEmpresa || Object.keys(dadosPorMes).length === 0) return;
    setCrossLoading(true);
    setShowCross(true);
    setCrossData(null);

    // Agrega detalhes por conta em todos os meses
    const detFisicoPorConta  = {};
    const detVirtualPorConta = {};

    Object.values(dadosPorMes).forEach(({ fisico, virtual }) => {
      (fisico || []).forEach(f => {
        const n = parseInt(f.conta);
        if (!n || isNaN(n)) return; // guarda: ignora contas inválidas
        const cid = String(n);
        if (!detFisicoPorConta[cid]) detFisicoPorConta[cid] = [];
        (f.detalhes || []).forEach(d => detFisicoPorConta[cid].push({ ...d, conta: n }));
      });
      (virtual || []).forEach(v => {
        const n = parseInt(v.conta);
        if (!n || isNaN(n)) return;
        const cid = String(n);
        if (!detVirtualPorConta[cid]) detVirtualPorConta[cid] = [];
        (v.detalhes || []).forEach(d => detVirtualPorConta[cid].push({ ...d, conta: n }));
      });
    });

    // Calcula órfãos conta a conta e agrega
    const orfaosQ = [];
    const orfaosV = [];
    const todasContas = new Set([
      ...Object.keys(detFisicoPorConta),
      ...Object.keys(detVirtualPorConta),
    ]);

    todasContas.forEach(cid => {
      const n = parseInt(cid);
      if (!n || isNaN(n)) return;
      const noGrupoApto = CONTAS_GRUPO_APTO.has(n);
      const fisLista = detFisicoPorConta[cid]  || [];
      const virLista = detVirtualPorConta[cid] || [];
      const { fisicosOrfaos, virtuaisOrfaos } = calcularOrfaos(fisLista, virLista);
      // Mapeamento explícito: só campos que o backend OrfaoItem espera.
      // Para contas do grupo APTO (5653/5665/5666): só incluir se tiver APTO+número no histórico,
      // garantindo que o indexador primário existe antes de enviar ao motor de matching.
      fisicosOrfaos.forEach(o => {
        const textoOrfao = String(o.historico || '') + ' ' + String(o.chave || '');
        if (noGrupoApto && !extractAptoNum(textoOrfao)) return; // sem APTO identificado → descarta
        orfaosQ.push({
          conta:    n,
          data:     String(o.data     || ''),
          historico:String(o.historico|| ''),
          natureza: String(o.natureza || ''),
          valor:    Number(o.valor    || 0),
          chave:    String(o.chave    || ''),
          logica:   String(o.logica   || ''),
        });
      });
      virtuaisOrfaos.forEach(o => {
        const textoOrfao = String(o.historico || '') + ' ' + String(o.logica || '');
        if (noGrupoApto && !extractAptoNum(textoOrfao)) return; // sem APTO identificado → descarta
        orfaosV.push({
          conta:    n,
          data:     String(o.data     || ''),
          historico:String(o.historico|| ''),
          natureza: String(o.natureza || ''),
          valor:    Number(o.valor    || 0),
          chave:    String(o.chave    || ''),
          logica:   String(o.logica   || ''),
        });
      });
    });

    if (orfaosQ.length === 0 && orfaosV.length === 0) {
      setCrossData({ matches: [], total_matches: 0, total_orfaos_questor: 0, total_orfaos_vulcano: 0 });
      setCrossLoading(false);
      return;
    }

    try {
      const r = await fetch(`${API_BASE}/api/auditoria/concilia-orfaos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          empresa_id: parseInt(selectedEmpresa),
          orfaos_questor: orfaosQ,
          orfaos_vulcano: orfaosV,
          threshold: 0.38,
          use_pgvector: usePgVector,
        }),
      });
      const j = await r.json();
      if (!r.ok) {
        // j.detail pode ser string ou array de ValidationError Pydantic
        const msg = typeof j.detail === 'string'
          ? j.detail
          : Array.isArray(j.detail)
            ? j.detail.map(e => `${e.loc?.join('.')||''}: ${e.msg||''}`).join('; ')
            : JSON.stringify(j.detail);
        throw new Error(msg || 'Erro na conciliação cross-account');
      }
      setCrossData(j);
    } catch (e) {
      setCrossData({ error: String(e) });
    }
    setCrossLoading(false);
  };


  // ── Contas a exibir: contas com cálculo Vulcano + contas Legado ──
  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ virtual, legado }) => {
      // 1. Contas Virtuais
      (virtual || []).forEach(c => {
        if (!c.is_caixa) {
          if (!m[c.conta]) m[c.conta] = { nome: c.nome || `Conta ${c.conta}`, classif: c.classif || '9.99.99' };
        }
      });
      // 2. Contas Legado
      (legado || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = { nome: c.nome ? `${c.nome} (Vulcano 1.0)` : `Conta ${c.conta} (Vulcano 1.0)`, classif: c.classif || '9.99.99' };
      });
    });
    return m; // { contaId → nome }
  }, [dadosPorMes]);

  // ── Métricas globais — filtra fisico apenas nas contas visíveis (mapeadas + órfãs VU) ────────
  const metrics = useMemo(() => {
    let totMovFisico = 0, totMovVirtual = 0;
    let contasConciliadas = 0, contasDivergentes = 0;
    const contasVisiveisIds = Object.keys(contasMap);

    Object.values(dadosPorMes).forEach(({ fisico, virtual }) => {
      (fisico || []).filter(c => contasVisiveisIds.includes(String(c.conta)))
        .forEach(c => { totMovFisico += Math.abs(c.movimento_liquido || 0); });
      (virtual || []).forEach(c => { totMovVirtual += Math.abs(c.movimento_liquido || 0); });
    });

    Object.keys(contasMap).forEach(contaId => {
      const usaMovimento = CONTAS_USA_MOVIMENTO.has(contaId);
      let diffTotal = 0;
      competencias.forEach(comp => {
        const f = dadosPorMes[comp]?.fisico?.find( r => String(r.conta) === contaId);
        const v = dadosPorMes[comp]?.virtual?.find(r => String(r.conta) === contaId);
        if (usaMovimento) {
          // Contas especiais: compara movimento_liquido do Questor × Vulcano
          diffTotal += ((v?.movimento_liquido || 0) - (f?.movimento_liquido || 0));
        } else {
          // Demais: compara delta de saldo (saldo_final - saldo_anterior) do Questor × Vulcano
          const movF = f ? ((f.saldo_final || 0) - (f.saldo_anterior || 0)) : 0;
          diffTotal += ((v?.movimento_liquido || 0) - movF);
        }
      });
      if (abs(diffTotal) < DIVERGENCIA_CORTE) contasConciliadas++;
      else contasDivergentes++;
    });

    const diffMov   = totMovVirtual - totMovFisico;
    const pctAdh    = (contasConciliadas + contasDivergentes) > 0
      ? (contasConciliadas / (contasConciliadas + contasDivergentes)) * 100
      : 0;

    return { totMovFisico, totMovVirtual, diffMov, pctAdh, contasConciliadas, contasDivergentes };
  }, [dadosPorMes, contasMap, competencias]);

  const temDados = Object.keys(dadosPorMes).length > 0;

  return (
    <div className="flex flex-col gap-5 pb-10 text-[var(--v-text)] animate-in fade-in">
      {/* Header */}
      <div className="border-b border-[var(--v-border)] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-[var(--v-text-bold)] flex items-center gap-3 mb-1">
          <ShieldCheck className="text-[var(--v-accent)]" size={36}/> Auditoria ERP
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--v-text-faint)] font-black">
          Contas a Injetar no Questor — Calculado (Vulcano) × Registrado (Questor)
        </p>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-end bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-4">
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Período De</span>
          <input type="month" value={periodoInicio}
            onChange={e => { const v = e.target.value; setPeriodoInicio(v); if (v > periodoFim) setPeriodoFim(v); }}
            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text)] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Até</span>
          <input type="month" value={periodoFim}
            onChange={e => { const v = e.target.value; setPeriodoFim(v); if (v < periodoInicio) setPeriodoInicio(v); }}
            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text)] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>
        <div className="flex flex-col gap-1 min-w-[220px]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">
            Empreendimento {empsLoading ? '(carregando...)' : `(${empreendimentos.length})`}
          </span>
          <select value={filtroEmpId} onChange={e => setFiltroEmpId(e.target.value)}
            className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded px-3 py-2 text-[var(--v-text)] text-xs font-bold outline-none focus:border-[#ff4d00] transition-colors">
            <option value="">Todos os empreendimentos</option>
            {empreendimentos.map(e => <option key={e.id} value={String(e.id)}>{e.nome}</option>)}
          </select>
        </div>
        <div className="flex flex-col justify-end pb-0.5">
          <span className="text-[9px] font-bold text-[var(--v-text-faint)] uppercase tracking-wider">
            {competencias.length} mês{competencias.length !== 1 ? 'es' : ''}
            {!periodoValido && <span className="text-[var(--v-accent)] ml-2">⚠ máx. 18</span>}
          </span>
        </div>
        <button onClick={fetchTudo} disabled={loading || !periodoValido || !selectedEmpresa}
          className="ml-auto px-6 py-2.5 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? `Auditando ${competencias.length} meses...` : 'Auditar'}
        </button>
        <button onClick={fetchDiagnostico} disabled={diagLoading || !selectedEmpresa}
          title="Analisa Questor ↔ Vulcano com PyOD + DuckDB + KMeans (24 meses)"
          className={`px-5 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all disabled:opacity-40 border ${
            showDiag ? 'bg-[#a259ff]/20 border-[#a259ff]/60 text-[var(--v-accent-5)]' : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent-5)] hover:border-[#a259ff]/40'
          }`}>
          {diagLoading ? <Zap className="animate-spin" size={12}/> : <Zap size={12}/>}
          {diagLoading ? 'Analisando...' : '🧠 Diagnóstico IA'}
        </button>
        <button onClick={fetchCrossMatch} disabled={crossLoading || !temDados}
          title="Fuzzy matching cross-account: busca pares prováveis entre todos os lançamentos órfãos"
          className={`px-5 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all disabled:opacity-40 border ${
            showCross ? 'bg-[#34c759]/20 border-[#34c759]/60 text-[var(--v-accent-3)]' : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[var(--v-accent-3)] hover:border-[#34c759]/40'
          }`}>
          {crossLoading ? <Link2 className="animate-spin" size={12}/> : <Link2 size={12}/>}
          {crossLoading ? 'Conciliando...' : '🔗 Cross-Account'}
        </button>
        <button onClick={() => setUsePgVector(!usePgVector)}
          title="Aceleração Vetorial via PostgreSQL (Embeddings Semânticos)"
          className={`px-4 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all border ${
            usePgVector ? 'bg-[#ffcc00]/20 border-[#ffcc00]/60 text-[#ffcc00]' : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[#ffcc00] hover:border-[#ffcc00]/40'
          }`}>
          <Zap size={12}/> {usePgVector ? 'PGVector Ligado' : 'PGVector Desligado'}
        </button>
      </div>

      {error && (
        <div className="bg-[var(--v-accent)]/10 border border-[#ff4d00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={14} className="text-[var(--v-accent)] shrink-0"/>
          <p className="text-sm font-mono text-[var(--v-accent)]">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-12">
          <Zap className="animate-spin text-[var(--v-accent)]" size={28}/>
          <span className="text-xs font-black uppercase tracking-widest text-[var(--v-text-faint)]">
            Confrontando {competencias.length} competência{competencias.length > 1 ? 's' : ''}...
          </span>
        </div>
      )}

      {/* ── Painel Diagnóstico IA ── */}
      {showDiag && (
        <div className="bg-[var(--v-deep)] border border-[#a259ff]/30 rounded-[var(--v-radius)] overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-[#a259ff]/20 bg-[#a259ff]/5">
            <div className="flex items-center gap-3">
              <span className="text-[var(--v-accent-5)] text-lg">🧠</span>
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-[var(--v-accent-5)]">Diagnóstico IA — Causa Raiz Questor ↔ Vulcano</p>
                <p className="text-[9px] text-[var(--v-text-faint)] mt-0.5">PyOD IsolationForest · DuckDB · KMeans · LevelShift (24 meses)</p>
              </div>
            </div>
            <button onClick={() => setShowDiag(false)} className="text-[var(--v-text-faint)] hover:text-[var(--v-text-bold)] text-xs px-2 py-1">✕ Fechar</button>
          </div>

          {diagLoading && (
            <div className="flex items-center justify-center gap-3 py-10">
              <span className="text-[var(--v-accent-5)] animate-spin text-xl">⚡</span>
              <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">Rodando PyOD + DuckDB + KMeans...</span>
            </div>
          )}

          {diagData?.error && (
            <div className="p-4 text-[var(--v-accent)] text-xs font-mono">{diagData.error}</div>
          )}

          {diagData && !diagData.error && !diagLoading && (
            <div className="p-4 space-y-4">
              {/* Summary banner */}
              <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-3 text-[10px] text-[var(--v-text-muted)] font-mono">
                {diagData.summary}
              </div>

              {/* Tabela de contas */}
              <div className="overflow-auto max-h-[500px] custom-scrollbar">
                <table className="w-full text-left border-collapse text-[10px]">
                  <thead className="sticky top-0 bg-[var(--v-deep)] border-b border-[var(--v-border)]">
                    <tr>
                      <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest">Conta</th>
                      <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest w-32">Score IA</th>
                      <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest">Padrão</th>
                      <th className="p-2 text-right text-[var(--v-text-faint)] font-black uppercase tracking-widest">Δ Médio</th>
                      <th className="p-2 text-right text-[var(--v-text-faint)] font-black uppercase tracking-widest">Δ Máx</th>
                      <th className="p-2 text-center text-[var(--v-text-faint)] font-black uppercase tracking-widest">Meses Div.</th>
                      <th className="p-2 text-[var(--v-text-faint)] font-black uppercase tracking-widest">Mudança de Nível</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(diagData.contas || []).map((c, i) => {
                      const score = c.anomaly_score ?? 0;
                      const isAnomalia = c.anomaly_label === 'ANOMALIA';
                      const scoreColor = score > 0.7 ? '#ff4d00' : score > 0.4 ? '#ffcc00' : '#34c759';
                      const padraoColors = {
                        'Exato': 'bg-[#34c759]/10 text-[var(--v-accent-3)] border-[#34c759]/30',
                        'Lag Temporal': 'bg-[#007aff]/10 text-[var(--v-accent-4)] border-[#007aff]/30',
                        'Percentual Fixo': 'bg-[#ffcc00]/10 text-[var(--v-accent-6)] border-[#ffcc00]/30',
                        'Caótico': 'bg-[var(--v-accent)]/10 text-[var(--v-accent)] border-[#ff4d00]/30',
                      };
                      const padraoClass = padraoColors[c.padrao] || 'bg-[var(--v-hover)] text-[var(--v-text-faint)] border-[var(--v-border)]';
                      return (
                        <React.Fragment key={i}>
                        <tr className={`border-b border-[var(--v-bg)] ${isAnomalia ? 'bg-[var(--v-accent)]/5' : ''} hover:bg-[var(--v-deep)]/60`}>
                          <td className="p-2">
                            <div className="font-black text-[var(--v-text-bold)] text-[10px]">{c.conta_nome}</div>
                            <div className="text-[var(--v-text-faint)] font-mono text-[9px]">#{c.conta_id}</div>
                          </td>
                          <td className="p-2">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-[var(--v-hover)] rounded-[var(--v-radius)] h-1.5">
                                <div className="h-1.5 rounded-[var(--v-radius)] transition-all" style={{width:`${score*100}%`, background: scoreColor}}/>
                              </div>
                              <span className="font-black text-[9px] font-mono" style={{color: scoreColor}}>{Math.round(score*100)}%</span>
                            </div>
                            {isAnomalia && <span className="text-[8px] text-[var(--v-accent)] font-black uppercase">⚠ Anômalo</span>}
                          </td>
                          <td className="p-2">
                            <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border uppercase tracking-widest ${padraoClass}`}>
                              {c.padrao}
                            </span>
                          </td>
                          <td className="p-2 text-right font-mono text-[var(--v-text)]">
                            {c.media_delta >= 0 ? '+' : ''}{c.media_delta?.toLocaleString('pt-BR', {minimumFractionDigits:0, maximumFractionDigits:0})}
                          </td>
                          <td className="p-2 text-right font-mono text-[var(--v-accent)]">
                            {c.max_delta_abs?.toLocaleString('pt-BR', {minimumFractionDigits:0, maximumFractionDigits:0})}
                          </td>
                          <td className="p-2 text-center">
                            <span className={`font-black text-[9px] ${c.pct_meses_divergentes > 80 ? 'text-[var(--v-accent)]' : c.pct_meses_divergentes > 40 ? 'text-[var(--v-accent-6)]' : 'text-[var(--v-accent-3)]'}`}>
                              {c.pct_meses_divergentes?.toFixed(0)}%
                            </span>
                          </td>
                          <td className="p-2">
                            {c.level_shift ? (
                              <div>
                                <span className="text-[var(--v-accent-6)] font-black text-[9px]">⬆ {c.level_shift.competencia}</span>
                                <div className="text-[8px] text-[var(--v-text-faint)] mt-0.5 font-mono">
                                  {c.level_shift.delta_antes?.toFixed(0)} → {c.level_shift.delta_depois?.toFixed(0)}
                                </div>
                              </div>
                            ) : (
                              <span className="text-[#333] text-[8px]">—</span>
                            )}
                          </td>
                        </tr>
                        {c.causa_raiz && (
                          <tr className="bg-[#a259ff]/10">
                            <td colSpan={7} className="p-3 border-b border-[#a259ff]/20">
                              <div className="flex items-start gap-2">
                                <Zap className="text-[var(--v-accent-5)] shrink-0 mt-0.5" size={12}/>
                                <div className="max-w-2xl">
                                  <div className="text-[10px] font-black text-[var(--v-accent-5)] uppercase tracking-widest mb-1">Diagnóstico IA (Causa Raiz)</div>
                                  <div className="text-[11px] text-[#ddd] leading-relaxed mb-1.5">{c.causa_raiz}</div>
                                  {c.recomendacao && (
                                    <div className="text-[10px] text-[var(--v-accent-6)]"><span className="font-bold">Recomendação:</span> {c.recomendacao}</div>
                                  )}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Painel Cross-Account (Fuzzy Orphan Matching) ── */}
      {showCross && (
        crossLoading ? (
          <div className="bg-[var(--v-bg)] border border-[#34c759]/25 rounded-[var(--v-radius)] p-8 flex items-center justify-center gap-3">
            <Link2 className="animate-spin text-[var(--v-accent-3)]" size={18}/>
            <span className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-faint)]">
              Coletando órfãos e calculando fuzzy scores cross-account...
            </span>
          </div>
        ) : (
          <CrossMatchPanel result={crossData} onClose={() => setShowCross(false)} empresaId={selectedEmpresa}/>
        )
      )}

      {/* ── Cards de resumo ── */}
      {!loading && temDados && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Gauge conciliação */}
          <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-4 col-span-1">
            <p className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2">Conciliação Global</p>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-black font-mono" style={{ color: metrics.pctAdh >= 95 ? '#34c759' : metrics.pctAdh >= 80 ? '#ffcc00' : '#ff4d00' }}>
                {metrics.pctAdh.toFixed(0)}%
              </span>
              <span className="text-[10px] text-[var(--v-text-faint)] mb-0.5 font-bold">aderência</span>
            </div>
            <div className="w-full bg-[var(--v-hover)] rounded-[var(--v-radius)] h-1.5 mt-2">
              <div className="h-1.5 rounded-[var(--v-radius)] transition-all" style={{
                width: `${metrics.pctAdh}%`,
                background: metrics.pctAdh >= 95 ? '#34c759' : metrics.pctAdh >= 80 ? '#ffcc00' : '#ff4d00'
              }}/>
            </div>
            <p className="text-[9px] text-[var(--v-text-faint)] mt-2 font-bold">
              <span className="text-[var(--v-accent-3)]">{metrics.contasConciliadas}</span> OK · <span className="text-[var(--v-accent)]">{metrics.contasDivergentes}</span> div.
            </p>
          </div>

          {[
            { label: 'Movimento Total Questor', val: metrics.totMovFisico,  cor: '#ff4d00' },
            { label: 'Movimento Total Vulcano', val: metrics.totMovVirtual, cor: '#a259ff' },
            { label: 'Diferença de Movimento',  val: metrics.diffMov, cor: corDiff(metrics.diffMov) },
          ].map(m => (
            <div key={m.label} className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded p-4">
              <p className="text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] mb-2">{m.label}</p>
              <p className="text-xl font-black font-mono" style={{ color: m.cor }}>{fmt(m.val)}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Tabela de confronto ── */}
      {!loading && Object.keys(contasMap).length > 0 && (
        <div className="bg-[var(--v-deep)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
          {/* Cabeçalho da legenda de colunas */}
          <div className="px-4 py-3 border-b border-[var(--v-border)] flex items-center gap-4 flex-wrap">
            <h3 className="text-[10px] font-black uppercase tracking-widest text-[var(--v-text-bold)]">Confronto por Conta</h3>
            <div className="flex gap-4 ml-auto text-[9px] font-bold uppercase tracking-widest">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[var(--v-radius)] bg-[var(--v-accent)] inline-block"/>
                <span className="text-[var(--v-accent)]">Questor (Físico)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[var(--v-radius)] bg-[#a259ff] inline-block"/>
                <span className="text-[var(--v-accent-5)]">Vulcano (Societário)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[var(--v-radius)] bg-[#ffcc00] inline-block"/>
                <span className="text-[var(--v-accent-6)]">Δ Divergência</span>
              </span>
            </div>
          </div>

          <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 300px)' }}>
            <table
              className="w-full border-collapse"
              style={{ minWidth: `${220 + competencias.length * 270 + 140}px` }}
            >
              <thead>
                <tr className="bg-[var(--v-deep)]">
                  {/* Conta */}
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[var(--v-text-faint)] border-b border-[var(--v-border)] sticky left-0 top-0 z-30 bg-[var(--v-deep)] min-w-[220px]">
                    Conta
                  </th>
                  {/* Grupos de colunas por mês */}
                  {competencias.map(comp => (
                    <th key={comp} colSpan={1} className="p-0 border-b border-[var(--v-border)] border-l border-[var(--v-bg)] sticky top-0 z-20 bg-[var(--v-deep)]"
                        style={{ minWidth: '270px' }}>
                      <div className="px-2 py-1.5 text-center text-[9px] font-black uppercase tracking-widest text-[var(--v-text-faint)] border-b border-[var(--v-border)]">
                        {labelMes(comp)}
                      </div>
                      <div className="flex text-[7px] font-black uppercase tracking-widest text-[#333]">
                        <div className="flex-1 px-2 py-1 text-right border-r border-[var(--v-bg)]">Questor</div>
                        <div className="flex-1 px-2 py-1 text-right border-r border-[var(--v-bg)]">Vulcano</div>
                        <div className="flex-1 px-2 py-1 text-right">Δ</div>
                      </div>
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-[var(--v-text-bold)] border-b border-[var(--v-border)] sticky top-0 z-20 bg-[var(--v-deep)] min-w-[130px]">
                    Status Final
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(contasMap)
                  .sort((a, b) => {
                    const classA = a[1].classif;
                    const classB = b[1].classif;
                    if (classA !== classB) return classA.localeCompare(classB);
                    return a[1].nome.localeCompare(b[1].nome);
                  })
                  .map(([contaId, contaObj]) => (
                  <ContaConfronto
                    key={contaId}
                    contaId={contaId}
                    contaNome={contaObj.nome}
                    competencias={competencias}
                    dadosPorMes={dadosPorMes}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !temDados && !error && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <div className="w-16 h-16 bg-[var(--v-accent)]/10 border border-[#ff4d00]/20 rounded flex items-center justify-center">
            <ShieldCheck className="text-[var(--v-accent)]" size={28}/>
          </div>
          <p className="font-black uppercase tracking-widest text-[var(--v-text-bold)] text-sm">
            Selecione o período e clique em Auditar
          </p>
          <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest max-w-sm">
            Confronta movimento e saldo do Questor (físico) com o motor societário Vulcano (POC + tributos) conta a conta
          </p>
          <button onClick={fetchTudo} disabled={!selectedEmpresa}
            className="mt-2 px-6 py-3 bg-[var(--v-accent)] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40">
            <Zap size={13}/> Iniciar Auditoria
          </button>
        </div>
      )}
    </div>
  );
};
