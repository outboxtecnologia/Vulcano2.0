import codecs
import re

with codecs.open('frontend/src/VulcanoViews.jsx', 'r', 'utf-8') as f:
    content = f.read()

pattern = re.compile(r'^export const VendasView =.*?(?=\nexport const )', re.MULTILINE | re.DOTALL)
match = pattern.search(content)

if match:
    new_vendas_view = """export const VendasView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [distratoModal, setDistratoModal] = useState(null);
  const [condicoesModal, setCondicoesModal] = useState(null); // { venda, payload, loading, error }
  
  // Custom form state
  const [compradores, setCompradores] = useState([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
  const [condicoes, setCondicoes] = useState([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 100;

  const openCondicoes = async (venda) => {
    setCondicoesModal({ venda, payload: null, loading: true, error: '' });
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${encodeURIComponent(venda.id)}/condicoes`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
      setCondicoesModal({ venda, payload: json, loading: false, error: '' });
    } catch (e) {
      console.error(e);
      setCondicoesModal({ venda, payload: null, loading: false, error: e.message || 'Falha ao carregar condições.' });
    }
  };

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        setData(Array.isArray(d) ? d : []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(v => v.empreendimento))].sort();
  const filtered = data.filter(v => !empreendimentoFilter || v.empreendimento === empreendimentoFilter);

  useEffect(() => {
     setCurrentPage(1);
  }, [empreendimentoFilter]);

  const totalVgv = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);
  const totalDistratos = filtered.filter(v => v.distrato === 'S').reduce((acc, curr) => acc + (curr.total || 0), 0);

  // Pagination Math
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const addComprador = () => setCompradores([...compradores, { id: Date.now(), nome: '', cpf_cnpj: '', percentual: 0 }]);
  const updateComprador = (id, field, value) => setCompradores(compradores.map(c => c.id === id ? { ...c, [field]: value } : c));
  const removeComprador = (id) => setCompradores(compradores.filter(c => c.id !== id));

  const addCondicao = () => setCondicoes([...condicoes, { id: Date.now(), tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);
  const updateCondicao = (id, field, value) => setCondicoes(condicoes.map(c => c.id === id ? { ...c, [field]: value } : c));
  const removeCondicao = (id) => setCondicoes(condicoes.filter(c => c.id !== id));

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd);
    payload.compradores = compradores;
    payload.condicoes = condicoes;
    
    try {
      await fetch(`${API_BASE}/api/vulcano/vendas`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      alert("Venda cadastrada!"); 
      e.target.reset(); 
      setCompradores([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
      setCondicoes([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);
      setShowForm(false);
      
      // Reload Table
      setLoading(true);
      fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
        .then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
    } catch (err) { alert("Erro ao cadastrar."); }
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
      {/* HEADER STITCH */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
             <ShoppingCart className="text-[var(--v-accent-3)]" size={32}/> 
             Painel de Vendas
          </h2>
          <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Unidades Comercializadas e Distratos</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="bg-[var(--v-accent-3)] text-black text-[11px] font-bold uppercase tracking-widest px-4 py-3 rounded-sm hover:opacity-90 transition-opacity flex items-center gap-2">
          <Plus size={16}/> Cadastrar Venda
        </button>
      </div>
      
      {showForm && (
        <div className="magma-card border border-[var(--v-accent-3)]/30 rounded-sm p-6 animate-in slide-in-from-top-4 overflow-y-auto max-h-[60vh] custom-scrollbar">
          <div className="flex justify-between items-center mb-6 border-b border-[var(--v-border)] pb-3">
            <h3 className="text-xs uppercase tracking-widest text-[var(--v-accent-3)] font-black">Nova Venda</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-[var(--v-text-faint)] hover:text-white text-[10px] uppercase tracking-widest font-bold">FECHAR X</button>
          </div>
          
          <form className="flex flex-col gap-6" onSubmit={handleFormSubmit}>
            <input type="hidden" name="empresa_id" value={selectedEmpresa} />
            
            <div className="flex gap-4">
              <div className="w-24"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">ID Emp.</label><input name="id_empreendimento" type="number" required className="bento-input w-full" /></div>
              <div className="w-32"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Unidade</label><input name="unidade" required className="bento-input w-full" /></div>
              <div className="flex-1"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Total Venda</label><input name="total" type="number" step="0.01" required className="bento-input w-full" /></div>
              <div className="w-40"><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-1">Data Venda</label><input name="data" type="date" required className="bento-input w-full" /></div>
            </div>

            <div className="border border-[var(--v-border)] bg-[var(--v-surface-container)] p-4 rounded-sm">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold flex items-center gap-2"><Users size={12}/> Compradores / Sociedade</h4>
                <button type="button" onClick={addComprador} className="text-[var(--v-accent-3)] hover:text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Adicionar Comprador</button>
              </div>
              <div className="flex flex-col gap-3">
                {compradores.map((comp, idx) => (
                  <div key={comp.id} className="flex gap-3 items-end">
                    <div className="flex-1"><label className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest block mb-1">Nome/Razão Social</label><input value={comp.nome} onChange={(e) => updateComprador(comp.id, 'nome', e.target.value)} required className="bento-input w-full" /></div>
                    <div className="w-40"><label className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest block mb-1">CPF/CNPJ</label><input value={comp.cpf_cnpj} onChange={(e) => updateComprador(comp.id, 'cpf_cnpj', e.target.value)} required className="bento-input w-full" /></div>
                    <div className="w-24"><label className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest block mb-1">% Compra</label><input type="number" step="0.01" value={comp.percentual} onChange={(e) => updateComprador(comp.id, 'percentual', parseFloat(e.target.value) || 0)} required className="bento-input w-full text-right" /></div>
                    {compradores.length > 1 && (
                      <button type="button" onClick={() => removeComprador(comp.id)} className="bg-[var(--v-text-red)]/10 text-[var(--v-text-red)] border border-[var(--v-text-red)]/30 hover:bg-[var(--v-text-red)] hover:text-white p-2 rounded-sm mb-[1px] transition-colors"><AlertCircle size={14}/></button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-[var(--v-border)] bg-[var(--v-surface-container)] p-4 rounded-sm overflow-x-auto custom-scrollbar">
              <div className="flex justify-between items-center mb-4 min-w-[700px]">
                <h4 className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold flex items-center gap-2"><DollarSign size={12}/> Condições / Projeção</h4>
                <button type="button" onClick={addCondicao} className="text-[var(--v-accent)] hover:text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Nova Condição</button>
              </div>
              <div className="flex flex-col gap-3 min-w-[700px]">
                <div className="flex gap-3 px-1">
                  <span className="w-32 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Tipo</span>
                  <span className="w-20 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Qtd.</span>
                  <span className="flex-1 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">1º Vencimento</span>
                  <span className="flex-1 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Valor Base</span>
                  <span className="w-32 text-[10px] text-[var(--v-text-faint)] uppercase tracking-widest font-bold">Indexador</span>
                  <span className="w-8"></span>
                </div>
                {condicoes.map((cond, idx) => (
                  <div key={cond.id} className="flex gap-3 items-center">
                    <select value={cond.tipo} onChange={(e) => updateCondicao(cond.id, 'tipo', e.target.value)} className="bento-select w-32">
                      <option value="SINAL">Sinal/Ato</option>
                      <option value="MENSAL">Mensais</option>
                      <option value="REFORCO_ANUAL">Reforço Anual</option>
                      <option value="CHAVE">Balão das Chaves</option>
                      <option value="FINANCIAMENTO">Financiamento</option>
                    </select>
                    <input type="number" min="1" value={cond.quantidade} onChange={(e) => updateCondicao(cond.id, 'quantidade', parseInt(e.target.value) || 1)} required className="bento-input w-20 text-center" />
                    <input type="date" value={cond.vencimento} onChange={(e) => updateCondicao(cond.id, 'vencimento', e.target.value)} required className="bento-input flex-1" />
                    <input type="number" step="0.01" value={cond.valor} onChange={(e) => updateCondicao(cond.id, 'valor', e.target.value)} required className="bento-input flex-1" placeholder="R$" />
                    <select value={cond.indexador} onChange={(e) => updateCondicao(cond.id, 'indexador', e.target.value)} className="bento-select w-32">
                      <option value="NENHUM">Sem Indexador</option>
                      <option value="INCC">INCC</option>
                      <option value="IGPM">IGP-M</option>
                      <option value="IPCA">IPCA</option>
                    </select>
                    {condicoes.length > 1 ? (
                      <button type="button" onClick={() => removeCondicao(cond.id)} className="text-[var(--v-text-red)] hover:text-white w-8 flex justify-center"><AlertCircle size={16}/></button>
                    ) : <span className="w-8"></span>}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end mt-2">
              <button type="submit" className="bg-[var(--v-accent-3)] text-black text-[11px] font-bold uppercase tracking-widest px-8 py-3 rounded-sm hover:opacity-90 transition-opacity">Registrar Contrato de Venda</button>
            </div>
          </form>
        </div>
      )}

      {/* STITCH MASTER-DETAIL LAYOUT */}
      <div className="flex gap-6 h-[calc(100vh-220px)] overflow-hidden">
        {/* SIDEBAR MASTER */}
        <div className="w-64 magma-card rounded-sm flex flex-col shrink-0 border border-[var(--v-border)]">
          <div className="p-4 border-b border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center gap-2">
            <Building2 size={16} className="text-[var(--v-text-faint)]"/>
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-[var(--v-text-muted)]">Obras/Empreendimentos</h3>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            <div 
              onClick={() => setEmpreendimentoFilter('')}
              className={`p-3 text-xs font-bold cursor-pointer transition-colors rounded-sm ${empreendimentoFilter === '' ? 'text-[var(--v-accent-3)] bg-[var(--v-hover)]' : 'text-[var(--v-text-muted)] hover:text-[var(--v-text)] hover:bg-[var(--v-border)]'}`}
            >
              [ CONSOLIDADO GERAL ]
            </div>
            {uniqueEmps.map((emp, i) => (
              <div 
                key={i} 
                onClick={() => setEmpreendimentoFilter(emp)}
                className={`p-3 text-xs cursor-pointer transition-colors truncate rounded-sm ${empreendimentoFilter === emp ? 'text-[var(--v-accent-3)] bg-[var(--v-hover)] font-bold' : 'text-[var(--v-text-faint)] hover:text-[var(--v-text)] hover:bg-[var(--v-surface-container)]'}`} 
                title={emp}
              >
                {emp || 'Indefinido'}
              </div>
            ))}
          </div>
        </div>

        {/* DETAIL CONTENT */}
        <div className="flex-1 flex flex-col gap-5 overflow-hidden">
          {/* KPI BENTO GRIDS */}
          <div className="grid grid-cols-2 gap-5 shrink-0">
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent-3)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">VGV Lançado (Período / Empresa)</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalVgv)}</h4>
               </div>
               <ShoppingCart size={40} className="text-[var(--v-accent-3)] opacity-20 absolute -right-2 -bottom-2 group-hover:scale-110 transition-transform"/>
            </div>
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-text-red)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Total de Distratos Realizados</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalDistratos)}</h4>
               </div>
            </div>
          </div>

          {/* TABLE DATA GRID (PAGINATED) */}
          <div className="magma-card border border-[var(--v-border)] rounded-sm flex flex-col flex-1 overflow-hidden relative">
            {loading && (
               <div className="absolute inset-0 bg-[#00000099] backdrop-blur-sm flex flex-col items-center justify-center z-50">
                   <Loader2 className="animate-spin text-[var(--v-accent-3)] mb-3" size={40} />
                   <span className="text-[10px] font-bold uppercase tracking-widest text-white">Integrando Vendas Vulcano...</span>
               </div>
            )}
            <div className="overflow-auto flex-1">
               <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-[var(--v-surface-container)] sticky top-0 z-10 shadow-sm border-b border-[var(--v-border)]">
                     <tr>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold w-32 border-b border-[var(--v-border)]">Venda/Contrato</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Data</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Descrição/Unid.</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">CPF/CNPJ</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold border-b border-[var(--v-border)]">Cliente</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold border-b border-[var(--v-border)] text-right">Total Venda</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent)] uppercase font-bold border-b border-[var(--v-border)] text-center w-24">Condições</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-red)] uppercase font-bold border-b border-[var(--v-border)] text-center w-24">Distrato</th>
                     </tr>
                  </thead>
                  <tbody>
                     {paginatedData.map((v) => (
                       <tr key={v.id} className={`border-b border-[var(--v-border)] transition-colors hover:bg-[var(--v-hover)] ${v.distrato === 'S' ? 'bg-[var(--v-text-red)]/5 border-l-2 border-l-[var(--v-text-red)]' : ''}`}>
                          <td className="p-3 text-[var(--v-text-muted)] font-mono text-[11px]">{v.id} <span className="text-[var(--v-text-faint)] ml-1">#{v.num_cad}</span></td>
                          <td className="p-3 text-[var(--v-text-muted)] font-mono">{v.data}</td>
                          <td className="p-3 text-[var(--v-text)] font-bold truncate max-w-[200px]" title={v.descricao}>{v.descricao}</td>
                          <td className="p-3 text-[var(--v-text-faint)] font-mono">{v.cliente_cnpj}</td>
                          <td className="p-3 text-[var(--v-text-muted)] truncate max-w-[150px]" title={v.cliente_nome}>{v.cliente_nome}</td>
                          <td className={`p-3 text-right font-black text-[13px] ${v.distrato === 'S' ? 'text-[var(--v-text-red)]' : 'text-[var(--v-accent-3)]'}`}>{formatCurrency(v.total)}</td>
                          <td className="p-3 text-center">
                              <button onClick={() => openCondicoes(v)} className="text-[var(--v-accent)] border border-[var(--v-accent)]/40 hover:bg-[var(--v-accent)] hover:text-black transition-colors text-[9px] font-bold uppercase py-1 px-3 rounded-sm">Cond.</button>
                          </td>
                          <td className="p-3 text-center">
                              {v.distrato === 'S' ? (
                                  <span className="text-[var(--v-text-red)] text-[9px] uppercase font-bold px-2 py-0.5 bg-[var(--v-text-red)]/10 rounded">Anulado</span>
                              ) : (
                                  <button onClick={() => setDistratoModal(v)} className="text-[var(--v-text-muted)] border border-[var(--v-border)] hover:border-[var(--v-text-red)] hover:text-[var(--v-text-red)] transition-colors text-[9px] font-bold uppercase py-1 px-3 rounded-sm">Distratar</button>
                              )}
                          </td>
                       </tr>
                     ))}
                     {paginatedData.length === 0 && !loading && (
                        <tr><td colSpan="8" className="p-12 text-center text-[var(--v-text-faint)] uppercase tracking-widest text-[10px]">Nenhuma venda registrada para os filtros aplicados.</td></tr>
                     )}
                  </tbody>
               </table>
            </div>

            {/* PAGINATION FOOTER */}
            <div className="p-3 border-t border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center justify-between">
               <span className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest font-bold">
                  Exibindo {paginatedData.length} de {filtered.length} Registros
               </span>
               <div className="flex items-center gap-2">
                  <button onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))} disabled={currentPage === 1} className="bento-button disabled:opacity-30">PÁG ANTERIOR</button>
                  <span className="text-[10px] text-[var(--v-text)] uppercase font-bold tracking-widest px-4">{currentPage} / {totalPages || 1}</span>
                  <button onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))} disabled={currentPage === totalPages || totalPages === 0} className="bento-button disabled:opacity-30">PRÓXIMA PÁG</button>
               </div>
            </div>
          </div>
        </div>
      </div>

      {/* DISTRATO MODAL (STITCH) */}
      {distratoModal && (
        <div className="fixed inset-0 bg-[#000000CC] backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in">
          <div className="magma-card border border-[var(--v-text-red)] p-7 rounded-sm max-w-md w-full shadow-[0_0_50px_rgba(255,59,48,0.15)]">
            <h3 className="text-sm uppercase tracking-widest text-[var(--v-text-red)] font-black mb-5">Registrar Distrato/Rescisão</h3>
            
            <div className="bg-[var(--v-surface-container)] p-4 border border-[var(--v-border)] rounded-sm mb-5">
              <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Alvo do Distrato</p>
              <p className="text-sm font-bold text-[var(--v-text-bold)] block truncate mb-1">{distratoModal.descricao}</p>
              <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-muted)] font-bold">Cliente: {distratoModal.cliente_nome}</p>
            </div>
            
            <form className="flex flex-col gap-4" onSubmit={async (e) => {
              e.preventDefault();
              const fd = new FormData(e.target);
              fd.append('id_venda', distratoModal.id);
              try {
                await fetch(`${API_BASE}/api/distratos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
                alert("Distrato registrado com sucesso!"); 
                setDistratoModal(null);
                setLoading(true);
                fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
                  .then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
              } catch (err) { alert("Erro ao registrar distrato."); }
            }}>
              <div><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-2">Data do Distrato</label><input name="data_distrato" type="date" required className="bento-input w-full" /></div>
              <div><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-2">Valor Total a Devolver (R$)</label><input name="valor_devolvido" type="number" step="0.01" required className="bento-input w-full" /></div>
              <div><label className="text-[10px] text-[var(--v-text-muted)] uppercase tracking-widest block mb-2">Data Previsão Pagto</label><input name="data_pagamento" type="date" required className="bento-input w-full" /></div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setDistratoModal(null)} className="bento-button border-transparent hover:bg-[var(--v-hover)]">Cancelar</button>
                <button type="submit" className="bg-[var(--v-text-red)] text-white text-[10px] font-bold uppercase tracking-widest px-6 py-3 rounded-sm hover:opacity-90 transition-opacity">Confirmar Averbação</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONDICOES MODAL (STITCH) */}
      {condicoesModal && (
        <div className="fixed inset-0 bg-[#000000CC] backdrop-blur-sm flex items-center justify-center z-[99999] animate-in fade-in p-6">
          <div className="magma-card border border-[var(--v-accent)] p-6 rounded-sm w-full max-w-[1400px] h-full max-h-[85vh] flex flex-col shadow-[0_0_50px_rgba(52,199,89,0.1)]">
            <div className="flex justify-between items-start border-b border-[var(--v-border)] pb-4 mb-5 shrink-0">
               <div>
                  <h3 className="text-lg uppercase tracking-widest text-[var(--v-accent)] font-black flex items-center gap-3">
                     <Layers size={22}/> Estrutura Financeira da Venda
                  </h3>
                  <p className="text-[11px] text-[var(--v-text-faint)] uppercase tracking-widest mt-1">
                     Venda #{condicoesModal.venda?.id} <span className="mx-2">•</span> {condicoesModal.venda?.descricao}
                  </p>
               </div>
               <button onClick={() => setCondicoesModal(null)} className="bento-button border-transparent hover:bg-[var(--v-hover)]"><X size={18}/></button>
            </div>
            
            <div className="flex-1 overflow-auto custom-scrollbar flex flex-col gap-6">
               {condicoesModal.loading && (
                 <div className="flex flex-col items-center justify-center h-40 text-[var(--v-text-muted)] gap-3 bg-[var(--v-surface-container)] rounded-sm border border-[var(--v-border)]">
                   <Loader2 className="animate-spin text-[var(--v-accent)]" size={32} />
                   <span className="text-[10px] uppercase tracking-widest font-bold">Resgatando Fluxo Vulcano...</span>
                 </div>
               )}
               
               {!condicoesModal.loading && condicoesModal.error && (
                 <div className="magma-card border-l-4 border-l-[var(--v-text-red)] p-5">
                   <h4 className="text-[var(--v-text-red)] font-bold mb-2">Erro de Resgate</h4>
                   <p className="text-[var(--v-text-muted)] text-sm">{condicoesModal.error}</p>
                 </div>
               )}
               
               {!condicoesModal.loading && condicoesModal.payload && (
                  <>
                    <div className="grid grid-cols-3 gap-5">
                       <div className="bg-[var(--v-surface-container)] border border-[var(--v-border)] p-4 rounded-sm flex flex-col justify-center">
                          <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold">Target VGV</span>
                          <span className="text-xl font-black text-[var(--v-accent-3)]">{formatCurrency(condicoesModal.payload.venda?.total || 0)}</span>
                       </div>
                       <div className="bg-[var(--v-surface-container)] border border-[var(--v-border)] p-4 rounded-sm">
                          <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold">Cliente Base</span>
                          <span className="text-sm font-bold text-[var(--v-text)] block truncate">{condicoesModal.payload.venda?.cliente?.nome || '-'}</span>
                          <span className="text-[10px] uppercase font-mono text-[var(--v-text-muted)]">{condicoesModal.payload.venda?.cliente?.cnpj || ''}</span>
                       </div>
                       <div className="bg-[var(--v-surface-container)] border border-[var(--v-border)] p-4 rounded-sm">
                          <span className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold">Ref. Data</span>
                          <span className="text-sm font-bold text-[var(--v-text)] block">{condicoesModal.payload.venda?.data || '-'}</span>
                          <span className="text-[10px] uppercase text-[var(--v-text-muted)] truncate block">{condicoesModal.payload.venda?.empreendimento || '-'}</span>
                       </div>
                    </div>
                    
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-full min-h-0">
                       {/* FORMAS DE PAGAMENTO */}
                       <div className="flex flex-col border border-[var(--v-border)] rounded-sm overflow-hidden bg-[var(--v-surface-container)]">
                          <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)]">
                             <h4 className="text-[10px] tracking-widest uppercase font-bold text-[var(--v-text-bold)]">Quadro de Condições Formais</h4>
                          </div>
                          <div className="flex-1 overflow-auto">
                             <table className="w-full text-left text-[11px] border-collapse">
                                <thead className="bg-[#0f0f0f] border-b border-[var(--v-border)] sticky top-0">
                                   <tr>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest">Macro Componente</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">Montante Base</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">Aberturas</th>
                                   </tr>
                                </thead>
                                <tbody>
                                  {(condicoesModal.payload.formas_pagto || []).map(f => (
                                     <tr key={f.id} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                                        <td className="p-3 font-bold text-[var(--v-text-muted)]">{f.descricao || '-'}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-text)] font-semibold">{formatCurrency(f.valor || 0)}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-text-faint)]">{f.quantidade_parcelas || 0} p.</td>
                                     </tr>
                                  ))}
                                  {(condicoesModal.payload.formas_pagto || []).length === 0 && (
                                     <tr><td colSpan="3" className="p-10 text-center text-[var(--v-text-faint)] italic text-[10px] uppercase">Nenhuma condição comercial fixada.</td></tr>
                                  )}
                                </tbody>
                             </table>
                          </div>
                       </div>
                       
                       {/* PLANILHA RECEBER (PARCELAS) */}
                       <div className="flex flex-col border border-[var(--v-border)] rounded-sm overflow-hidden bg-[var(--v-surface-container)]">
                          <div className="p-3 bg-[var(--v-hover)] border-b border-[var(--v-border)] flex justify-between items-center">
                             <h4 className="text-[10px] tracking-widest uppercase font-bold text-[var(--v-text-bold)]">Projeção Dinâmica (Contas a Receber)</h4>
                             <span className="text-[10px] text-[var(--v-text-faint)] font-mono">{(condicoesModal.payload.parcelas || []).length} Títulos</span>
                          </div>
                          <div className="flex-1 overflow-auto">
                             <table className="w-full text-left text-[11px] border-collapse">
                                <thead className="bg-[#0f0f0f] border-b border-[var(--v-border)] sticky top-0">
                                   <tr>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest whitespace-nowrap">Venc. / Nº</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">R$ Parcela</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">R$ Variação</th>
                                     <th className="p-3 text-[10px] text-[var(--v-text-faint)] uppercase font-bold tracking-widest text-right">Status Quitação</th>
                                   </tr>
                                </thead>
                                <tbody>
                                  {(condicoesModal.payload.parcelas || []).map(p => (
                                     <tr key={p.id} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] transition-colors">
                                        <td className="p-3 font-mono text-[var(--v-text-muted)] whitespace-nowrap">{p.data || '-'} <span className="opacity-30">|</span> {p.parcela || '-'}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-text)] font-semibold">{formatCurrency(p.valor_parcela || 0)}</td>
                                        <td className="p-3 text-right font-mono text-[var(--v-accent-6)]">{p.variacao > 0 ? formatCurrency(p.variacao) : '-'}</td>
                                        <td className={`p-3 text-right font-mono font-bold font-black flex justify-end gap-2 items-center ${(p.total_pago || 0) > 0 ? 'text-[var(--v-accent)]' : 'text-[var(--v-text-faint)]'}`}>
                                          {(p.total_pago || 0) > 0 ? <><CheckCircle size={10}/> {formatCurrency(p.total_pago)}</> : 'Aberto'}
                                        </td>
                                     </tr>
                                  ))}
                                  {(condicoesModal.payload.parcelas || []).length === 0 && (
                                     <tr><td colSpan="4" className="p-10 text-center text-[var(--v-text-faint)] italic text-[10px] uppercase">Nenhum título projetado.</td></tr>
                                  )}
                                </tbody>
                             </table>
                          </div>
                       </div>
                    </div>
                  </>
               )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};"""

    modified_content = content[:match.start()] + new_vendas_view + "\n" + content[match.end():]
    with codecs.open('frontend/src/VulcanoViews.jsx', 'w', 'utf-8') as f:
        f.write(modified_content)
    print("SUCCESS: VendasView replaced with paginated Stitch layout!")
else:
    print("ERROR: Could not find VendasView in VulcanoViews.jsx")
