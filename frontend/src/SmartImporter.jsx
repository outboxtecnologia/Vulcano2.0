import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, ChevronRight, FileSpreadsheet, Loader2, Database, AlertCircle, Sparkles, Save, ArrowUpRight } from 'lucide-react';

const API_BASE = import.meta?.env?.VITE_API_BASE || 'http://127.0.0.1:8000';

// Campos destino por entidade — devem ser idênticos ao _SMART_IMPORTER_SCHEMAS do backend
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
    { value: 'DATA_PAGAMENTO',      label: 'Data de Pagamento (Recebimento)' },
    { value: 'DATA_VENCIMENTO',     label: 'Data de Vencimento' },
    { value: 'VALOR_PAGO',          label: 'Valor Pago' },
    { value: 'VALOR_PARCELA',       label: 'Valor da Parcela (Nominal)' },
    { value: 'ACRESCIMOS',          label: 'Acréscimos / Juros / Mora' },
    { value: 'DESCONTOS',           label: 'Descontos / Abatimentos' },
    { value: 'NUMERO_PARCELA',      label: 'Número da Parcela' },
    { value: 'DESCRICAO',           label: 'Descrição / Histórico' },
    { value: 'CLIENTE_NOME',        label: 'Nome do Cliente' },
    { value: 'CLIENTE_CPF_CNPJ',    label: 'CPF / CNPJ' },
    { value: 'EMPREENDIMENTO',      label: 'Empreendimento' },
    { value: 'UNIDADE',             label: 'Unidade' },
    { value: 'CONTRATO',            label: 'Contrato / RF' },
    { value: 'FORMA_PAGAMENTO',     label: 'Forma de Pagamento' },
    { value: 'BANCO',               label: 'Banco' },
    { value: 'AGENCIA',             label: 'Agência' },
    { value: 'CONTA',               label: 'Conta Bancária' },
    { value: 'NOSSO_NUMERO',        label: 'Nosso Número' },
    { value: 'OBSERVACOES',         label: 'Observações' },
  ],
  EMPREENDIMENTOS: [
    { value: 'NOME',                    label: 'Nome' },
    { value: 'CODIGO_CC',               label: 'Código do Centro de Custo' },
    { value: 'DATA_INICIO',             label: 'Data de Início' },
    { value: 'DATA_PREVISTA_ENTREGA',   label: 'Data Prevista de Entrega' },
    { value: 'CONTA_ESTOQUE',           label: 'Conta de Estoque' },
    { value: 'CONTA_CUSTO',             label: 'Conta de Custo' },
    { value: 'CUSTO_ORCADO',            label: 'Custo Orçado' },
    { value: 'AREA_TOTAL',              label: 'Área Total (m²)' },
    { value: 'CNPJ',                    label: 'CNPJ' },
  ],
  CLIENTES: [
    { value: 'NOME',        label: 'Nome' },
    { value: 'CPF_CNPJ',   label: 'CPF / CNPJ' },
    { value: 'EMAIL',       label: 'E-mail' },
    { value: 'TELEFONE',    label: 'Telefone' },
    { value: 'ENDERECO',    label: 'Endereço' },
    { value: 'CIDADE',      label: 'Cidade' },
    { value: 'ESTADO',      label: 'Estado (UF)' },
    { value: 'CEP',         label: 'CEP' },
    { value: 'OBSERVACOES', label: 'Observações' },
  ],
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
  const [commitLoading, setCommitLoading] = useState(false);

  React.useEffect(() => {
    fetch(`${API_BASE}/api/templates`)
      .then(res => res.json())
      .then(data => setTemplates(data))
      .catch(err => console.error("Erro ao carregar templates", err));
  }, []);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      alert("Selecione um arquivo.");
      return;
    }
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
    } catch (err) {
      alert("Erro ao validar planilha. Verifique se o backend está rodando e o arquivo é válido.");
    } finally {
      setLoading(false);
    }
  };

  const callGeminiMatching = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/schema-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ columns, target_table: targetTable })
      });
      if (!res.ok) throw new Error("Falha no mapeamento IA");
      const data = await res.json();
      // Normaliza: JSON null → string 'null' para compatibilidade com o <select>
      const raw = data.mapping || {};
      const normalized = {};
      for (const [k, v] of Object.entries(raw)) {
        normalized[k] = (v === null || v === undefined || v === '' || v === 'null') ? 'null' : v;
      }
      setMapping(normalized);
    } catch(err) {
      alert("Erro ao chamar o Gemini (schema). Verifique GEMINI_API_KEY e o backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTemplate = async () => {
    const nome = prompt("Digite um nome para o template:");
    if (!nome) return;
    try {
      await fetch(`${API_BASE}/api/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome,
          target_table: targetTable,
          mapping_json: JSON.stringify(mapping)
        })
      });
      alert("Template salvo com sucesso!");
      fetch(`${API_BASE}/api/templates`)
        .then(res => res.json())
        .then(data => setTemplates(data));
    } catch(err) {
      alert("Erro ao salvar template");
    }
  };

  const handleApplyTemplate = (templateHtmlJson) => {
    if (!templateHtmlJson) return;
    try {
       const mapObj = JSON.parse(templateHtmlJson);
       setMapping(mapObj);
    } catch(e) {}
  };

  const handleMappingChange = (sourceCol, newTarget) => {
    setMapping(prev => ({ ...prev, [sourceCol]: newTarget }));
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
          empresa_id: selectedEmpresa ? parseInt(selectedEmpresa, 10) : null
        })
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Erro no preview'); }
      const data = await res.json();
      setMatchData(data.resultados || []);
      setStep(3);
    } catch(err) {
      alert('Erro ao gerar preview de match: ' + err.message);
    } finally {
      setMatchLoading(false);
    }
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

  const STATUS_META = {
    JA_QUITADO:    { label: 'Já Quitado',    cls: 'bg-[#34c759]/10 text-[#34c759] border-[#34c759]/30' },
    MATCH_PERFEITO:{ label: 'Match',          cls: 'bg-[#007aff]/10 text-[#007aff] border-[#007aff]/30' },
    SEM_MATCH:     { label: 'Sem Match',      cls: 'bg-[#ff4d00]/10 text-[#ff4d00] border-[#ff4d00]/30' },
    DIVERGENCIA:   { label: 'Divergência',    cls: 'bg-[#ffcc00]/10 text-[#ffcc00] border-[#ffcc00]/30' },
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto w-full">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter text-[var(--v-text-bold)] uppercase flex items-center gap-3">
            <Sparkles className="text-[var(--v-accent-5)]" size={36} /> Smart Importer IA
          </h2>
          <p className="text-sm text-[var(--v-text-muted)] mt-2 uppercase tracking-widest font-bold">Importação e de-para guiados por inteligência artificial</p>
        </div>
      </div>

      {/* Stepper Header */}
      <div className="flex items-center justify-between bg-[var(--v-card)] border border-[var(--v-border)] p-6 rounded-[var(--v-radius)]">
        {[
          { num: 1, label: 'Upload de Planilha' },
          { num: 2, label: 'Validação DE-PARA' },
          { num: 3, label: 'Preview de Match' }
        ].map((s, idx) => (
          <React.Fragment key={s.num}>
            <div className={`flex flex-col items-center gap-2 ${step >= s.num ? 'opacity-100' : 'opacity-40'}`}>
              <div className={`w-10 h-10 rounded-[var(--v-radius)] flex items-center justify-center font-bold text-sm border-2 ${step > s.num ? 'bg-[#a259ff] border-[#a259ff] text-[var(--v-text-bold)]' : step === s.num ? 'border-[#a259ff] text-[var(--v-accent-5)]' : 'border-[var(--v-border)] text-[var(--v-text-muted)]'}`}>
                {step > s.num ? <CheckCircle2 size={18} /> : s.num}
              </div>
              <span className={`text-[10px] uppercase font-bold tracking-widest ${step >= s.num ? 'text-[var(--v-text)]' : 'text-[var(--v-text-faint)]'}`}>{s.label}</span>
            </div>
            {idx < 2 && <div className={`flex-1 h-px ${step > s.num ? 'bg-[#a259ff]' : 'bg-[#333]'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Upload */}
      {step === 1 && (
        <div className="bg-[var(--v-card)] border border-[var(--v-border)] p-8 rounded-[var(--v-radius)] text-center">
          <FileSpreadsheet size={64} className="mx-auto text-[var(--v-text-faint)] mb-6" />
          <h3 className="text-xl font-bold text-[var(--v-text-bold)] mb-2 uppercase tracking-widest">Selecione seu arquivo</h3>
          <p className="text-[var(--v-text-muted)] text-sm mb-8">Suporte para .XLS, .XLSX e .CSV. O sistema irá ler o cabeçalho automaticamente.</p>
          
          <form onSubmit={handleFileUpload} className="max-w-md mx-auto flex flex-col gap-4">
            <input 
              type="file" 
              accept=".csv, .xls, .xlsx"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full text-sm text-[var(--v-text-muted)] file:mr-4 file:py-3 file:px-4 file:rounded-[var(--v-radius)] file:border-0 file:text-[10px] file:font-bold file:uppercase file:tracking-widest file:bg-[var(--v-hover)] file:text-[var(--v-accent-4)] hover:file:bg-[var(--v-hover)] file:cursor-pointer border border-[var(--v-border)] bg-[#0b0b0b] p-2"
            />
            <button 
              type="submit" 
              disabled={loading || !file} 
              className="w-full bg-[#007aff] text-[var(--v-text-bold)] py-4 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] hover:bg-[#005bb5] transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />}
              {loading ? 'Analisando Estrutura...' : 'Iniciar Importação'}
            </button>
          </form>
        </div>
      )}

      {/* Step 2: Validação Humana / Mapping */}
      {step === 2 && (
        <div className="flex flex-col gap-6">
          <div className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] p-8">
            <div className="flex items-center gap-4 mb-8 pb-6 border-b border-[var(--v-border)]">
              <Sparkles className="text-[var(--v-accent-5)]" size={32} />
              <div>
                <h3 className="text-xl font-bold text-[var(--v-text-bold)] uppercase tracking-widest">Configuração do Destino</h3>
                <p className="text-[var(--v-text-muted)] text-sm">Defina o destino e mapeie as colunas. Se precisar, peça para a IA sugerir o mapeamento.</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-8 mb-8">
              <div>
                <label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold block mb-2">Entidade Destino (Vulcano/Questor)</label>
                <select 
                  value={targetTable} 
                  onChange={(e) => setTargetTable(e.target.value)}
                  className="w-full bg-[#0b0b0b] border border-[var(--v-border)] text-[var(--v-text-bold)] p-4 rounded-[var(--v-radius)] outline-none focus:border-[#a259ff] text-sm font-bold tracking-widest uppercase transition-colors"
                >
                  <option value="VENDAS">Vendas (Contratos)</option>
                  <option value="RECEBIMENTOS">Recebimentos (Baixas)</option>
                  <option value="EMPREENDIMENTOS">Empreendimentos</option>
                  <option value="CLIENTES">Clientes / Fornecedores</option>
                </select>
              </div>
              <div className="bg-[#0b0b0b] p-4 border border-[var(--v-border)] rounded-[var(--v-radius)] flex flex-col justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-2">Aplicar Template Salvo</p>
                  <select 
                    onChange={(e) => handleApplyTemplate(e.target.value)}
                    className="w-full bg-[var(--v-card)] border border-[var(--v-border)] text-[var(--v-text-bold)] p-3 rounded-[var(--v-radius)] outline-none text-xs font-bold tracking-widest uppercase transition-colors"
                  >
                    <option value="">-- Selecione (Opcional) --</option>
                    {templates.filter(t => t.target_table === targetTable).map(t => (
                      <option key={t.id} value={t.mapping_json}>{t.nome}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-6 mt-4 pt-4 border-t border-[var(--v-border)] items-center justify-between">
                  <div>
                    <p className="text-2xl font-black text-[var(--v-accent-5)]">{columns.length}</p>
                    <p className="text-xs text-[var(--v-text-muted)]">Colunas Identificadas</p>
                  </div>
                  <button 
                    onClick={callGeminiMatching} 
                    disabled={loading}
                    className="bg-[var(--v-card)] border border-[#a259ff] text-[#a259ff] px-4 py-2 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] hover:bg-[#a259ff]/10 transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                    {loading ? 'Rodando Inferência...' : 'Sugerir Mapeamento (IA)'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--v-deep)]">
                  <th className="p-4 border-b border-[var(--v-border)] text-[10px] font-bold tracking-widest uppercase text-[var(--v-text-faint)] w-1/2">Coluna Origem (Planilha)</th>
                  <th className="p-4 border-b border-[var(--v-border)] text-[10px] font-bold tracking-widest uppercase text-[var(--v-accent-5)] w-1/2">Campo Destino ({targetTable})</th>
                </tr>
              </thead>
              <tbody>
                {columns.map((col, idx) => (
                  <tr key={idx} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                    <td className="p-4 text-sm font-bold text-[var(--v-text)] flex flex-col gap-1">
                      {col}
                      <span className="text-[10px] text-[var(--v-text-faint)] font-normal truncate max-w-sm" title={previewData.length > 0 ? previewData[0][col] : ''}>
                        {previewData.length > 0 ? `Ex: ${previewData[0][col]}` : ''}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <ArrowUpRight size={14} className="text-[var(--v-text-faint)]" />
                        <select 
                          value={mapping[col] ?? 'null'} 
                          onChange={(e) => handleMappingChange(col, e.target.value)}
                          className={`w-full bg-[#0b0b0b] border ${mapping[col] && mapping[col] !== 'null' ? 'border-[#a259ff] text-[var(--v-text)]' : 'border-[var(--v-border)] text-[var(--v-text-muted)]'} p-2 rounded-[var(--v-radius)] outline-none text-xs font-bold uppercase tracking-wider transition-colors`}
                        >
                          <option value="null">-- Não Importar --</option>
                          {(TARGET_SCHEMAS[targetTable] || []).map(field => (
                            <option key={field.value} value={field.value}>{field.label}</option>
                          ))}
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center bg-[var(--v-card)] p-4 border border-[var(--v-border)] rounded-[var(--v-radius)]">
            <button onClick={handleSaveTemplate} className="flex items-center gap-2 text-[var(--v-text-muted)] hover:text-[var(--v-accent-4)] transition-colors text-[10px] font-bold uppercase tracking-widest">
              <Save size={14} /> Salvar como Template
            </button>
            <div className="flex gap-4">
              <button onClick={() => setStep(1)} className="px-6 py-3 rounded-[var(--v-radius)] text-[var(--v-text-muted)] border border-[var(--v-border)] hover:text-[var(--v-text-bold)] hover:bg-[var(--v-hover)] text-[10px] uppercase font-bold tracking-widest transition-colors">Voltar</button>
              <button
                onClick={handlePreviewMatch}
                disabled={matchLoading}
                className="bg-[#a259ff] text-[var(--v-text-bold)] px-8 py-3 rounded-[var(--v-radius)] font-bold uppercase tracking-widest text-[10px] hover:bg-[#8e45e6] transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {matchLoading ? <Loader2 size={16} className="animate-spin" /> : <ArrowUpRight size={16} />}
                {matchLoading ? 'Analisando...' : 'Avançar para Match →'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Preview de Match */}
      {step === 3 && (
        <div className="flex flex-col gap-6">
          {/* KPIs */}
          {(() => {
            const total   = matchData.length;
            const quitados = matchData.filter(r => r.status === 'JA_QUITADO').length;
            const matches  = matchData.filter(r => r.status === 'MATCH_PERFEITO').length;
            const semMatch = matchData.filter(r => r.status === 'SEM_MATCH').length;
            return (
              <div className="grid grid-cols-4 gap-4">
                {[{l:'Total Linhas', v:total, c:'border-[var(--v-border)]'},
                  {l:'Já Quitados', v:quitados, c:'border-[#34c759]'},
                  {l:'Match Encontrado', v:matches, c:'border-[#007aff]'},
                  {l:'Sem Match', v:semMatch, c:'border-[#ff4d00]'}].map(k => (
                  <div key={k.l} className={`bg-[var(--v-card)] border-l-4 ${k.c} p-5 rounded-[var(--v-radius)]`}>
                    <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">{k.l}</p>
                    <p className="text-3xl font-black text-[var(--v-text-bold)]">{k.v}</p>
                  </div>
                ))}
              </div>
            );
          })()}

          {/* Tabela */}
          <div className="bg-[var(--v-card)] border border-[var(--v-border)] rounded-[var(--v-radius)] overflow-hidden">
            <div className="overflow-x-auto max-h-[55vh] overflow-y-auto custom-scrollbar">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[var(--v-deep)] sticky top-0 z-10">
                  <tr>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Status</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Cliente (Planilha)</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Dt Vencimento</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Dt Pagamento</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-accent-3)] text-right">Valor Planilha</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-accent)] text-right">Valor Vulcano</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Unidade / Contrato</th>
                    <th className="p-3 text-[10px] font-bold uppercase tracking-widest text-[var(--v-text-faint)]">Obs</th>
                  </tr>
                </thead>
                <tbody>
                  {matchData.map((r, idx) => {
                    const meta = STATUS_META[r.status] || { label: r.status, cls: 'bg-[#333] text-[var(--v-text-muted)] border-[var(--v-border)]' };
                    const fmt = v => v != null ? `R$ ${Number(v).toLocaleString('pt-BR', {minimumFractionDigits:2})}` : '-';
                    return (
                      <tr key={idx} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                        <td className="p-3">
                          <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-1 rounded border ${meta.cls}`}>{meta.label}</span>
                        </td>
                        <td className="p-3 font-bold text-[var(--v-text)] truncate max-w-[180px]">{r.cliente_planilha || '-'}</td>
                        <td className="p-3 text-[var(--v-text-muted)] font-mono">{r.dt_vencimento || '-'}</td>
                        <td className="p-3 text-[var(--v-text-muted)] font-mono">{r.dt_pagamento || '-'}</td>
                        <td className="p-3 text-right font-black text-[var(--v-accent-3)]">{fmt(r.valor_planilha)}</td>
                        <td className="p-3 text-right font-black text-[var(--v-accent)]">{fmt(r.valor_vulcano)}</td>
                        <td className="p-3 text-[var(--v-text-faint)] truncate max-w-[160px]">{r.unidade || r.contrato || '-'}</td>
                        <td className="p-3 text-[10px] text-[var(--v-text-faint)] truncate max-w-[140px]">{r.obs || '-'}</td>
                      </tr>
                    );
                  })}
                  {matchData.length === 0 && (
                    <tr><td colSpan="8" className="p-12 text-center text-[var(--v-text-faint)] uppercase tracking-widest text-[10px]">Nenhum resultado retornado pelo backend.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-between items-center bg-[var(--v-card)] p-4 border border-[var(--v-border)] rounded-[var(--v-radius)]">
            <div className="flex items-center gap-4">
              <button onClick={handleSaveTemplate} className="flex items-center gap-2 text-[var(--v-text-muted)] hover:text-[var(--v-accent-4)] transition-colors text-[10px] font-bold uppercase tracking-widest">
                <Save size={14} /> Salvar Template
              </button>
              <button onClick={handleDownloadTxt} className="flex items-center gap-2 text-[var(--v-text-muted)] hover:text-[#007aff] transition-colors text-[10px] font-bold uppercase tracking-widest">
                <Download size={14} /> Baixar TXT
              </button>
            </div>
            <div className="flex gap-4 items-center">
              <button onClick={() => setStep(2)} className="px-6 py-3 rounded-[var(--v-radius)] text-[var(--v-text-muted)] border border-[var(--v-border)] hover:text-[var(--v-text-bold)] hover:bg-[var(--v-hover)] text-[10px] uppercase font-bold tracking-widest transition-colors">Voltar ao DE-PARA</button>
              <div className="flex items-center gap-3 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest ml-4">
                <span>{matchData.filter(r=>r.status==='MATCH_PERFEITO').length} pronto(s)</span>
                <span className="text-[var(--v-border)]">|</span>
                <span>{matchData.filter(r=>r.status==='JA_QUITADO').length} quitado(s)</span>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
