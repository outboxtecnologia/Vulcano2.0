import React, { useState, useEffect } from 'react';
import { UploadCloud, CheckCircle2, ChevronRight, FileSpreadsheet, Database, Sparkles, Save, ArrowUpRight, Download, X, Search, Terminal, AlertCircle, Trash2, Settings, Zap, RefreshCw } from 'lucide-react';
import { API_BASE } from './apiBase';

const TARGET_SCHEMAS = {
  VENDAS: [
    { value: 'DATA_VENDA',          label: 'Data da Venda' },
    { value: 'NUMERO_CONTRATO',     label: 'Número do Contrato' },
    { value: 'CLIENTE_NOME',        label: 'Nome do Cliente' },
    { value: 'CLIENTE_CPF_CNPJ',    label: 'CPF / CNPJ' },
    { value: 'EMPREENDIMENTO',      label: 'Empreendimento' },
    { value: 'UNIDADE',             label: 'Unidade' },
    { value: 'BLOCO',               label: 'Bloco' },
    { value: 'VGV',                 label: 'VGV (Valor Geral de Vendas)' },
    { value: 'AREA',                label: 'Área (m²)' },
    { value: 'FORMA_PAGAMENTO',     label: 'Forma de Pagamento' },
    { value: 'CORRETOR',            label: 'Corretor' },
    { value: 'STATUS',              label: 'Status' },
    { value: 'OBSERVACOES',         label: 'Observações' },
  ],
  RECEBIMENTOS: [
    { value: 'DATA_PAGAMENTO',      label: 'Data de Pagamento' },
    { value: 'DATA_VENCIMENTO',     label: 'Data de Vencimento' },
    { value: 'VALOR_PAGO',          label: 'Valor Pago' },
    { value: 'VALOR_PARCELA',       label: 'Valor da Parcela' },
    { value: 'ACRESCIMOS',          label: 'Acréscimos' },
    { value: 'DESCONTOS',           label: 'Descontos' },
    { value: 'NUMERO_PARCELA',      label: 'Número da Parcela' },
    { value: 'DESCRICAO',           label: 'Descrição' },
    { value: 'CLIENTE_NOME',        label: 'Nome do Cliente' },
    { value: 'CLIENTE_CPF_CNPJ',    label: 'CPF / CNPJ' },
    { value: 'EMPREENDIMENTO',      label: 'Empreendimento' },
    { value: 'UNIDADE',             label: 'Unidade' },
    { value: 'CONTRATO',            label: 'Contrato' },
    { value: 'FORMA_PAGAMENTO',     label: 'Forma de Pagamento' },
    { value: 'BANCO',               label: 'Banco' },
    { value: 'AGENCIA',             label: 'Agência' },
    { value: 'CONTA',               label: 'Conta Bancária' },
    { value: 'NOSSO_NUMERO',        label: 'Nosso Número' },
    { value: 'OBSERVACOES',         label: 'Observações' },
  ],
};

const STATUS_META = {
  JA_QUITADO:    { label: 'JÁ QUITADO',   color: 'var(--v-ok)' },
  MATCH_PERFEITO:{ label: 'MATCH',        color: 'var(--v-info)' },
  MATCH_MANUAL:  { label: 'MATCH MANUAL', color: 'var(--v-src-vu1)' },
  SEM_MATCH:     { label: 'SEM MATCH',    color: 'var(--v-accent)' },
  DIVERGENCIA:   { label: 'DIVERGÊNCIA',  color: 'var(--v-warn-hi)' },
};

