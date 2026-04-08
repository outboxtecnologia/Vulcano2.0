import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, ChevronRight, FileSpreadsheet, Loader2, Database, AlertCircle, Sparkles, Save } from 'lucide-react';

const API_BASE = import.meta?.env?.VITE_API_BASE || 'http://127.0.0.1:8000';

export default function SmartImporter({ selectedEmpresa }) {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [columns, setColumns] = useState([]);
  const [previewData, setPreviewData] = useState([]);
  const [targetTable, setTargetTable] = useState('VENDAS');
  const [mapping, setMapping] = useState({});
  const [templates, setTemplates] = useState([]);

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
      setMapping(data.mapping || {});
      setStep(3);
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

  const handleFinalizeImport = async () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      alert("Importação concluída com sucesso! (Simulação)");
      setStep(1);
      setFile(null);
      setColumns([]);
      setMapping({});
    }, 1500);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto w-full">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tighter text-white uppercase flex items-center gap-3">
            <Sparkles className="text-[#a259ff]" size={36} /> Smart Importer IA
          </h2>
          <p className="text-sm text-[#888] mt-2 uppercase tracking-widest font-bold">Importação e de-para guiados por inteligência artificial</p>
        </div>
      </div>

      {/* Stepper Header */}
      <div className="flex items-center justify-between bg-[#131313] border border-[#333] p-6 rounded-sm">
        {[
          { num: 1, label: 'Upload de Planilha' },
          { num: 2, label: 'Análise de Contexto' },
          { num: 3, label: 'Validação Humana' },
          { num: 4, label: 'Processamento' }
        ].map((s, idx) => (
          <React.Fragment key={s.num}>
            <div className={`flex flex-col items-center gap-2 ${step >= s.num ? 'opacity-100' : 'opacity-40'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 ${step > s.num ? 'bg-[#a259ff] border-[#a259ff] text-white' : step === s.num ? 'border-[#a259ff] text-[#a259ff]' : 'border-[#444] text-[#888]'}`}>
                {step > s.num ? <CheckCircle2 size={18} /> : s.num}
              </div>
              <span className={`text-[10px] uppercase font-bold tracking-widest ${step >= s.num ? 'text-[#e5e2e1]' : 'text-[#666]'}`}>{s.label}</span>
            </div>
            {idx < 3 && <div className={`flex-1 h-px ${step > s.num ? 'bg-[#a259ff]' : 'bg-[#333]'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Upload */}
      {step === 1 && (
        <div className="bg-[#131313] border border-[#333] p-8 rounded-sm text-center">
          <FileSpreadsheet size={64} className="mx-auto text-[#444] mb-6" />
          <h3 className="text-xl font-bold text-white mb-2 uppercase tracking-widest">Selecione seu arquivo</h3>
          <p className="text-[#888] text-sm mb-8">Suporte para .XLS, .XLSX e .CSV. O sistema irá ler o cabeçalho automaticamente.</p>
          
          <form onSubmit={handleFileUpload} className="max-w-md mx-auto flex flex-col gap-4">
            <input 
              type="file" 
              accept=".csv, .xls, .xlsx"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full text-sm text-[#888] file:mr-4 file:py-3 file:px-4 file:rounded-sm file:border-0 file:text-[10px] file:font-bold file:uppercase file:tracking-widest file:bg-[#1a1a1c] file:text-[#007aff] hover:file:bg-[#222] file:cursor-pointer border border-[#333] bg-[#0b0b0b] p-2"
            />
            <button 
              type="submit" 
              disabled={loading || !file} 
              className="w-full bg-[#007aff] text-white py-4 rounded-sm font-bold uppercase tracking-widest text-[10px] hover:bg-[#005bb5] transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />}
              {loading ? 'Analisando Estrutura...' : 'Iniciar Importação'}
            </button>
          </form>
        </div>
      )}

      {/* Step 2: Análise de Contexto */}
      {step === 2 && (
        <div className="bg-[#131313] border border-[#333] rounded-sm p-8">
          <div className="flex items-center gap-4 mb-8 pb-6 border-b border-[#333]">
            <Sparkles className="text-[#a259ff]" size={32} />
            <div>
              <h3 className="text-xl font-bold text-white uppercase tracking-widest">Configuração da Inteligência Artificial</h3>
              <p className="text-[#888] text-sm">Defina o destino para o Gemini mapear colunas automaticamente (schema matching).</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-8 mb-8">
            <div>
              <label className="text-[10px] uppercase tracking-widest text-[#555] font-bold block mb-2">Entidade Destino (Vulcano/Questor)</label>
              <select 
                value={targetTable} 
                onChange={(e) => setTargetTable(e.target.value)}
                className="w-full bg-[#0b0b0b] border border-[#444] text-white p-4 rounded-sm outline-none focus:border-[#a259ff] text-sm font-bold tracking-widest uppercase transition-colors"
              >
                <option value="VENDAS">Vendas (Contratos)</option>
                <option value="RECEBIMENTOS">Recebimentos (Baixas)</option>
                <option value="EMPREENDIMENTOS">Empreendimentos</option>
                <option value="CLIENTES">Clientes / Fornecedores</option>
              </select>
            </div>
            <div className="bg-[#0b0b0b] p-4 border border-[#333] rounded-sm flex flex-col justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#555] font-bold mb-2">Aplicar Template Salvo</p>
                <select 
                  onChange={(e) => handleApplyTemplate(e.target.value)}
                  className="w-full bg-[#131313] border border-[#444] text-white p-3 rounded-sm outline-none text-xs font-bold tracking-widest uppercase transition-colors"
                >
                  <option value="">-- Selecione (Opcional) --</option>
                  {templates.filter(t => t.target_table === targetTable).map(t => (
                    <option key={t.id} value={t.mapping_json}>{t.nome}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-6 mt-4 pt-4 border-t border-[#333]">
                <div>
                  <p className="text-2xl font-black text-[#a259ff]">{columns.length}</p>
                  <p className="text-xs text-[#888]">Colunas Identificadas</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-4">
            <button onClick={() => setStep(1)} className="px-6 py-3 rounded-sm text-[#888] border border-[#333] hover:text-white hover:bg-[#1a1a1c] text-[10px] uppercase font-bold tracking-widest transition-colors">Voltar</button>
            <button 
              onClick={callGeminiMatching} 
              disabled={loading}
              className="bg-[#a259ff] text-white px-8 py-3 rounded-sm font-bold uppercase tracking-widest text-[10px] hover:bg-[#8e45e6] transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              {loading ? 'Rodando Inferência...' : 'Gerar De-Para (IA)'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Validação Humana / Mapping */}
      {step === 3 && (
        <div className="flex flex-col gap-6">
          <div className="bg-[#1a1a1c] border border-[#ffcc00]/30 p-4 rounded-sm flex items-start gap-4 shadow-lg">
            <AlertCircle className="text-[#ffcc00] shrink-0" size={24} />
            <div>
              <h4 className="text-[#ffcc00] font-bold uppercase tracking-widest text-sm mb-1">Revisão Humana Necessária</h4>
              <p className="text-[#aaa] text-xs leading-relaxed">A IA sugeriu os seguintes mapeamentos. Revise-os e faça os ajustes necessários antes de importar. Deixe o destino como "Não Importar" se a coluna for irrelevante.</p>
            </div>
          </div>

          <div className="bg-[#131313] border border-[#333] rounded-sm overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0a0a0a]">
                  <th className="p-4 border-b border-[#333] text-[10px] font-bold tracking-widest uppercase text-[#555] w-1/2">Coluna Origem (Planilha)</th>
                  <th className="p-4 border-b border-[#333] text-[10px] font-bold tracking-widest uppercase text-[#a259ff] w-1/2">Campo Destino ({targetTable})</th>
                </tr>
              </thead>
              <tbody>
                {columns.map((col, idx) => (
                  <tr key={idx} className="border-b border-[#222] hover:bg-[#1a1a1a] transition-colors">
                    <td className="p-4 text-sm font-bold text-[#ccc] flex flex-col gap-1">
                      {col}
                      <span className="text-[10px] text-[#666] font-normal truncate max-w-sm" title={previewData.length > 0 ? previewData[0][col] : ''}>
                        {previewData.length > 0 ? `Ex: ${previewData[0][col]}` : ''}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <ArrowUpRight size={14} className="text-[#444]" />
                        <select 
                          value={mapping[col] || ''} 
                          onChange={(e) => handleMappingChange(col, e.target.value)}
                          className={`w-full bg-[#0b0b0b] border ${mapping[col] && mapping[col] !== 'null' ? 'border-[#a259ff] text-[#e5e2e1]' : 'border-[#444] text-[#888]'} p-2 rounded-sm outline-none text-xs font-bold uppercase tracking-wider transition-colors`}
                        >
                          <option value="null">-- Não Importar --</option>
                          <option value="DATA">DATA</option>
                          <option value="TOTAL">TOTAL (VALOR)</option>
                          <option value="DESCRICAO">DESCRICAO</option>
                          <option value="CLIENTE_CNPJ">CLIENTE/CPF/CNPJ</option>
                          <option value="CLIENTE_NOME">NOME DO CLIENTE</option>
                          <option value="EMPREENDIMENTO">EMPREENDIMENTO</option>
                          <option value="UNIDADE">UNIDADE</option>
                          <option value="OBSERVACOES">OBSERVACOES</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center bg-[#131313] p-4 border border-[#333] rounded-sm">
            <button onClick={handleSaveTemplate} className="flex items-center gap-2 text-[#888] hover:text-[#007aff] transition-colors text-[10px] font-bold uppercase tracking-widest">
              <Save size={14} /> Salvar como Template
            </button>
            <div className="flex gap-4">
              <button onClick={() => setStep(2)} className="px-6 py-3 rounded-sm text-[#888] border border-[#333] hover:text-white hover:bg-[#1a1a1c] text-[10px] uppercase font-bold tracking-widest transition-colors">Voltar</button>
              <button 
                onClick={handleFinalizeImport} 
                disabled={loading}
                className="bg-[#34c759] text-black px-8 py-3 rounded-sm font-bold uppercase tracking-widest text-[10px] hover:opacity-80 transition-opacity disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                {loading ? 'Consolidando...' : 'Confirmar Importação'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
