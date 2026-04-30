import re

with open(r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\SmartImporter.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add queue state
queue_state = """
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
"""
content = content.replace("const [manualMatchModal, setManualMatchModal] = useState({ open: false, rowData: null, rowIndex: null });", 
                          "const [manualMatchModal, setManualMatchModal] = useState({ open: false, rowData: null, rowIndex: null });" + queue_state)

# 2. Add Template & Download logic
template_logic = """
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
      String(r.unidade || r.contrato || '').replace(/\\r?\\n|\\r/g, " "),
      r.obs || ''
    ]);
    const txtContent = [headers.join(";"), ...rows.map(r => r.join(";"))].join("\\n");
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
"""
content = content.replace("const getConfidenceColor", template_logic + "\n  const getConfidenceColor")

# 3. Restore UI elements (Template select, Empreendimento filter, Download TXT button)
# Adding Empreendimento and Apply Template to the DE-PARA header
ui_de_para_header = """
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
"""
content = content.replace("""
            <div className="flex items-center gap-3">
              <select 
                value={targetTable} 
                onChange={(e) => setTargetTable(e.target.value)}
                className="bg-[var(--v-deep)] border border-[var(--v-border)] text-[var(--v-text-bold)] py-1.5 px-3 rounded text-[11px] outline-none"
              >
                <option value="VENDAS">Destino: VENDAS</option>
                <option value="RECEBIMENTOS">Destino: RECEBIMENTOS</option>
              </select>
""", ui_de_para_header)

# Save Template button and Download TXT
ui_preview_header = """
            <div className="flex items-center gap-3">
              <button onClick={handleSaveTemplate} className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[var(--v-border)] rounded text-[11px] text-[var(--v-text-muted)] hover:text-[var(--v-text)] transition-colors">
                <Save size={12} /> Salvar Template
              </button>
              <button onClick={handleDownloadTxt} className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[var(--v-border)] rounded text-[11px] text-[#007aff] hover:bg-[#007aff]/10 transition-colors">
                <Download size={12} /> Baixar TXT
              </button>
              <button onClick={() => setStep(2)} className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--v-deep)] border border-[var(--v-border)] rounded text-[11px] font-medium hover:bg-[var(--v-hover)] transition-colors">
                Voltar
              </button>
"""
content = content.replace("""
            <div className="flex items-center gap-3">
              <button onClick={() => setStep(2)} className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--v-deep)] border border-[var(--v-border)] rounded text-[11px] font-medium hover:bg-[var(--v-hover)] transition-colors">
                Voltar
              </button>
""", ui_preview_header)

# Fila Automática in Copilot Section
# We will replace the "Aprender com correções" features grid with the Fila list if there are queue items.
ui_queue = """
          {queueItems.length > 0 ? (
            <div className="flex-1 mt-2 z-10 overflow-y-auto pr-2 custom-scrollbar space-y-2">
              <h4 className="text-[10px] font-bold text-[var(--v-text-bold)] uppercase tracking-widest flex items-center gap-2 mb-2">
                <Database size={12} className="text-[var(--v-accent)]" /> Fila Automática ({queueItems.length})
              </h4>
              {queueItems.map(item => (
                <div key={item.id} className="bg-black/30 border border-[var(--v-border)] p-2 rounded flex flex-col gap-1">
                  <div className="flex justify-between items-start">
                    <p className="text-[10px] font-bold text-[var(--v-text)] truncate max-w-[150px]" title={item.filename}>{item.filename}</p>
                    <div className="flex gap-1">
                      <button onClick={() => handleDeleteQueue(item.id)} className="text-[var(--v-text-faint)] hover:text-[#ff4d00]">
                        <X size={12} />
                      </button>
                      {item.status === 'AGUARDANDO_REVISAO' && (
                        <button onClick={() => handleApproveQueue(item.id, item.target_table)} disabled={queueLoading} className="text-[#007aff] hover:underline text-[9px] font-bold uppercase tracking-widest">
                          Revisar
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="text-[8px] uppercase tracking-widest text-[var(--v-text-muted)] flex justify-between">
                    <span>Destino: <span className="text-[var(--v-accent)]">{item.target_table}</span></span>
                    <span className="text-[#ffcc00]">{item.status}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 z-10 mb-auto">
              {[
                { icon: <Sparkles size={14}/>, label: 'Sugerir mapeamento', value: 'IA · 0.96' },
                { icon: <CheckCircle2 size={14}/>, label: 'Validar com regras', value: '+12 regras' },
                { icon: <AlertCircle size={14}/>, label: 'Marcar divergências', value: 'auto' },
                { icon: <Zap size={14}/>, label: 'Aprender com correções', value: 'on' }
              ].map((f, i) => (
                <div key={i} className="flex items-center gap-2 p-2 bg-black/30 border border-[var(--v-border)] rounded-md">
                  <div className="text-[var(--v-text-muted)]">{f.icon}</div>
                  <span className="flex-1 text-[11px] text-[var(--v-text-bold)] truncate">{f.label}</span>
                  <span className="font-mono text-[9px] text-[var(--v-text-faint)]">{f.value}</span>
                </div>
              ))}
            </div>
          )}
"""
content = content.replace("""
          <div className="grid grid-cols-2 gap-2 z-10 mb-auto">
            {[
              { icon: <Sparkles size={14}/>, label: 'Sugerir mapeamento', value: 'IA · 0.96' },
              { icon: <CheckCircle2 size={14}/>, label: 'Validar com regras', value: '+12 regras' },
              { icon: <AlertCircle size={14}/>, label: 'Marcar divergências', value: 'auto' },
              { icon: <Zap size={14}/>, label: 'Aprender com correções', value: 'on' }
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-2 p-2 bg-black/30 border border-[var(--v-border)] rounded-md">
                <div className="text-[var(--v-text-muted)]">{f.icon}</div>
                <span className="flex-1 text-[11px] text-[var(--v-text-bold)] truncate">{f.label}</span>
                <span className="font-mono text-[9px] text-[var(--v-text-faint)]">{f.value}</span>
              </div>
            ))}
          </div>
""", ui_queue)

# Full Manual Match Modal
ui_modal = """
      {manualMatchModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#111] border border-[var(--v-border)] rounded-xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
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
            
            <div className="p-6 border-b border-[var(--v-border)] bg-[#0b0b0b]">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#a259ff] mb-3">Dados da Planilha (Pagamento Efetuado)</h4>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-[#1a1a1a] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Cliente</p>
                  <p className="text-xs font-bold text-[var(--v-text)] truncate">{manualMatchModal.rowData?.cliente_planilha || '-'}</p>
                </div>
                <div className="bg-[#1a1a1a] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Vencimento</p>
                  <p className="text-xs font-mono text-[var(--v-text-muted)]">{manualMatchModal.rowData?.dt_vencimento || '-'}</p>
                </div>
                <div className="bg-[#1a1a1a] p-3 rounded border border-[var(--v-border)]">
                  <p className="text-[9px] uppercase tracking-widest text-[var(--v-text-faint)] mb-1">Pagamento</p>
                  <p className="text-xs font-mono text-[var(--v-text-muted)]">{manualMatchModal.rowData?.dt_pagamento || '-'}</p>
                </div>
                <div className="bg-[#1a1a1a] p-3 rounded border border-[var(--v-border)]">
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
                      <div key={p.id} className="flex items-center justify-between p-3 border border-[var(--v-border)] bg-[#0b0b0b] rounded hover:border-[#a259ff] transition-colors group">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="bg-[#1a1a1a] px-3 py-1 rounded text-xs font-mono text-[var(--v-text-muted)] w-16 text-center border border-[var(--v-border)]">
                            Nº {p.numero_parcela}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-[var(--v-text)] truncate">{p.cliente_nome}</p>
                            <p className="text-[10px] text-[var(--v-text-faint)] truncate">{p.descricao_unidade} | Venc: {p.data_vencimento}</p>
                          </div>
                          <div className="text-right px-4">
                            <p className="text-sm font-black text-[var(--v-accent)]">R$ {p.valor_parcela.toLocaleString('pt-BR', {minimumFractionDigits:2})}</p>
                            {diff !== 0 && (
                              <p className={`text-[9px] font-bold uppercase tracking-widest ${isAcrescimo ? 'text-[#ffcc00]' : 'text-[#34c759]'}`}>
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
                          className="px-4 py-2 bg-[var(--v-deep)] border border-[#a259ff]/30 text-[#a259ff] rounded text-[10px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 hover:bg-[#a259ff] hover:text-white transition-all ml-4"
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
"""

content = content.replace("""
      {/* Modal de Match Manual (simplified) */}
      {manualMatchModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#111] border border-[var(--v-border)] rounded-xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col">
            <div className="p-5 border-b border-[var(--v-border)] flex justify-between items-center bg-[var(--v-deep)]">
              <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--v-text-bold)]">🔗 Vincular Parcela Manualmente</h3>
              <button onClick={() => setManualMatchModal({open: false})} className="text-[var(--v-text-muted)] hover:text-[#ff4d4d] transition-colors"><X size={18} /></button>
            </div>
            <div className="p-6">
              <p className="text-sm text-[var(--v-text-muted)]">Funcionalidade de vinculação em desenvolvimento. O modal está ativo e recebendo dados da linha: <strong className="text-white">{manualMatchModal.rowData?.cliente_planilha}</strong></p>
            </div>
          </div>
        </div>
      )}
""", ui_modal)


with open(r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\SmartImporter.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("SmartImporter.jsx patched successfully.")