export default function SmartImporter({ selectedEmpresa }) {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [columns, setColumns] = useState([]);
  const [previewData, setPreviewData] = useState([]);
  const [allRows, setAllRows] = useState([]);
  const [targetTable, setTargetTable] = useState('VENDAS');
  const [mapping, setMapping] = useState({});
  const [templates, setTemplates] = useState([]);
  
  const [matchData, setMatchData] = useState([]);
  const [matchLoading, setMatchLoading] = useState(false);
  
  const [empreendimentos, setEmpreendimentos] = useState([]);
  const [selectedEmpreendimento, setSelectedEmpreendimento] = useState('');
  const [parcelasAbertas, setParcelasAbertas] = useState([]);
  const [manualMatchModal, setManualMatchModal] = useState({ open: false, rowData: null, rowIndex: null });
  const [queueItems, setQueueItems] = useState([]);
  const [queueLoading, setQueueLoading] = useState(false);

  const loadQueue = () => {
    fetch(`${API_BASE}/api/smart-importer/queue`)
      .then(res => res.json())
      .then(data => setQueueItems(data))
      .catch(err => console.error("Erro ao carregar fila", err));
  };

  useEffect(() => {
    loadQueue();
    const interval = setInterval(loadQueue, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApproveQueue = async (queueId, target) => {
    setQueueLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/smart-importer/queue/${queueId}/approve`, { method: 'POST' });
      if (!res.ok) throw new Error("Falha ao puxar arquivo da fila");
      const data = await res.json();
      setColumns(data.columns || []);
      setPreviewData(data.preview || []);
      setAllRows(data.all_rows || data.preview || []);
      setTargetTable(target);
      setStep(2);
    } catch (err) {
      alert("Erro ao puxar da fila: " + err.message);
    } finally {
      setQueueLoading(false);
    }
  };

  const handleDeleteQueue = async (queueId) => {
    if (!window.confirm("Deseja descartar este arquivo da fila?")) return;
    try {
      await fetch(`${API_BASE}/api/smart-importer/queue/${queueId}`, { method: 'DELETE' });
      loadQueue();
    } catch (err) {
      alert("Erro ao deletar da fila.");
    }
  };


  useEffect(() => {
    fetch(`${API_BASE}/api/templates`)
      .then(res => res.json())
      .then(data => setTemplates(data))
      .catch(err => console.error("Erro ao carregar templates", err));
  }, []);

  useEffect(() => {
    if (selectedEmpresa) {
      fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
        .then(res => res.json())
        .then(data => setEmpreendimentos(data))
        .catch(err => console.error("Erro ao carregar empreendimentos", err));
    }
  }, [selectedEmpresa]);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) { alert("Selecione um arquivo."); return; }
    setLoading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch(`${API_BASE}/api/upload-planilha`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error("Falha no upload");
      const data = await res.json();
      setColumns(data.columns || []);
      setPreviewData(data.preview || []);
      setAllRows(data.all_rows || data.preview || []);
      setStep(2);

      // Auto-suggest mapping if possible
      callGeminiMatching(data.columns || [], (data.preview || [])[0]);
    } catch (err) {
      alert("Erro ao enviar arquivo.");
    } finally {
      setLoading(false);
    }
  };

  const callGeminiMatching = async (colsToMap = columns, amostraRow = null) => {
    if (!colsToMap.length) { alert('Envie uma planilha primeiro.'); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/schema-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          columns: colsToMap,
          target_table: targetTable,
          campos: (TARGET_SCHEMAS[targetTable] || []).map(f => f.value),
          amostras: amostraRow || previewData[0] || {},
        })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || 'Falha no mapeamento IA');
      const raw = data.mapping || {};
      const normalized = {};
      for (const [k, v] of Object.entries(raw)) {
        normalized[k] = (v === null || v === undefined || v === '' || v === 'null') ? 'null' : v;
      }
      setMapping(normalized);
      const mapeadas = Object.values(normalized).filter(v => v !== 'null').length;
      if (!mapeadas) alert('A IA não reconheceu nenhuma coluna para este destino — confira se o Destino (VENDAS/RECEBIMENTOS) está correto e mapeie manualmente.');
    } catch(err) {
      alert('Sugestão de mapeamento falhou: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewMatch = async () => {
    setMatchLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/smart-importer/preview-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rows: allRows,
          mapping,
          target_table: targetTable,
          empresa_id: selectedEmpresa ? parseInt(selectedEmpresa, 10) : null,
          empreendimento_id: selectedEmpreendimento ? parseInt(selectedEmpreendimento, 10) : null
        })
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Erro no preview'); }
      const data = await res.json();
      setMatchData(data.resultados || []);
      setParcelasAbertas(data.abertas || []);
      setStep(3);
    } catch(err) {
      alert('Erro ao gerar preview de match: ' + err.message);
    } finally {
      setMatchLoading(false);
    }
  };

  
  const handleSaveTemplate = async () => {
    const nome = prompt("Digite um nome para o template:");
    if (!nome) return;
    try {
      const res = await fetch(`${API_BASE}/api/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome,
          target_table: targetTable,
          mapping_json: JSON.stringify(mapping)
        })
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "Falha ao salvar");
      alert("Template salvo com sucesso!");
      fetch(`${API_BASE}/api/templates`)
        .then(r => r.json())
        .then(d => setTemplates(d));
    } catch(err) {
      alert("Erro ao salvar template.");
    }
  };

  const handleApplyTemplate = (templateHtmlJson) => {
    if (!templateHtmlJson) return;
    try {
       const mapObj = JSON.parse(templateHtmlJson);
       setMapping(mapObj);
    } catch(e) {}
  };

  const handleDownloadTxt = () => {
    if (!matchData || matchData.length === 0) return;
    const headers = ["Status", "Cliente_Planilha", "Dt_Vencimento", "Dt_Pagamento", "Valor_Planilha", "Valor_Vulcano", "Unidade_Contrato", "Observacao"];
    const rows = matchData.map(r => [
      r.status,
      r.cliente_planilha || '',
      r.dt_vencimento || '',
      r.dt_pagamento || '',
      r.valor_planilha || '',
      r.valor_vulcano || '',
      String(r.unidade || r.contrato || '').replace(/\r?\n|\r/g, " "),
      r.obs || ''
    ]);
    const txtContent = [headers.join(";"), ...rows.map(r => r.join(";"))].join("\n");
    const blob = new Blob([txtContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `smart_importer_match_${new Date().getTime()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getConfidenceColor = (val) => {
    if (val >= 0.9) return 'var(--v-ok)'; // Green
    if (val >= 0.7) return 'var(--v-warn)'; // Yellow
    return '#ff5c5c'; // Red
  };

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto w-full animate-in fade-in duration-500 pb-10">
      
      {/* Header & KPIs */}
      <div className="flex flex-col md:flex-row items-start justify-between gap-6 px-2">
        <div className="max-w-2xl">
          <div className="flex items-center gap-4 mb-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center border border-[rgb(var(--v-accent-rgb)_/_0.3)] bg-gradient-to-br from-[rgb(var(--v-accent-rgb)_/_0.2)] to-transparent shadow-[0_0_15px_rgba(255,122,26,0.15)]">
              <Sparkles className="text-[var(--v-accent)]" size={20} />
            </div>
            <h1 className="font-headline font-semibold text-2xl tracking-tight text-[var(--v-text)] flex items-center gap-2">
              Smart Importer <span className="text-[var(--v-accent)]">IA</span>
            </h1>
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold tracking-widest border border-[rgb(var(--v-accent-rgb)_/_0.3)] text-[var(--v-accent)] bg-[rgb(var(--v-accent-rgb)_/_0.1)]">
              BETA
            </span>
          </div>
          <p className="text-sm text-[var(--v-text-muted)] leading-relaxed">
            Importação e <span className="text-[var(--v-text-bold)]">de-para guiados por inteligência artificial</span> — solte planilhas, PDFs ou XMLs e a IA reconhece os headers, sugere o mapeamento contábil e enfileira para gravação.
          </p>
        </div>
        
        <div className="flex items-center gap-3 shrink-0">
          {[
            { label: 'ARQUIVOS HOJE', value: '38', sub: '+12 vs. ontem', color: 'text-[var(--v-accent)]' },
            { label: 'ACURÁCIA MÉDIA', value: '96.4%', sub: '↑ 2,1pp', color: 'text-[var(--v-ok)]' },
            { label: 'TEMPO POUPADO', value: '4h 12m', sub: 'vs. manual', color: 'text-[var(--v-text-bold)]' }
          ].map((kpi, i) => (
            <div key={i} className="min-w-[120px] p-3 bg-[var(--v-card)] border border-[var(--v-border)] rounded-lg">
              <p className="font-mono text-[9px] tracking-[0.2em] text-[var(--v-text-faint)] mb-1 uppercase">{kpi.label}</p>
              <p className={`font-headline text-xl font-semibold ${kpi.color}`}>{kpi.value}</p>
              <p className="font-mono text-[9px] text-[var(--v-text-faint)] mt-1">{kpi.sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Stepper (Visual Only) */}
      <div className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-xl p-4 md:px-6 md:py-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 relative">
          {[
            { num: 1, label: 'UPLOAD DE PLANILHA', sub: 'XLS · XLSX · CSV · PDF' },
            { num: 2, label: 'VALIDAÇÃO DE-PARA', sub: 'Headers reconhecidos pela IA' },
            { num: 3, label: 'PREVIEW DE MATCH', sub: 'Conferência antes de gravar' }
          ].map((s, idx) => (
            <div key={s.num} className="flex items-center gap-4 relative z-10">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-headline font-bold text-sm shrink-0 shadow-sm
                ${step >= s.num 
                  ? 'bg-gradient-to-br from-[var(--v-accent)] to-[#c93a12] border-none text-[var(--v-text-inv)] shadow-[inset_0_1px_0_rgba(255,220,180,0.4),0_0_15px_rgba(255,140,42,0.3)]' 
                  : 'bg-[rgb(var(--v-border-rgb)_/_0.1)] border border-[var(--v-border)] text-[var(--v-text-faint)]'}`}>
                {step > s.num ? <CheckCircle2 size={16} /> : s.num}
              </div>
              <div>
                <p className={`font-mono text-[10.5px] font-bold tracking-[0.18em] ${step >= s.num ? 'text-[var(--v-text-bold)]' : 'text-[var(--v-text-faint)]'}`}>{s.label}</p>
                <p className="text-[11px] text-[var(--v-text-muted)] mt-0.5">{s.sub}</p>
              </div>
              {idx < 2 && (
                <div className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 w-16 h-[2px] bg-[var(--v-border)] rounded"></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Upload & Copilot Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Upload Manual */}
        <div className="relative bg-[var(--v-card)] border border-dashed border-[var(--v-border)] hover:border-[rgb(var(--v-accent-rgb)_/_0.5)] transition-colors duration-300 rounded-xl p-6 flex flex-col min-h-[280px]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileSpreadsheet size={16} className="text-[var(--v-text-muted)]" />
              <span className="font-mono text-[10.5px] tracking-[0.22em] text-[var(--v-text-bold)] uppercase">Upload Manual</span>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold tracking-widest border border-[var(--v-border)] text-[var(--v-text-muted)] bg-[var(--v-tint)]">
              XLS · XLSX · CSV
            </span>
          </div>
          
          <form onSubmit={handleFileUpload} className="flex-1 flex flex-col items-center justify-center text-center">
            <div className="w-14 h-14 rounded-xl bg-[rgb(var(--v-accent-rgb)_/_0.05)] border border-[rgb(var(--v-accent-rgb)_/_0.2)] flex items-center justify-center mb-4 shadow-[inset_0_0_24px_rgba(255,140,42,0.08)]">
              <UploadCloud size={24} className="text-[var(--v-accent)]" />
            </div>
            <h3 className="font-headline font-semibold text-base text-[var(--v-text-bold)] mb-1">Arraste & solte um arquivo</h3>
            <p className="text-[12px] text-[var(--v-text-muted)] max-w-[320px] mb-6 leading-relaxed">
              A IA lê o cabeçalho automaticamente e reconhece o de-para de até <span className="text-[var(--v-accent)]">14 modelos aprendidos</span> da sua operação.
            </p>
            
            <div className="flex items-center gap-3 w-full max-w-sm">
              <input 
                type="file" 
                accept=".csv, .xls, .xlsx"
                onChange={(e) => setFile(e.target.files[0])}
                className="hidden"
                id="fileUpload"
              />
              <label htmlFor="fileUpload" className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-[var(--v-deep)] border border-[var(--v-border)] cursor-pointer hover:bg-[var(--v-hover)] transition-colors text-xs font-semibold text-[var(--v-text)] whitespace-nowrap">
                <Search size={14} /> Selecionar
              </label>
              
              <button type="submit" disabled={!file || loading} className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-gradient-to-br from-[var(--v-accent)] to-[#c93a12] text-[var(--v-text-inv)] font-semibold text-xs whitespace-nowrap shadow-[inset_0_1px_0_rgba(255,220,180,0.4),0_4px_12px_rgba(201,58,18,0.35)] disabled:opacity-50 hover:brightness-110 transition-all cursor-pointer border-none">
                {/* Rotulo em <span>: texto solto irmao de icone condicional vira no de referencia
                    do insertBefore e quebra o commit do React se algo (tradutor de pagina) tiver
                    embrulhado o texto. */}
                {loading ? <div className="animate-spin w-3 h-3 border-2 border-black border-t-transparent rounded-full" /> : <ChevronRight size={14} />}
                <span>{loading ? 'Analisando...' : 'Iniciar'}</span>
              </button>
            </div>
            {file && <p className="mt-4 text-[10px] text-[var(--v-text-bold)] truncate w-full max-w-xs">{file.name}</p>}
          </form>
        </div>

        {/* Copilot Card */}
        <div className="relative bg-[var(--v-card)] border border-[var(--v-border)] rounded-xl p-5 flex flex-col min-h-[280px] overflow-hidden">
          <div className="absolute -top-10 -right-10 w-36 h-36 bg-[radial-gradient(circle,rgba(255,140,42,0.18),transparent_70%)] pointer-events-none"></div>
          
          <div className="flex items-center justify-between mb-3 z-10">
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-[var(--v-ok)]" />
              <span className="font-mono text-[10.5px] tracking-[0.22em] text-[var(--v-text-bold)] uppercase">Copiloto de Importação</span>
            </div>
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold tracking-widest border border-[var(--v-ok)]/30 text-[var(--v-ok)] bg-[var(--v-ok)]/10 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--v-ok)] animate-pulse"></span> ONLINE
            </span>
          </div>
          
          <p className="text-[12.5px] text-[var(--v-text-muted)] leading-relaxed z-10 mb-5">
            Solte um arquivo e eu reconheço o layout. Modelos atuais cobrem <span className="text-[var(--v-text-bold)]">extratos bancários (BB, Itaú, Caixa)</span>, <span className="text-[var(--v-text-bold)]">NFe/NFSe</span>, <span className="text-[var(--v-text-bold)]">folha</span> e <span className="text-[var(--v-text-bold)]">SPED</span>.
          </p>
          
          {queueItems.length > 0 ? (
            <div className="flex-1 mt-2 z-10 overflow-y-auto pr-2 custom-scrollbar space-y-2">
              <h4 className="text-[10px] font-bold text-[var(--v-text-bold)] uppercase tracking-widest flex items-center gap-2 mb-2">
                <Database size={12} className="text-[var(--v-accent)]" /> Fila Automática ({queueItems.length})
              </h4>
              {queueItems.map(item => (
                <div key={item.id} className="bg-[var(--v-scrim)] border border-[var(--v-border)] p-2 rounded flex flex-col gap-1">
                  <div className="flex justify-between items-start">
                    <p className="text-[10px] font-bold text-[var(--v-text)] truncate max-w-[150px]" title={item.filename}>{item.filename}</p>
                    <div className="flex gap-1">
                      <button onClick={() => handleDeleteQueue(item.id)} className="text-[var(--v-text-faint)] hover:text-[var(--v-accent)]">
                        <X size={12} />
                      </button>
                      {item.status === 'AGUARDANDO_REVISAO' && (
                        <button onClick={() => handleApproveQueue(item.id, item.target_table)} disabled={queueLoading} className="text-[var(--v-info)] hover:underline text-[9px] font-bold uppercase tracking-widest">
                          Revisar
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="text-[8px] uppercase tracking-widest text-[var(--v-text-muted)] flex justify-between">
                    <span>Destino: <span className="text-[var(--v-accent)]">{item.target_table}</span></span>
                    <span className="text-[var(--v-warn-hi)]">{item.status}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 z-10 mb-auto">
              {/* Único card ACIONÁVEL: refaz a sugestão de de-para da IA.
                  Os demais descrevem etapas automáticas do fluxo (rodam sozinhos). */}
              <button onClick={() => callGeminiMatching()} disabled={loading || !columns.length}
                title={columns.length ? 'Refazer a sugestão de mapeamento da IA para o destino selecionado' : 'Envie uma planilha primeiro'}
                className="flex items-center gap-2 p-2 bg-black/30 border border-[var(--v-accent)]/40 rounded-md hover:bg-[var(--v-accent)]/10 transition-colors disabled:opacity-40 text-left">
                <div className="text-[var(--v-accent)]"><Sparkles size={14}/></div>
                <span className="flex-1 text-[11px] text-[var(--v-text-bold)] truncate">Sugerir mapeamento</span>
                <span className="font-mono text-[9px] text-[var(--v-accent)]">{loading ? '...' : 'IA'}</span>
              </button>
              {[
                { icon: <CheckCircle2 size={14}/>, label: 'Validar com regras', value: 'auto', tip: 'Validação automática no Preview de Match' },
                { icon: <AlertCircle size={14}/>, label: 'Marcar divergências', value: 'auto', tip: 'Divergências aparecem no Preview de Match' },
                { icon: <Zap size={14}/>, label: 'Aprender com correções', value: 'on', tip: 'Templates salvos reaproveitam suas correções' }
              ].map((f, i) => (
                <div key={i} title={f.tip} className="flex items-center gap-2 p-2 bg-[var(--v-scrim)] border border-[var(--v-border)] rounded-md cursor-default">
                  <div className="text-[var(--v-text-muted)]">{f.icon}</div>
                  <span className="flex-1 text-[11px] text-[var(--v-text-bold)] truncate">{f.label}</span>
                  <span className="font-mono text-[9px] text-[var(--v-text-faint)]">{f.value}</span>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 p-3 bg-[rgb(var(--v-accent-rgb)_/_0.05)] border border-dashed border-[rgb(var(--v-accent-rgb)_/_0.3)] rounded-lg flex gap-3 z-10">
            <Settings size={14} className="text-[var(--v-text-muted)] shrink-0 mt-0.5" />
            <p className="text-[11px] text-[var(--v-text-muted)] leading-snug">
              Sempre que uma coluna fica abaixo de <span className="text-[var(--v-warn)]">0.85 de confiança</span>, eu peço sua confirmação e aprendo o padrão para os próximos arquivos.
            </p>
          </div>
        </div>
      </div>

      {/* DE-PARA Table Section */}
      {step >= 2 && columns.length > 0 && step < 3 && (
        <div className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-xl overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
          <div className="p-4 border-b border-[var(--v-border)] flex items-center justify-between bg-[var(--v-zebra)]">
            <div className="flex items-center gap-3">
              <Database size={16} className="text-[var(--v-text-muted)]" />
              <span className="font-mono text-[10.5px] tracking-[0.22em] text-[var(--v-text-bold)] uppercase">DE-PARA SUGERIDO PELA IA</span>
              <div className="w-[1px] h-3 bg-[var(--v-border)]"></div>
              <span className="font-mono text-[9.5px] text-[var(--v-text-faint)]">{columns.length} colunas identificadas</span>
            </div>
            <div className="flex items-center gap-3">
              <select 
                onChange={(e) => handleApplyTemplate(e.target.value)}
                className="bg-[var(--v-deep)] border border-[var(--v-border)] text-[var(--v-text-muted)] py-1.5 px-3 rounded text-[11px] outline-none max-w-[150px]"
              >
                <option value="">Aplicar Template...</option>
                {templates.filter(t => t.target_table === targetTable).map(t => (
                  <option key={t.id} value={t.mapping_json}>{t.nome}</option>
                ))}
              </select>
              <select 
                value={selectedEmpreendimento} 
                onChange={(e) => setSelectedEmpreendimento(e.target.value)}
                className="bg-[var(--v-deep)] border border-[var(--v-border)] text-[var(--v-text-muted)] py-1.5 px-3 rounded text-[11px] outline-none max-w-[150px]"
              >
                <option value="">Todos Empreendimentos</option>
                {empreendimentos.map(e => <option key={e.id} value={e.id}>{e.id} - {e.nome}</option>)}
              </select>
              <select 
                value={targetTable} 
                onChange={(e) => setTargetTable(e.target.value)}
                className="bg-[var(--v-deep)] border border-[var(--v-border)] text-[var(--v-text-bold)] py-1.5 px-3 rounded text-[11px] outline-none"
              >
                <option value="VENDAS">Destino: VENDAS</option>
                <option value="RECEBIMENTOS">Destino: RECEBIMENTOS</option>
              </select>
              <button onClick={() => callGeminiMatching(columns)} className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--v-deep)] border border-[var(--v-border)] rounded text-[11px] font-medium hover:bg-[var(--v-hover)] transition-colors">
                <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Re-analisar
              </button>
              <button onClick={handlePreviewMatch} disabled={matchLoading} className="flex items-center gap-1.5 px-4 py-1.5 bg-[rgb(var(--v-accent-rgb)_/_0.1)] text-[var(--v-accent)] border border-[rgb(var(--v-accent-rgb)_/_0.3)] rounded text-[11px] font-bold hover:bg-[rgb(var(--v-accent-rgb)_/_0.2)] transition-colors disabled:opacity-50">
                {matchLoading ? 'Aguarde...' : 'Gerar Preview de Match'} <ArrowUpRight size={12} />
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="bg-[var(--v-scrim)] font-mono text-[9.5px] tracking-[0.2em] text-[var(--v-text-faint)] border-b border-[var(--v-border)]">
                  <th className="p-3 w-12 text-center">#</th>
                  <th className="p-3">COLUNA NA PLANILHA</th>
                  <th className="p-3 w-8 text-center"></th>
                  <th className="p-3">CAMPO VULCANO</th>
                  <th className="p-3 text-[var(--v-text-muted)]">AMOSTRA</th>
                  <th className="p-3 text-right">AÇÃO / OPÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {columns.map((col, idx) => {
                  const val = mapping[col] && mapping[col] !== 'null';
                  return (
                    <tr key={idx} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors items-center group">
                      <td className="p-3 text-center font-mono text-[10.5px] text-[var(--v-text-faint)]">{(idx + 1).toString().padStart(2, '0')}</td>
                      <td className="p-3 font-mono text-[11.5px] font-semibold text-[var(--v-text)]">{col}</td>
                      <td className="p-3 text-center text-[var(--v-accent)]"><ArrowUpRight size={14} className="opacity-50 mx-auto" /></td>
                      <td className="p-3">
                        <select 
                          value={mapping[col] ?? 'null'} 
                          onChange={(e) => {
                            setMapping(prev => ({ ...prev, [col]: e.target.value }));
                          }}
                          className={`w-full max-w-[220px] bg-[var(--v-deep)] border ${val ? 'border-[var(--v-ok)]/30 text-[var(--v-ok)]' : 'border-[var(--v-border)] text-[var(--v-text-muted)]'} py-1.5 px-2 rounded outline-none text-[11px] font-mono font-medium appearance-none cursor-pointer hover:border-[rgb(var(--v-accent-rgb)_/_0.5)] transition-colors`}
                        >
                          <option value="null">-- Ignorar --</option>
                          {(TARGET_SCHEMAS[targetTable] || []).map(field => (
                            <option key={field.value} value={field.value}>{field.label}</option>
                          ))}
                        </select>
                      </td>
                      <td className="p-3 text-[11px] text-[var(--v-text-muted)] truncate max-w-[180px]" title={previewData[0]?.[col]}>
                        {previewData[0]?.[col] || '-'}
                      </td>
                      <td className="p-3 text-right">
                        {val ? (
                          <span className="font-mono text-[9.5px] tracking-widest text-[var(--v-ok)] px-2 py-1 bg-[var(--v-ok)]/10 rounded border border-[var(--v-ok)]/20">MAPPED</span>
                        ) : (
                          <span className="font-mono text-[9.5px] tracking-widest text-[var(--v-text-faint)] px-2 py-1 bg-[var(--v-scrim)] rounded border border-[var(--v-border)]">IGNORADO</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MATCH PREVIEW Section */}
      {step === 3 && (
        <div className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-xl overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
          <div className="p-4 border-b border-[var(--v-border)] flex items-center justify-between bg-[var(--v-zebra)]">
            <div className="flex items-center gap-3">
              <Database size={16} className="text-[var(--v-text-muted)]" />
              <span className="font-mono text-[10.5px] tracking-[0.22em] text-[var(--v-text-bold)] uppercase">PREVIEW DE MATCH E INTEGRAÇÃO</span>
              <div className="w-[1px] h-3 bg-[var(--v-border)]"></div>
              <span className="font-mono text-[9.5px] text-[var(--v-text-faint)]">{matchData.length} registros analisados</span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={handleSaveTemplate} className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[var(--v-border)] rounded text-[11px] text-[var(--v-text-muted)] hover:text-[var(--v-text)] transition-colors">
                <Save size={12} /> Salvar Template
              </button>
              <button onClick={handleDownloadTxt} className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[var(--v-border)] rounded text-[11px] text-[var(--v-info)] hover:bg-[var(--v-info)]/10 transition-colors">
                <Download size={12} /> Baixar TXT
              </button>
              <button onClick={() => setStep(2)} className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--v-deep)] border border-[var(--v-border)] rounded text-[11px] font-medium hover:bg-[var(--v-hover)] transition-colors">
                Voltar
              </button>
              <button onClick={() => alert("Gravação será implementada na API")} className="flex items-center gap-1.5 px-4 py-1.5 bg-[var(--v-ok)]/10 text-[var(--v-ok)] border border-[var(--v-ok)]/30 rounded text-[11px] font-bold hover:bg-[var(--v-ok)]/20 transition-colors shadow-sm">
                <Save size={14} /> Gravar no ERP
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar">
            <table className="w-full text-left text-xs border-collapse min-w-[1000px]">
              <thead className="bg-[var(--v-scrim)] sticky top-0 z-10 backdrop-blur-md">
                <tr className="font-mono text-[9.5px] tracking-[0.1em] text-[var(--v-text-faint)] border-b border-[var(--v-border)]">
                  <th className="p-3">STATUS</th>
                  <th className="p-3">CLIENTE (Planilha)</th>
                  <th className="p-3">DATA PGTO</th>
                  <th className="p-3 text-right">VALOR PLANILHA</th>
                  <th className="p-3 text-right">VALOR ERP</th>
                  <th className="p-3 text-right">DIFERENÇA</th>
                  <th className="p-3 text-center">AÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {matchData.map((r, idx) => {
                  const meta = STATUS_META[r.status] || { label: r.status, color: 'var(--v-text-muted)' };
                  const fmt = v => v != null ? `R$ ${Number(v).toLocaleString('pt-BR', {minimumFractionDigits:2})}` : '-';
                  const diff = Math.abs((r.valor_planilha || 0) - (r.valor_vulcano || 0));
                  
                  return (
                    <tr key={idx} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                      <td className="p-3">
                        <span className="text-[9px] font-bold uppercase tracking-widest px-2 py-1 rounded border" style={{ color: meta.color, backgroundColor: `${meta.color}15`, borderColor: `${meta.color}30` }}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="p-3 max-w-[200px]">
                        <p className="font-semibold text-[var(--v-text)] truncate" title={r.cliente_planilha}>{r.cliente_planilha || '-'}</p>
                        {r.status !== 'SEM_MATCH' && (
                          <div className="mt-1 flex flex-col gap-0.5 border-t border-[rgb(var(--v-border-rgb)_/_0.5)] pt-1">
                            <span className="text-[9.5px] font-mono tracking-widest text-[var(--v-ok)] uppercase font-bold">
                              PARCELA: {r.numero_parcela || '-'} | VENC: {r.dt_venc_vulcano || '-'}
                            </span>
                            <span className="text-[10px] text-[var(--v-text-muted)] truncate" title={r.cliente_vulcano}>
                              {r.unidade_vulcano ? `${r.unidade_vulcano} - ` : ''}{r.cliente_vulcano || ''}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="p-3 font-mono text-[11px] text-[var(--v-text-muted)]">{r.dt_pagamento || '-'}</td>
                      <td className="p-3 text-right font-black text-[var(--v-text)]">{fmt(r.valor_planilha)}</td>
                      <td className="p-3 text-right font-black text-[var(--v-text-muted)]">{fmt(r.valor_vulcano)}</td>
                      <td className="p-3 text-right font-bold text-[11px]">
                        {diff > 0.01 ? <span className="text-[var(--v-warn)]">{fmt(diff)}</span> : <span className="text-[var(--v-text-faint)]">Exato</span>}
                      </td>
                      <td className="p-3 text-center">
                        {r.status === 'SEM_MATCH' ? (
                          <button onClick={() => setManualMatchModal({ open: true, rowData: r, rowIndex: idx })} className="px-2 py-1 bg-[var(--v-deep)] border border-[var(--v-border)] hover:border-[var(--v-src-vu1)] text-[var(--v-text-muted)] hover:text-[var(--v-src-vu1)] rounded text-[9px] font-bold uppercase tracking-widest transition-colors inline-flex items-center gap-1">
                            Vincular
                          </button>
                        ) : (
                          <span className="text-[var(--v-text-faint)]">-</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {manualMatchModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--v-overlay)] backdrop-blur-sm p-4">
          <div className="bg-[var(--v-bg)] border border-[var(--v-border)] rounded-xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-6 border-b border-[var(--v-border)] flex justify-between items-center bg-[var(--v-deep)]">
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest text-[var(--v-text-bold)] flex items-center gap-2">
                  🔗 Pareamento Manual
                </h3>
                <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] mt-1">Selecione a parcela correspondente do sistema para vincular ao recebimento da planilha.</p>
              </div>
              <button onClick={() => setManualMatchModal({open: false, rowData: null, rowIndex: null})} className="text-[var(--v-text-muted)] hover:text-[#ff4d4d] transition-colors">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 border-b border-[var(--v-border)] bg-[var(--v-deep)]">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-src-vu1)] mb-3">Dados da Planilha (Pagamento Efetuado)</h4>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-[var(--v-card)] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Cliente</p>
                  <p className="text-xs font-bold text-[var(--v-text)] truncate">{manualMatchModal.rowData?.cliente_planilha || '-'}</p>
                </div>
                <div className="bg-[var(--v-card)] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Vencimento</p>
                  <p className="text-xs font-mono text-[var(--v-text-muted)]">{manualMatchModal.rowData?.dt_vencimento || '-'}</p>
                </div>
                <div className="bg-[var(--v-card)] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Pagamento</p>
                  <p className="text-xs font-mono text-[var(--v-text-muted)]">{manualMatchModal.rowData?.dt_pagamento || '-'}</p>
                </div>
                <div className="bg-[var(--v-card)] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Valor Pago</p>
                  <p className="text-sm font-black text-[var(--v-accent)]">R$ {Number(manualMatchModal.rowData?.valor_planilha || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</p>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-6 bg-[var(--v-card)]">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-muted)] mb-3">Selecione a Parcela do Questor ({parcelasAbertas.length} em aberto)</h4>
              
              {parcelasAbertas.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-[var(--v-border)] rounded">
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)]">Nenhuma parcela em aberto encontrada para os filtros atuais.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {parcelasAbertas.map(p => {
                    const rowVal = manualMatchModal.rowData?.valor_planilha || 0;
                    const diff = Math.round((rowVal - p.valor_parcela) * 100) / 100;
                    const isAcrescimo = diff > 0;
                    const isDesconto = diff < 0;
                    
                    return (
                      <div key={p.id} className="flex items-center justify-between p-3 border border-[var(--v-border)] bg-[var(--v-deep)] rounded hover:border-[var(--v-src-vu1)] transition-colors group">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="bg-[var(--v-card)] px-3 py-1 rounded text-xs font-mono text-[var(--v-text-muted)] w-16 text-center border border-[var(--v-border)]">
                            Nº {p.numero_parcela}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-[var(--v-text)] truncate">{p.cliente_nome}</p>
                            <p className="text-[10px] text-[var(--v-text-faint)] truncate">{p.descricao_unidade} | Venc: {p.data_vencimento}</p>
                          </div>
                          <div className="text-right px-4">
                            <p className="text-sm font-black text-[var(--v-accent)]">R$ {p.valor_parcela.toLocaleString('pt-BR', {minimumFractionDigits:2})}</p>
                            {diff !== 0 && (
                              <p className={`text-[9px] font-bold uppercase tracking-widest ${isAcrescimo ? 'text-[var(--v-warn-hi)]' : 'text-[var(--v-ok)]'}`}>
                                {isAcrescimo ? '+ Acréscimo' : '- Desconto'}: R$ {Math.abs(diff).toLocaleString('pt-BR', {minimumFractionDigits:2})}
                              </p>
                            )}
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            const newData = [...matchData];
                            const idx = manualMatchModal.rowIndex;
                            newData[idx] = {
                              ...newData[idx],
                              status: 'MATCH_MANUAL',
                              id_parcela: p.id,
                              numero_parcela: p.numero_parcela,
                              cliente_vulcano: p.cliente_nome,
                              dt_vencimento: p.data_vencimento,
                              valor_vulcano: p.valor_parcela,
                              unidade: p.descricao_unidade,
                              acrescimos: isAcrescimo ? Math.abs(diff) : 0,
                              descontos: isDesconto ? Math.abs(diff) : 0
                            };
                            setMatchData(newData);
                            setManualMatchModal({open: false, rowData: null, rowIndex: null});
                          }}
                          className="px-4 py-2 bg-[var(--v-deep)] border border-[var(--v-src-vu1)]/30 text-[var(--v-src-vu1)] rounded text-[10px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 hover:bg-[var(--v-src-vu1)] hover:text-[var(--v-text-bold)] transition-all ml-4"
                        >
                          Vincular
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* IMPORTAÇÕES RECENTES */}
      <div className="pt-6">
        <div className="flex items-center gap-3 mb-4">
          <Database size={16} className="text-[var(--v-text-faint)]" />
          <span className="font-mono text-[10.5px] tracking-[0.22em] text-[var(--v-text-bold)] uppercase">Importações Recentes</span>
          <div className="flex-1 h-px bg-[rgb(var(--v-border-rgb)_/_0.5)]"></div>
          <span className="font-mono text-[9.5px] text-[var(--v-text-faint)]">ÚLTIMAS 24H · 38 ARQUIVOS</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { name: 'recebimentos_quinzena.csv', time: 'há 2 min', lines: 218, acc: '98.0%', saved: '14m', icon: <FileSpreadsheet size={16}/>, color: 'var(--v-info)' },
            { name: 'extrato_caixa_06.pdf', time: 'há 8 min', lines: 412, acc: '95.0%', saved: '22m', icon: <UploadCloud size={16}/>, color: 'var(--v-accent)' },
            { name: 'NF_emit_05.xlsx', time: 'há 47 min', lines: 174, acc: '97.0%', saved: '11m', icon: <FileSpreadsheet size={16}/>, color: 'var(--v-ok)' }
          ].map((item, i) => (
            <div key={i} className="bg-[var(--v-scrim)] border border-[var(--v-border)] hover:border-[rgb(var(--v-border-rgb)_/_0.8)] rounded-xl p-4 transition-colors cursor-pointer group">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-[var(--v-text-bold)]">
                  <div style={{color: item.color}} className="opacity-80 group-hover:opacity-100 transition-opacity">{item.icon}</div>
                  <span className="font-mono text-[11px] truncate max-w-[150px]" title={item.name}>{item.name}</span>
                </div>
                <span className="font-mono text-[9.5px] text-[var(--v-text-faint)]">{item.time}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <div>
                  <div className="font-headline font-semibold text-lg text-[var(--v-text)]">{item.lines}</div>
                  <div className="font-mono text-[9px] tracking-widest text-[var(--v-text-faint)] mt-0.5">LINHAS</div>
                </div>
                <div>
                  <div className="font-headline font-semibold text-lg text-[var(--v-ok)]">{item.acc}</div>
                  <div className="font-mono text-[9px] tracking-widest text-[var(--v-text-faint)] mt-0.5">ACURÁCIA</div>
                </div>
                <div>
                  <div className="font-headline font-semibold text-lg text-[var(--v-accent)]">{item.saved}</div>
                  <div className="font-mono text-[9px] tracking-widest text-[var(--v-text-faint)] mt-0.5">POUPADO</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
