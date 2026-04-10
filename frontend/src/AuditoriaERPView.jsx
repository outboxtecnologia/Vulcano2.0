import React, { useState, useEffect, useMemo, useCallback } from 'react';
import * as XLSX from 'xlsx';
import {
  ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle,
  RefreshCw, Building2, ChevronDown, ChevronUp, ArrowRight,
  Download, GitCompare, List, Link2
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const fmt = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 }).format(v || 0);
const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

// ── helpers ──────────────────────────────────────────────────────────────────
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

const abs = (v) => Math.abs(v || 0);
const DIVERGENCIA_CORTE = 0.5; // abaixo disso, considera ok

// Contas que usam movimentação do período para conciliação (não delta de saldo)
const CONTAS_USA_MOVIMENTO = new Set([
  '1545','1552','1553','1556',
  '2829','2830',
  '4828','4829','4958','4995'
]);

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
  if (abs(diff) < DIVERGENCIA_CORTE) return <CheckCircle2 size={14} className="text-[#34c759] shrink-0"/>;
  if (abs(diff) < 5000)             return <AlertTriangle size={14} className="text-[#ffcc00] shrink-0"/>;
  return <XCircle size={14} className="text-[#ff4d00] shrink-0"/>;
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
            <tr key={i} className="border-b border-[#0e0e0e] hover:bg-[#0a0a0a]">
              <td className="px-2 py-1 font-mono font-bold text-[#555] whitespace-nowrap overflow-hidden">{d.data}</td>
              <td className="px-2 py-1 overflow-hidden" title={hist}>
                <div className="truncate font-bold text-[#555]">{hist}</div>
              </td>
              <td className="px-2 py-1 text-center font-black text-[12px] overflow-hidden" style={{ color: d.natureza === 'D' ? corNaturezaD : corNaturezaC }}>{d.natureza}</td>
              <td className="px-2 py-1 text-right font-mono font-black text-[#888] whitespace-nowrap overflow-hidden">{fmt(d.valor)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// ── Painel de orfaos (expande ao clicar na linha da conta) ───────────────────
function DetalheOrfaos({ porComp, contaId, contaNome, todosVirtualLogica, onRacional }) {
  const [aba, setAba] = useState('orfaos');

  const todosFisico  = porComp.flatMap(c => c.detalhesFisico);
  const todosVirtual = porComp.flatMap(c => c.detalhesVirtual);

  const { fisicosOrfaos, virtuaisOrfaos } = useMemo(
    () => calcularOrfaos(todosFisico, todosVirtual),
    [todosFisico.length, todosVirtual.length]
  );

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
      <td colSpan={999} className="p-0 bg-[#060606]">
        <div style={{ position: 'sticky', left: 0, maxWidth: '820px', minWidth: 0 }}>

          {/* Barra de abas e acoes */}
          <div className="px-3 py-1.5 border-b border-[#111] flex items-center gap-2 flex-wrap bg-[#060606]">
            <button
              onClick={e => { e.stopPropagation(); setAba('orfaos'); }}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest border transition-all ${aba === 'orfaos' ? 'bg-[#ff4d00]/20 border-[#ff4d00]/40 text-[#ff4d00]' : 'bg-transparent border-[#222] text-[#444] hover:text-[#ff4d00]/70'}`}
            >
              <GitCompare size={10}/> Orfaos
              {totalOrfaos > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-[#ff4d00] text-black rounded-full text-[8px] font-black">{totalOrfaos}</span>
              )}
            </button>
            <button
              onClick={e => { e.stopPropagation(); setAba('razao'); }}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest border transition-all ${aba === 'razao' ? 'bg-[#a259ff]/20 border-[#a259ff]/40 text-[#a259ff]' : 'bg-transparent border-[#222] text-[#444] hover:text-[#a259ff]/70'}`}
            >
              <List size={10}/> Razao
              <span className="ml-1 text-[9px] font-bold text-[#333]">({todosFisico.length}Q/{todosVirtual.length}V)</span>
            </button>
            <div className="flex-1"/>
            {todosVirtualLogica.length > 0 && (
              <button
                onClick={e => { e.stopPropagation(); onRacional(); }}
                className="flex items-center gap-1.5 px-2.5 py-1 bg-[#a259ff]/15 border border-[#a259ff]/30 rounded text-[10px] font-black uppercase tracking-widest text-[#a259ff] hover:bg-[#a259ff]/25 transition-all"
              >
                <Zap size={10}/> Racional
              </button>
            )}
            <button
              onClick={handleXLSX}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-[#34c759]/10 border border-[#34c759]/30 rounded text-[10px] font-black uppercase tracking-widest text-[#34c759] hover:bg-[#34c759]/20 transition-all"
            >
              <Download size={10}/> XLSX
            </button>
          </div>

          {/* Conteudo da aba */}
          {aba === 'orfaos' && (
            totalOrfaos === 0 ? (
              <div className="flex items-center gap-2 px-4 py-3 text-[#34c759]">
                <CheckCircle2 size={12}/>
                <span className="text-[10px] font-black uppercase tracking-widest">Nenhum orfao encontrado</span>
              </div>
            ) : (
              <div className="grid grid-cols-2 divide-x divide-[#111]">
                <div>
                  <div className="px-3 py-1 bg-[#0d0d0d] border-b border-[#111] flex items-center gap-2">
                    <span className="text-[9px] font-black uppercase tracking-widest text-[#ff4d00]">Questor s/ par no Vulcano</span>
                    {fisicosOrfaos.length > 0 && <span className="px-1 py-0.5 bg-[#ff4d00] text-black rounded text-[8px] font-black">{fisicosOrfaos.length}</span>}
                  </div>
                  <TabelaLancs itens={fisicosOrfaos} corNaturezaD="#34c759" corNaturezaC="#ff4d00" semLabel="Nenhum orfao no Questor"/>
                </div>
                <div>
                  <div className="px-3 py-1 bg-[#0d0d0d] border-b border-[#111] flex items-center gap-2">
                    <span className="text-[9px] font-black uppercase tracking-widest text-[#a259ff]">Vulcano s/ par no Questor</span>
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
                <div className="px-3 py-1 bg-[#0d0d0d] border-b border-[#111]">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#ff4d00]">Questor ({todosFisico.length})</span>
                </div>
                <TabelaLancs itens={todosFisico} corNaturezaD="#34c759" corNaturezaC="#ff4d00" semLabel="Sem lancamentos fisicos"/>
              </div>
              <div>
                <div className="px-3 py-1 bg-[#0d0d0d] border-b border-[#111]">
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#a259ff]">Vulcano ({todosVirtual.length})</span>
                </div>
                <TabelaLancs itens={todosVirtual} corNaturezaD="#a259ff" corNaturezaC="#ff9f0a" semLabel="Sem lancamentos societarios"/>
              </div>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

// ── Linha de conta na tabela de confronto ────────────────────────────────────
function ContaConfronto({ contaId, contaNome, competencias, dadosPorMes }) {
  const [open, setOpen] = useState(false);
  const [racionalOpen, setRacionalOpen] = useState(false);

  // Contas especiais usam movimento do período (não delta de saldo) para conciliação
  const usaMovimento = CONTAS_USA_MOVIMENTO.has(String(contaId));

  // Para cada competência: soma fisico e virtual desta conta
  const porComp = competencias.map(comp => {
    const lista = dadosPorMes[comp] || {};
    const fisico   = lista.fisico?.find(r => String(r.conta) === String(contaId));
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

  // Só mostra contas que têm qualquer movimento em algum lado
  const temQualquerDado = porComp.some(c => abs(c.movFisico) > 0 || abs(c.movVirtual) > 0 || c.saldoFisico || c.saldoVirtual);
  if (!temQualquerDado) return null;

  // Todos os lançamentos virtuais com logica (para o Racional)
  const todosVirtualLogica = porComp.flatMap(({ comp, detalhesVirtual }) =>
    detalhesVirtual.filter(d => d.logica).map(d => ({ ...d, comp }))
  );

  return (
    <>
      <tr
        className={`border-b transition-colors cursor-pointer ${temDivergencia ? 'border-[#ff4d00]/10 hover:bg-[#1a0800]' : 'border-[#1a1a1a] hover:bg-[#141414]'}`}
        onClick={() => setOpen(o => !o)}
      >
        {/* Conta + nome */}
        <td className="px-3 py-2.5 sticky left-0 z-10 bg-[#0d0d0d] min-w-[220px]">
          <div className="flex items-center gap-2">
            <Status diff={diffParaStatus}/>
            <span className="font-mono text-[13px] font-black text-[#ff4d00] shrink-0">{contaId}</span>
            <span className="text-[12px] font-bold text-[#666] truncate" title={contaNome}>{contaNome}</span>
            {usaMovimento && <span title="Conciliação por Movimento do Período" className="text-[8px] font-black uppercase tracking-widest text-[#ffcc00] border border-[#ffcc00]/30 px-1 py-0.5 rounded">MOV</span>}
            <ChevronDown size={10} className={`text-[#444] shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}/>
          </div>
        </td>

        {/* Por competência: mov fisico / mov virtual / diff */}
        {porComp.map(({ comp, movFisico, movVirtual, movVirtualDeb, movVirtualCred, diffMov, saldoFisico, saldoVirtual, temFisico }) => (
          <td key={comp} className="px-1 py-0" style={{ minWidth: '270px' }}>
            <div className="flex gap-0 h-full">
              {/* Questor */}
              <div className="flex-1 px-2 py-2.5 text-right border-r border-[#1a1a1a] flex flex-col justify-center">
                <div className="font-mono text-[12px] font-black">
                  {temFisico || abs(movFisico) > 0.01 ? (
                    <span className={movFisico == 0 ? 'text-[#888]' : movFisico >= 0 ? 'text-[#34c759]/80' : 'text-[#ff4d00]/80'}>
                      {movFisico > 0 ? '+' : ''}{fmt(movFisico)}
                    </span>
                  ) : <span className="text-[#252525]">—</span>}
                </div>
                {abs(saldoFisico) > 0.01 && (
                  <div className="text-[10px] font-bold font-mono text-[#555] mt-0.5" title="Saldo Final no Mês">
                    S: {fmt(saldoFisico)}
                  </div>
                )}
              </div>
              {/* Vulcano */}
              <div className="flex-1 px-2 py-2.5 text-right border-r border-[#1a1a1a] flex flex-col justify-center">
                <div className="font-mono text-[12px] font-black">
                  {abs(movVirtual) > 0.01 ? (
                    <span className={movVirtual >= 0 ? 'text-[#a259ff]' : 'text-[#ff9f0a]'}>
                      {movVirtual > 0 ? '+' : ''}{fmt(movVirtual)}
                    </span>
                  ) : (abs(movVirtualDeb) > 0.01 || abs(movVirtualCred) > 0.01) ? (
                    // Movimento bruto existe mas líquido = 0 (ex: reconhecimento + recebimento no mesmo mês)
                    <span className="text-[#555] text-[10px] leading-tight">
                      <span className="text-[#a259ff]/60">D:{fmt(movVirtualDeb)}</span>
                      <br/>
                      <span className="text-[#ff9f0a]/60">C:{fmt(movVirtualCred)}</span>
                    </span>
                  ) : <span className="text-[#252525]">—</span>}
                </div>
                {abs(saldoVirtual) > 0.01 && (
                  <div className="text-[10px] font-bold font-mono text-[#555] mt-0.5" title="Saldo Final no Mês (Virtual)">
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
              <span className="text-[12px] font-black text-[#34c759] uppercase tracking-wider">Conciliado</span>
              {usaMovimento && <p className="text-[9px] font-black uppercase tracking-widest text-[#ffcc00]/60 mt-0.5">via movimento</p>}
            </div>
          ) : (
            <div>
              <span className="font-mono text-[14px] font-black" style={{ color: corDiff(diffParaStatus) }}>
                {diffParaStatus > 0 ? '+' : ''}{fmt(diffParaStatus)}
              </span>
              <p className="text-[10px] font-black uppercase tracking-widest text-[#555] mt-0.5">
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
          todosVirtualLogica={todosVirtualLogica}
          onRacional={() => setRacionalOpen(true)}
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
                className="bg-[#0d0d0d] border border-[#a259ff]/30 rounded-lg w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl shadow-[#a259ff]/10"
                onClick={e => e.stopPropagation()}
              >
                <div className="flex items-center justify-between px-6 py-4 border-b border-[#1a1a1a]">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-widest text-[#a259ff] mb-0.5">Racional de Cálculo — Vulcano Motor Societário</p>
                    <p className="text-white font-black text-[15px]">
                      <span className="text-[#ff4d00] font-mono mr-2">{contaId}</span>{contaNome}
                    </p>
                  </div>
                  <button
                    onClick={() => setRacionalOpen(false)}
                    className="w-8 h-8 rounded bg-[#1a1a1a] hover:bg-[#222] text-[#666] hover:text-white font-black text-[18px] flex items-center justify-center transition-all"
                  >×</button>
                </div>
                <div className="overflow-y-auto flex-1 px-6 py-4 flex flex-col gap-3">
                  {todosVirtualLogica.map((d, i) => (
                    <div key={i} className="border border-[#1e1e1e] rounded p-4 bg-[#0a0a0a] hover:border-[#a259ff]/20 transition-colors">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-[9px] font-black uppercase tracking-widest text-[#555]">{d.comp} · {d.data}</span>
                        <span
                          className="text-[10px] font-black px-2 py-0.5 rounded"
                          style={{ background: d.natureza === 'D' ? '#a259ff22' : '#ff9f0a22', color: d.natureza === 'D' ? '#a259ff' : '#ff9f0a' }}
                        >
                          {d.natureza === 'D' ? 'DÉBITO' : 'CRÉDITO'} {fmt(d.valor)}
                        </span>
                      </div>
                      <p className="text-[12px] font-bold text-[#888] mb-1">{d.historico}</p>
                      {d.logica && (
                        <p className="text-[11px] font-mono text-[#a259ff]/70 bg-[#a259ff]/5 rounded px-3 py-2 border-l-2 border-[#a259ff]/30">
                          {d.logica}
                        </p>
                      )}
                    </div>
                  ))}
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
function CrossMatchPanel({ result, onClose }) {
  if (!result) return null;

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

  return (
    <div className="bg-[#090909] border border-[#34c759]/25 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#34c759]/15 bg-[#34c759]/5">
        <div className="flex items-center gap-3">
          <Link2 size={16} className="text-[#34c759]"/>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-[#34c759]">Conciliação Cross-Account — Órfãos</p>
            <p className="text-[9px] text-[#555] mt-0.5">
              {result.total_matches} par{result.total_matches !== 1 ? 'es' : ''} encontrado{result.total_matches !== 1 ? 's' : ''}
              {' '}·{' '}{result.total_orfaos_questor}Q + {result.total_orfaos_vulcano}V órfãos analisados
              {' '}· Scoring: Valor 50% + Histórico 25% + Data 15% + Conta 10%
            </p>
          </div>
        </div>
        <button onClick={onClose} className="text-[#333] hover:text-white text-xs px-2 py-1 transition-colors">✕ Fechar</button>
      </div>

      {/* Matches */}
      {result.error ? (
        <p className="p-4 text-[#ff4d00] text-xs font-mono">{result.error}</p>
      ) : result.matches?.length === 0 ? (
        <div className="flex items-center gap-2 px-5 py-6 text-[#555]">
          <CheckCircle2 size={14}/>
          <span className="text-[10px] font-black uppercase tracking-widest">Nenhum par candidato encontrado acima do threshold (38%)</span>
        </div>
      ) : (
        <div className="divide-y divide-[#111] max-h-[520px] overflow-y-auto">
          {result.matches.map((m, i) => {
            const cor = corScore(m.score);
            const pct = Math.round(m.score * 100);
            return (
              <div key={i} className="px-4 py-3 hover:bg-[#0d0d0d] transition-colors">
                {/* Top row: score bar + badges + sugestão */}
                <div className="flex items-center gap-3 mb-2">
                  {/* Score indicator */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div className="w-[60px] h-[6px] bg-[#111] rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: cor }}/>
                    </div>
                    <span className="text-[10px] font-black font-mono" style={{ color: cor }}>{pct}%</span>
                    <span className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded" style={{ color: cor, border: `1px solid ${cor}40`, background: `${cor}15` }}>{labelScore(m.score)}</span>
                  </div>

                  {/* Tipo badge */}
                  {m.tipo === 'CROSS_ACCOUNT' && (
                    <span className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 bg-[#a259ff]/15 border border-[#a259ff]/40 text-[#a259ff] rounded">
                      ⇄ Cross-Account
                    </span>
                  )}
                  {!m.nat_match && (
                    <span className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 bg-[#ff9f0a]/15 border border-[#ff9f0a]/40 text-[#ff9f0a] rounded">
                      ⚠ Nat. Invertida
                    </span>
                  )}

                  {/* Score breakdown */}
                  <span className="text-[9px] text-[#333] font-mono ml-auto shrink-0">
                    V:{Math.round(m.score_valor*100)}% H:{Math.round(m.score_hist*100)}% D:{Math.round(m.score_data*100)}% C:{Math.round(m.score_conta*100)}%
                  </span>
                </div>

                {/* Par lado a lado */}
                  <div className="grid grid-cols-2 gap-2 text-[10px] mb-2">
                    <div className="bg-[#0a0a0a] border border-[#ff4d00]/15 rounded p-2 flex flex-col gap-1 max-h-[140px] overflow-y-auto">
                      <p className="text-[8px] font-black uppercase tracking-widest text-[#ff4d00] ml-1">Questor</p>
                      {(m.questor_detalhe && m.questor_detalhe.length > 0 ? m.questor_detalhe : [m.questor]).map((q, idx) => (
                          <div key={idx} className="bg-[#111] p-1.5 rounded border border-[#ff4d00]/10">
                            <p className="font-mono font-bold text-[#666] text-[8px]">{q.data} | c/{q.conta}</p>
                            <p className="font-bold text-[#aaa] truncate" title={q.historico || q.chave}>{(q.historico || q.chave || '?').slice(0,50)}</p>
                            <p className="font-black text-[#34c759] mt-0.5">{fmt(q.valor)} <span className="text-[#444]">{q.natureza}</span></p>
                          </div>
                      ))}
                    </div>
                    <div className="bg-[#0a0a0a] border border-[#a259ff]/15 rounded p-2 flex flex-col gap-1 max-h-[140px] overflow-y-auto">
                      <p className="text-[8px] font-black uppercase tracking-widest text-[#a259ff] ml-1">Vulcano</p>
                      {(m.vulcano_detalhe && m.vulcano_detalhe.length > 0 ? m.vulcano_detalhe : [m.vulcano]).map((v, idx) => (
                          <div key={idx} className="bg-[#111] p-1.5 rounded border border-[#a259ff]/10">
                            <p className="font-mono font-bold text-[#666] text-[8px]">{v.data} | c/{v.conta}</p>
                            <p className="font-bold text-[#aaa] truncate" title={v.historico || v.logica}>{(v.historico || v.logica || '?').slice(0,50)}</p>
                            <p className="font-black text-[#a259ff] mt-0.5">{fmt(v.valor)} <span className="text-[#444]">{v.natureza}</span></p>
                          </div>
                      ))}
                    </div>
                  </div>

                {/* Sugestão */}
                <p className="text-[9px] font-bold text-[#555] italic px-1">{m.sugestao}</p>
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
        (jsonV.data || []).forEach(emp => mergeConta(emp.contas_virtuais, accVirtual));
        const virtualList = Object.values(accVirtual);
        
        virtualList.forEach(c => contasGlobais.add(c.conta));
        virtuaisPorMes[comp] = virtualList;
      }

      // PASS 2: Busca Físico (Questor) para todos os meses usando a união de todas as contas
      const contasCsv = Array.from(contasGlobais).join(',');
      
      if (contasGlobais.size > 0) {
        for (const comp of competencias) {
          const [ano, mes] = comp.split('-').map(Number);
          
          let fisicoList = [];
          let urlF = `${API_BASE}/api/questor/saldo-contas?empresa_id=${selectedEmpresa}&mes=${mes}&ano=${ano}&contas=${contasCsv}`;
          if (filtroEmpId) urlF += `&empreendimento_id=${filtroEmpId}`;
          
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
          };
        }
      } else {
        competencias.forEach(comp => {
          novos[comp] = { fisico: [], virtual: [] };
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
      const fisLista = detFisicoPorConta[cid]  || [];
      const virLista = detVirtualPorConta[cid] || [];
      const { fisicosOrfaos, virtuaisOrfaos } = calcularOrfaos(fisLista, virLista);
      // Mapeamento explícito: só campos que o backend OrfaoItem espera
      fisicosOrfaos.forEach(o => orfaosQ.push({
        conta:    n,
        data:     String(o.data     || ''),
        historico:String(o.historico|| ''),
        natureza: String(o.natureza || ''),
        valor:    Number(o.valor    || 0),
        chave:    String(o.chave    || ''),
        logica:   String(o.logica   || ''),
      }));
      virtuaisOrfaos.forEach(o => orfaosV.push({
        conta:    n,
        data:     String(o.data     || ''),
        historico:String(o.historico|| ''),
        natureza: String(o.natureza || ''),
        valor:    Number(o.valor    || 0),
        chave:    String(o.chave    || ''),
        logica:   String(o.logica   || ''),
      }));
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


  // ── Apenas contas que o Vulcano calculou para injeção (contas_virtuais) ──
  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ virtual }) => {
      (virtual || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta}`;
      });
    });
    return m; // { contaId → nome } — apenas contas com lançamento societário
  }, [dadosPorMes]);

  // ── Métricas globais — filtra fisico apenas nas contas que geramos ────────
  const metrics = useMemo(() => {
    let totMovFisico = 0, totMovVirtual = 0;
    let contasConciliadas = 0, contasDivergentes = 0;
    const contasVirtualIds = Object.keys(contasMap);

    Object.values(dadosPorMes).forEach(({ fisico, virtual }) => {
      // Questor: só as contas que o Vulcano calcula
      (fisico || []).filter(c => contasVirtualIds.includes(String(c.conta)))
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
    <div className="flex flex-col gap-5 pb-10 text-[#e5e2e1] animate-in fade-in">
      {/* Header */}
      <div className="border-b border-[#222] pb-4">
        <h2 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3 mb-1">
          <ShieldCheck className="text-[#ff4d00]" size={36}/> Auditoria ERP
        </h2>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#555] font-black">
          Contas a Injetar no Questor — Calculado (Vulcano) × Registrado (Questor)
        </p>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-end bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Período De</span>
          <input type="month" value={periodoInicio}
            onChange={e => { const v = e.target.value; setPeriodoInicio(v); if (v > periodoFim) setPeriodoFim(v); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">Até</span>
          <input type="month" value={periodoFim}
            onChange={e => { const v = e.target.value; setPeriodoFim(v); if (v < periodoInicio) setPeriodoInicio(v); }}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-mono outline-none focus:border-[#ff4d00] transition-colors [color-scheme:dark]"/>
        </div>
        <div className="flex flex-col gap-1 min-w-[220px]">
          <span className="text-[8px] font-black uppercase tracking-widest text-[#555]">
            Empreendimento {empsLoading ? '(carregando...)' : `(${empreendimentos.length})`}
          </span>
          <select value={filtroEmpId} onChange={e => setFiltroEmpId(e.target.value)}
            className="bg-[#111] border border-[#222] rounded px-3 py-2 text-[#ccc] text-xs font-bold outline-none focus:border-[#ff4d00] transition-colors">
            <option value="">Todos os empreendimentos</option>
            {empreendimentos.map(e => <option key={e.id} value={String(e.id)}>{e.nome}</option>)}
          </select>
        </div>
        <div className="flex flex-col justify-end pb-0.5">
          <span className="text-[9px] font-bold text-[#444] uppercase tracking-wider">
            {competencias.length} mês{competencias.length !== 1 ? 'es' : ''}
            {!periodoValido && <span className="text-[#ff4d00] ml-2">⚠ máx. 18</span>}
          </span>
        </div>
        <button onClick={fetchTudo} disabled={loading || !periodoValido || !selectedEmpresa}
          className="ml-auto px-6 py-2.5 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
          {loading ? <Zap className="animate-spin" size={13}/> : <RefreshCw size={13}/>}
          {loading ? `Auditando ${competencias.length} meses...` : 'Auditar'}
        </button>
        <button onClick={fetchDiagnostico} disabled={diagLoading || !selectedEmpresa}
          title="Analisa Questor ↔ Vulcano com PyOD + DuckDB + KMeans (24 meses)"
          className={`px-5 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all disabled:opacity-40 border ${
            showDiag ? 'bg-[#a259ff]/20 border-[#a259ff]/60 text-[#a259ff]' : 'bg-[#111] border-[#333] text-[#555] hover:text-[#a259ff] hover:border-[#a259ff]/40'
          }`}>
          {diagLoading ? <Zap className="animate-spin" size={12}/> : <Zap size={12}/>}
          {diagLoading ? 'Analisando...' : '🧠 Diagnóstico IA'}
        </button>
        <button onClick={fetchCrossMatch} disabled={crossLoading || !temDados}
          title="Fuzzy matching cross-account: busca pares prováveis entre todos os lançamentos órfãos"
          className={`px-5 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all disabled:opacity-40 border ${
            showCross ? 'bg-[#34c759]/20 border-[#34c759]/60 text-[#34c759]' : 'bg-[#111] border-[#333] text-[#555] hover:text-[#34c759] hover:border-[#34c759]/40'
          }`}>
          {crossLoading ? <Link2 className="animate-spin" size={12}/> : <Link2 size={12}/>}
          {crossLoading ? 'Conciliando...' : '🔗 Cross-Account'}
        </button>
      </div>

      {error && (
        <div className="bg-[#ff4d00]/10 border border-[#ff4d00]/30 rounded p-3 flex items-center gap-3">
          <AlertTriangle size={14} className="text-[#ff4d00] shrink-0"/>
          <p className="text-sm font-mono text-[#ff4d00]">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-12">
          <Zap className="animate-spin text-[#ff4d00]" size={28}/>
          <span className="text-xs font-black uppercase tracking-widest text-[#555]">
            Confrontando {competencias.length} competência{competencias.length > 1 ? 's' : ''}...
          </span>
        </div>
      )}

      {/* ── Painel Diagnóstico IA ── */}
      {showDiag && (
        <div className="bg-[#0a0a0a] border border-[#a259ff]/30 rounded-lg overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-[#a259ff]/20 bg-[#a259ff]/5">
            <div className="flex items-center gap-3">
              <span className="text-[#a259ff] text-lg">🧠</span>
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-[#a259ff]">Diagnóstico IA — Causa Raiz Questor ↔ Vulcano</p>
                <p className="text-[9px] text-[#555] mt-0.5">PyOD IsolationForest · DuckDB · KMeans · LevelShift (24 meses)</p>
              </div>
            </div>
            <button onClick={() => setShowDiag(false)} className="text-[#555] hover:text-white text-xs px-2 py-1">✕ Fechar</button>
          </div>

          {diagLoading && (
            <div className="flex items-center justify-center gap-3 py-10">
              <span className="text-[#a259ff] animate-spin text-xl">⚡</span>
              <span className="text-[10px] font-black uppercase tracking-widest text-[#555]">Rodando PyOD + DuckDB + KMeans...</span>
            </div>
          )}

          {diagData?.error && (
            <div className="p-4 text-[#ff4d00] text-xs font-mono">{diagData.error}</div>
          )}

          {diagData && !diagData.error && !diagLoading && (
            <div className="p-4 space-y-4">
              {/* Summary banner */}
              <div className="bg-[#111] border border-[#222] rounded p-3 text-[10px] text-[#888] font-mono">
                {diagData.summary}
              </div>

              {/* Tabela de contas */}
              <div className="overflow-auto max-h-[500px] custom-scrollbar">
                <table className="w-full text-left border-collapse text-[10px]">
                  <thead className="sticky top-0 bg-[#0d0d0d] border-b border-[#222]">
                    <tr>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest">Conta</th>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest w-32">Score IA</th>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest">Padrão</th>
                      <th className="p-2 text-right text-[#555] font-black uppercase tracking-widest">Δ Médio</th>
                      <th className="p-2 text-right text-[#555] font-black uppercase tracking-widest">Δ Máx</th>
                      <th className="p-2 text-center text-[#555] font-black uppercase tracking-widest">Meses Div.</th>
                      <th className="p-2 text-[#555] font-black uppercase tracking-widest">Mudança de Nível</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(diagData.contas || []).map((c, i) => {
                      const score = c.anomaly_score ?? 0;
                      const isAnomalia = c.anomaly_label === 'ANOMALIA';
                      const scoreColor = score > 0.7 ? '#ff4d00' : score > 0.4 ? '#ffcc00' : '#34c759';
                      const padraoColors = {
                        'Exato': 'bg-[#34c759]/10 text-[#34c759] border-[#34c759]/30',
                        'Lag Temporal': 'bg-[#007aff]/10 text-[#007aff] border-[#007aff]/30',
                        'Percentual Fixo': 'bg-[#ffcc00]/10 text-[#ffcc00] border-[#ffcc00]/30',
                        'Caótico': 'bg-[#ff4d00]/10 text-[#ff4d00] border-[#ff4d00]/30',
                      };
                      const padraoClass = padraoColors[c.padrao] || 'bg-[#222] text-[#555] border-[#333]';
                      return (
                        <React.Fragment key={i}>
                        <tr className={`border-b border-[#111] ${isAnomalia ? 'bg-[#ff4d00]/5' : ''} hover:bg-[#111]/60`}>
                          <td className="p-2">
                            <div className="font-black text-white text-[10px]">{c.conta_nome}</div>
                            <div className="text-[#555] font-mono text-[9px]">#{c.conta_id}</div>
                          </td>
                          <td className="p-2">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-[#1a1a1a] rounded-full h-1.5">
                                <div className="h-1.5 rounded-full transition-all" style={{width:`${score*100}%`, background: scoreColor}}/>
                              </div>
                              <span className="font-black text-[9px] font-mono" style={{color: scoreColor}}>{Math.round(score*100)}%</span>
                            </div>
                            {isAnomalia && <span className="text-[8px] text-[#ff4d00] font-black uppercase">⚠ Anômalo</span>}
                          </td>
                          <td className="p-2">
                            <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border uppercase tracking-widest ${padraoClass}`}>
                              {c.padrao}
                            </span>
                          </td>
                          <td className="p-2 text-right font-mono text-[#ccc]">
                            {c.media_delta >= 0 ? '+' : ''}{c.media_delta?.toLocaleString('pt-BR', {minimumFractionDigits:0, maximumFractionDigits:0})}
                          </td>
                          <td className="p-2 text-right font-mono text-[#ff4d00]">
                            {c.max_delta_abs?.toLocaleString('pt-BR', {minimumFractionDigits:0, maximumFractionDigits:0})}
                          </td>
                          <td className="p-2 text-center">
                            <span className={`font-black text-[9px] ${c.pct_meses_divergentes > 80 ? 'text-[#ff4d00]' : c.pct_meses_divergentes > 40 ? 'text-[#ffcc00]' : 'text-[#34c759]'}`}>
                              {c.pct_meses_divergentes?.toFixed(0)}%
                            </span>
                          </td>
                          <td className="p-2">
                            {c.level_shift ? (
                              <div>
                                <span className="text-[#ffcc00] font-black text-[9px]">⬆ {c.level_shift.competencia}</span>
                                <div className="text-[8px] text-[#555] mt-0.5 font-mono">
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
                                <Zap className="text-[#a259ff] shrink-0 mt-0.5" size={12}/>
                                <div className="max-w-2xl">
                                  <div className="text-[10px] font-black text-[#a259ff] uppercase tracking-widest mb-1">Diagnóstico IA (Causa Raiz)</div>
                                  <div className="text-[11px] text-[#ddd] leading-relaxed mb-1.5">{c.causa_raiz}</div>
                                  {c.recomendacao && (
                                    <div className="text-[10px] text-[#ffcc00]"><span className="font-bold">Recomendação:</span> {c.recomendacao}</div>
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
          <div className="bg-[#090909] border border-[#34c759]/25 rounded-lg p-8 flex items-center justify-center gap-3">
            <Link2 className="animate-spin text-[#34c759]" size={18}/>
            <span className="text-[10px] font-black uppercase tracking-widest text-[#555]">
              Coletando órfãos e calculando fuzzy scores cross-account...
            </span>
          </div>
        ) : (
          <CrossMatchPanel result={crossData} onClose={() => setShowCross(false)}/>
        )
      )}

      {/* ── Cards de resumo ── */}
      {!loading && temDados && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Gauge conciliação */}
          <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4 col-span-1">
            <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-2">Conciliação Global</p>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-black font-mono" style={{ color: metrics.pctAdh >= 95 ? '#34c759' : metrics.pctAdh >= 80 ? '#ffcc00' : '#ff4d00' }}>
                {metrics.pctAdh.toFixed(0)}%
              </span>
              <span className="text-[10px] text-[#555] mb-0.5 font-bold">aderência</span>
            </div>
            <div className="w-full bg-[#1a1a1a] rounded-full h-1.5 mt-2">
              <div className="h-1.5 rounded-full transition-all" style={{
                width: `${metrics.pctAdh}%`,
                background: metrics.pctAdh >= 95 ? '#34c759' : metrics.pctAdh >= 80 ? '#ffcc00' : '#ff4d00'
              }}/>
            </div>
            <p className="text-[9px] text-[#444] mt-2 font-bold">
              <span className="text-[#34c759]">{metrics.contasConciliadas}</span> OK · <span className="text-[#ff4d00]">{metrics.contasDivergentes}</span> div.
            </p>
          </div>

          {[
            { label: 'Movimento Total Questor', val: metrics.totMovFisico,  cor: '#ff4d00' },
            { label: 'Movimento Total Vulcano', val: metrics.totMovVirtual, cor: '#a259ff' },
            { label: 'Diferença de Movimento',  val: metrics.diffMov, cor: corDiff(metrics.diffMov) },
          ].map(m => (
            <div key={m.label} className="bg-[#0d0d0d] border border-[#1e1e1e] rounded p-4">
              <p className="text-[8px] font-black uppercase tracking-widest text-[#555] mb-2">{m.label}</p>
              <p className="text-xl font-black font-mono" style={{ color: m.cor }}>{fmt(m.val)}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Tabela de confronto ── */}
      {!loading && Object.keys(contasMap).length > 0 && (
        <div className="bg-[#0d0d0d] border border-[#1e1e1e] rounded-sm overflow-hidden">
          {/* Cabeçalho da legenda de colunas */}
          <div className="px-4 py-3 border-b border-[#1a1a1a] flex items-center gap-4 flex-wrap">
            <h3 className="text-[10px] font-black uppercase tracking-widest text-white">Confronto por Conta</h3>
            <div className="flex gap-4 ml-auto text-[9px] font-bold uppercase tracking-widest">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#ff4d00] inline-block"/>
                <span className="text-[#ff4d00]">Questor (Físico)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#a259ff] inline-block"/>
                <span className="text-[#a259ff]">Vulcano (Societário)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#ffcc00] inline-block"/>
                <span className="text-[#ffcc00]">Δ Divergência</span>
              </span>
            </div>
          </div>

          <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 300px)' }}>
            <table
              className="w-full border-collapse"
              style={{ minWidth: `${220 + competencias.length * 270 + 140}px` }}
            >
              <thead>
                <tr className="bg-[#111]">
                  {/* Conta */}
                  <th className="px-3 py-2 text-left text-[8px] font-black uppercase tracking-widest text-[#444] border-b border-[#1a1a1a] sticky left-0 top-0 z-30 bg-[#111] min-w-[220px]">
                    Conta
                  </th>
                  {/* Grupos de colunas por mês */}
                  {competencias.map(comp => (
                    <th key={comp} colSpan={1} className="p-0 border-b border-[#1a1a1a] border-l border-[#111] sticky top-0 z-20 bg-[#111]"
                        style={{ minWidth: '270px' }}>
                      <div className="px-2 py-1.5 text-center text-[9px] font-black uppercase tracking-widest text-[#666] border-b border-[#222]">
                        {labelMes(comp)}
                      </div>
                      <div className="flex text-[7px] font-black uppercase tracking-widest text-[#333]">
                        <div className="flex-1 px-2 py-1 text-right border-r border-[#111]">Questor</div>
                        <div className="flex-1 px-2 py-1 text-right border-r border-[#111]">Vulcano</div>
                        <div className="flex-1 px-2 py-1 text-right">Δ</div>
                      </div>
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right text-[8px] font-black uppercase tracking-widest text-white border-b border-[#1a1a1a] sticky top-0 z-20 bg-[#111] min-w-[130px]">
                    Status Final
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(contasMap).map(([contaId, contaNome]) => (
                  <ContaConfronto
                    key={contaId}
                    contaId={contaId}
                    contaNome={contaNome}
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
          <div className="w-16 h-16 bg-[#ff4d00]/10 border border-[#ff4d00]/20 rounded flex items-center justify-center">
            <ShieldCheck className="text-[#ff4d00]" size={28}/>
          </div>
          <p className="font-black uppercase tracking-widest text-white text-sm">
            Selecione o período e clique em Auditar
          </p>
          <p className="text-[10px] text-[#444] uppercase tracking-widest max-w-sm">
            Confronta movimento e saldo do Questor (físico) com o motor societário Vulcano (POC + tributos) conta a conta
          </p>
          <button onClick={fetchTudo} disabled={!selectedEmpresa}
            className="mt-2 px-6 py-3 bg-[#ff4d00] text-black text-[9px] font-black uppercase tracking-widest rounded hover:bg-white transition-all flex items-center gap-2 disabled:opacity-40">
            <Zap size={13}/> Iniciar Auditoria
          </button>
        </div>
      )}
    </div>
  );
};
