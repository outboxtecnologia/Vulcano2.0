import sys
import re

file_path = r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# Ache start de VendasView
start_idx = code.find("export const VendasView =")
if start_idx == -1:
    print("VendasView não encontrado!")
    sys.exit(1)

# Ache a proxima view (RecebimentosView)
end_idx = code.find("export const RecebimentosView =", start_idx)
if end_idx == -1:
    print("RecebimentosView não encontrado para servir de âncora!")
    sys.exit(1)

new_component = """export const VendasView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [periodoFilter, setPeriodoFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('ATIVAS');
  
  const [showForm, setShowForm] = useState(false);
  const [distratoModal, setDistratoModal] = useState(null);
  const [condicoesModal, setCondicoesModal] = useState(null); 
  
  // Custom form state
  const [compradores, setCompradores] = useState([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
  const [condicoes, setCondicoes] = useState([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);
  
  const [empreendimentosList, setEmpreendimentosList] = useState([]);
  const [formIdEmp, setFormIdEmp] = useState('');
  const [unidadesList, setUnidadesList] = useState([]);
  const [unidadesSelected, setUnidadesSelected] = useState([]);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;
  
  useEffect(() => {
    if (!selectedEmpresa) return;
    fetch(`${API_BASE}/api/vulcano/empreendimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => setEmpreendimentosList(d || []))
      .catch(console.error);
  }, [selectedEmpresa]);

  useEffect(() => {
    if (!formIdEmp) {
      setUnidadesList([]);
      setUnidadesSelected([]);
      return;
    }
    fetch(`${API_BASE}/api/vulcano/empreendimentos/${formIdEmp}/detalhes`)
      .then(res => res.json())
      .then(d => {
        setUnidadesList(d.unidades || []);
      })
      .catch(console.error);
  }, [formIdEmp]);

  const buscarCliente = async (id, cpf) => {
    if (!cpf || cpf.length < 11) return;
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/clientes/search?cpf_cnpj=${encodeURIComponent(cpf)}`);
      const data = await res.json();
      if (data.found && data.nome) {
         updateComprador(id, 'nome', data.nome);
      }
    } catch (e) { console.error('Erro buscar cliente', e); }
  };

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

  const fetchVendas = () => {
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
  };

  useEffect(() => {
    fetchVendas();
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(v => v.empreendimento))].sort();
  
  // Date Utilities
  const filterByDays = (days) => {
     setPeriodoFilter(days);
  };
  
  const filtered = data.filter(v => {
    let ok = true;
    if (empreendimentoFilter && v.empreendimento !== empreendimentoFilter) ok = false;
    
    // Status Filter
    if (statusFilter === 'ATIVAS' && v.distrato === 'S') ok = false;
    if (statusFilter === 'DISTRATADAS' && v.distrato !== 'S') ok = false;
    
    // Date filter
    if (periodoFilter) {
       if (!v.data) {
          ok = false;
       } else {
          const parts = v.data.split('/');
          if (parts.length === 3) {
             const vDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}T12:00:00`);
             const limit = new Date();
             limit.setDate(limit.getDate() - parseInt(periodoFilter));
             if (vDate < limit) ok = false;
          }
       }
    }
    
    return ok;
  });

  useEffect(() => {
     setCurrentPage(1);
  }, [empreendimentoFilter, periodoFilter, statusFilter]);

  const totalVgv = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);
  const ticketMedio = filtered.length > 0 ? (totalVgv / filtered.length) : 0;
  
  // Mock para status de estoques based on unique properties?
  // We'll use a static 82% with current unit count logic if available, or just derived from count.
  const maxCapacity = 200; 
  const currentSalesCount = filtered.length;
  const porcentagemVendido = Math.min(100, Math.max(0, (currentSalesCount / maxCapacity) * 100));

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
    payload.unidades_selecionadas = unidadesSelected;
    
    const descricoes = unidadesList.filter(u => unidadesSelected.includes(u.id)).map(u => u.descricao).join(" + ");
    payload.unidade = descricoes || "ND";
    payload.permuta = fd.get("permuta") ? "S" : "N";
    
    try {
      await fetch(`${API_BASE}/api/vulcano/vendas`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      alert("Venda cadastrada!"); 
      e.target.reset(); 
      setCompradores([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
      setCondicoes([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);
      setUnidadesSelected([]);
      setFormIdEmp('');
      setShowForm(false);
      fetchVendas();
    } catch (err) { alert("Erro ao cadastrar."); }
  };

  return (
    <div className="flex flex-col h-full bg-[#0c0c0c] text-white p-6 md:p-10 font-sans animate-in fade-in max-w-[1600px] mx-auto w-full">
      {/* HEADER */}
      <div className="flex justify-between items-end mb-8 shrink-0">
        <div>
          <h2 className="text-4xl font-black tracking-tighter uppercase text-white mb-2 shadow-sm drop-shadow-md">VENDAS</h2>
          <p className="text-[10px] text-[#ff4d00] font-bold uppercase tracking-[0.2em]">TRANSACTION LEDGER & REAL ESTATE INVENTORY TRACKING</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="bg-[#ff4d00] text-black text-xs font-black uppercase tracking-widest px-6 py-3 rounded hover:bg-white transition-colors duration-300 flex items-center gap-2 shadow-[0_0_20px_rgba(255,77,0,0.3)]">
          <Plus size={16}/> NOVA VENDA
        </button>
      </div>

      {/* FILTER RIBBON */}
      <div className="flex flex-wrap lg:flex-nowrap gap-6 items-end mb-8 shrink-0">
         <div className="w-56 text-left">
            <label className="text-[9px] text-[#777] font-bold uppercase tracking-[0.15em] mb-2 block">Filtrar por Empreendimento</label>
            <div className="relative">
               <Building2 size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555]"/>
               <select value={empreendimentoFilter} onChange={e => setEmpreendimentoFilter(e.target.value)} className="w-full bg-[#151515] text-[#ccc] border border-white/10 rounded pl-9 pr-3 py-3 text-xs font-bold appearance-none cursor-pointer focus:outline-none focus:border-[#ff4d00]/50 transition-colors">
                  <option value="">Todas as Unidades</option>
                  {uniqueEmps.map((emp, i) => <option key={i} value={emp}>{emp}</option>)}
               </select>
               <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#555] pointer-events-none"/>
            </div>
         </div>
         
         <div className="w-56 text-left">
            <label className="text-[9px] text-[#777] font-bold uppercase tracking-[0.15em] mb-2 block">Período</label>
            <div className="relative">
               <Calendar size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555]"/>
               <select value={periodoFilter} onChange={e => filterByDays(e.target.value)} className="w-full bg-[#151515] text-[#ccc] border border-white/10 rounded pl-9 pr-3 py-3 text-xs font-bold appearance-none cursor-pointer focus:outline-none focus:border-[#ff4d00]/50 transition-colors">
                  <option value="">Todo o Período</option>
                  <option value="30">Últimos 30 Dias</option>
                  <option value="90">Últimos 90 Dias</option>
                  <option value="365">Último Ano</option>
               </select>
               <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#555] pointer-events-none"/>
            </div>
         </div>

         <div className="w-48 text-left">
            <label className="text-[9px] text-[#777] font-bold uppercase tracking-[0.15em] mb-2 block">Status</label>
            <div className="relative">
               <Layers size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555]"/>
               <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-full bg-[#151515] text-[#ccc] border border-white/10 rounded pl-9 pr-3 py-3 text-xs font-bold appearance-none cursor-pointer focus:outline-none focus:border-[#ff4d00]/50 transition-colors">
                  <option value="TODAS">Consolidado</option>
                  <option value="ATIVAS">Ativas</option>
                  <option value="DISTRATADAS">Distratadas</option>
               </select>
               <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#555] pointer-events-none"/>
            </div>
         </div>

         <button onClick={fetchVendas} disabled={loading} className="w-11 h-11 rounded bg-[#151515] hover:bg-[#222] border border-white/10 flex items-center justify-center text-[#777] hover:text-white transition-colors">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
         </button>
      </div>

      {/* REGISTRATION FORM (Conditional) */}
      {showForm && (
        <div className="mb-8 bg-[#151515] border border-[#ff4d00]/30 rounded p-6 shadow-xl relative animate-in fade-in slide-in-from-top-4 shrink-0">
          <div className="flex justify-between items-center border-b border-white/5 pb-4 mb-6">
            <h3 className="text-xs font-black uppercase tracking-widest text-[#ff4d00]">Realizar Nova Venda</h3>
            <button onClick={() => setShowForm(false)} className="text-[#555] hover:text-white text-[10px] font-bold tracking-widest uppercase transition-colors">FECHAR X</button>
          </div>
          
          <form className="flex flex-col gap-6" onSubmit={handleFormSubmit}>
            <input type="hidden" name="empresa_id" value={selectedEmpresa} />
            
            <div className="flex gap-4">
              <div className="w-52 text-left"><label className="text-[9px] text-[#777] uppercase tracking-widest mb-1 block">Empreendimento</label>
                  <select name="id_empreendimento" required value={formIdEmp} onChange={(e) => setFormIdEmp(e.target.value)} className="w-full bg-[#0a0a0a] text-[#ccc] border border-white/10 rounded p-3 text-xs focus:outline-none focus:border-[#ff4d00]/50">
                    <option value="">Selecione...</option>
                    {empreendimentosList.map(emp => <option key={emp.id} value={emp.id}>{emp.nome}</option>)}
                  </select>
              </div>
              <div className="flex-1 min-w-[200px] text-left"><label className="text-[9px] text-[#777] uppercase tracking-widest mb-1 block">Unidades / Garagens Vinculadas</label>
                  <div className="flex flex-wrap gap-2 max-h-24 min-h-[42px] overflow-y-auto custom-scrollbar border border-white/10 p-2 rounded bg-[#0a0a0a]">
                    {unidadesList.length === 0 ? <span className="text-[10px] text-[#555] italic">Selecione o Empreendimento p/ carregar.</span> :
                     unidadesList.map(u => (
                      <label key={u.id} className={`flex items-center gap-2 text-[10px] px-2 py-1.5 rounded cursor-pointer border transition-colors ${unidadesSelected.includes(u.id) ? 'bg-[#ff4d00]/20 border-[#ff4d00]/50 text-white' : 'bg-[#151515] hover:bg-[#222] border-white/5 text-[#888]'}`}>
                        <input type="checkbox" checked={unidadesSelected.includes(u.id)} onChange={(e) => {
                          if (e.target.checked) setUnidadesSelected([...unidadesSelected, u.id]);
                          else setUnidadesSelected(unidadesSelected.filter(id => id !== u.id));
                        }} className="hidden" />
                        <span className="truncate max-w-[150px] font-bold tracking-widest">{u.descricao}</span>
                      </label>
                    ))}
                  </div>
              </div>
              <div className="w-40 text-left"><label className="text-[9px] text-[#777] uppercase tracking-widest mb-1 block">Data Venda</label><input name="data" type="date" required className="w-full bg-[#0a0a0a] text-[#ccc] border border-white/10 rounded p-3 text-xs focus:outline-none focus:border-[#ff4d00]/50" /></div>
              <div className="w-44 text-left"><label className="text-[9px] text-[#777] uppercase tracking-widest mb-1 block">Total Montante R$</label><input name="total" type="number" step="0.01" required className="w-full bg-[#0a0a0a] text-[#ccc] border border-white/10 rounded p-3 text-xs focus:outline-none focus:border-[#ff4d00]/50" /></div>
            </div>

            <div className="border border-white/5 bg-[#0a0a0a] p-4 rounded text-left">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-[10px] text-[#777] uppercase tracking-widest font-bold flex items-center gap-2"><Users size={12}/> Compradores / Sociedade</h4>
                <button type="button" onClick={addComprador} className="text-[#ff4d00] hover:text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-1"><Plus size={12}/> Adicionar</button>
              </div>
              <div className="flex flex-col gap-3">
                {compradores.map((comp) => (
                  <div key={comp.id} className="flex gap-3 items-end">
                    <div className="w-44">
                        <label className="text-[9px] text-[#555] uppercase tracking-widest mb-1 block">CPF/CNPJ (Busca Auto)</label>
                        <input value={comp.cpf_cnpj} onChange={(e) => updateComprador(comp.id, 'cpf_cnpj', e.target.value)} onBlur={() => buscarCliente(comp.id, comp.cpf_cnpj)} required className="w-full bg-[#111] border border-white/10 p-3 text-xs rounded focus:border-[#ff4d00]/50 outline-none" placeholder="000.000.000-00" />
                    </div>
                    <div className="flex-1"><label className="text-[9px] text-[#555] uppercase tracking-widest mb-1 block">Nome/Razão Social</label><input value={comp.nome} onChange={(e) => updateComprador(comp.id, 'nome', e.target.value)} required className="w-full bg-[#111] border border-white/10 p-3 text-xs rounded focus:border-[#ff4d00]/50 outline-none" /></div>
                    <div className="w-24"><label className="text-[9px] text-[#555] uppercase tracking-widest mb-1 block">% Compra</label><input type="number" step="0.01" value={comp.percentual} onChange={(e) => updateComprador(comp.id, 'percentual', parseFloat(e.target.value) || 0)} required className="w-full bg-[#111] border border-white/10 p-3 text-xs rounded focus:border-[#ff4d00]/50 text-right text-[#ff4d00] font-mono outline-none" /></div>
                    {compradores.length > 1 && (
                      <button type="button" onClick={() => removeComprador(comp.id)} className="bg-red-500/10 text-red-500 border border-red-500/30 hover:bg-red-500 hover:text-white p-3 rounded mb-[1px] transition-colors"><AlertCircle size={14}/></button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end mt-2">
              <button type="submit" className="bg-[#ff4d00] text-black text-xs font-black uppercase tracking-widest px-8 py-4 rounded hover:bg-white transition-colors duration-300 shadow-[0_0_15px_rgba(255,77,0,0.3)]">Registrar Venda</button>
            </div>
          </form>
        </div>
      )}

      {/* DATA GRID */}
      <div className="bg-[#111] border border-white/5 rounded flex flex-col flex-1 overflow-hidden min-h-[400px]">
         <div className="flex-1 overflow-auto relative">
            {loading && (
               <div className="absolute inset-0 bg-black/50 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                  <Loader2 className="animate-spin text-[#ff4d00] mb-4" size={32} />
                  <span className="text-[10px] font-bold text-white uppercase tracking-widest">Sincronizando Base ERP...</span>
               </div>
            )}
            <table className="w-full text-left border-collapse">
               <thead className="bg-[#181818] border-b border-white/5 sticky top-0 z-10">
                  <tr>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase w-28 text-left">ID</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase w-32 text-left">DATA</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase text-left">EMPREENDIMENTO</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase text-left">DESCRIÇÃO (UNIDADE)</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase text-left">CLIENTE</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase text-left">CNPJ/CPF</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase text-right">TOTAL (BRL)</th>
                     <th className="p-4 text-[9px] text-[#666] tracking-[0.2em] font-black uppercase text-center w-36">AÇÕES</th>
                  </tr>
               </thead>
               <tbody>
                  {paginatedData.map((v) => (
                     <tr key={v.id} className={`hover:bg-white/[0.02] border-b border-white/[0.02] transition-colors ${v.distrato === 'S' ? 'opacity-50' : ''}`}>
                        <td className="p-4">
                           <span className="text-xs font-mono text-[#555]">#{v.distrato !== 'S' ? 'VL-' : 'DS-'}{v.id}</span>
                        </td>
                        <td className="p-4 text-xs font-bold text-[#888]">{v.data}</td>
                        <td className="p-4 text-[11px] font-bold text-[#aaa] uppercase tracking-wider truncate max-w-[150px]">{v.empreendimento}</td>
                        <td className="p-4 text-xs font-bold text-white uppercase tracking-wider">{v.descricao}</td>
                        <td className="p-4 text-xs font-medium text-[#ccc] truncate max-w-[180px]">{v.cliente_nome}</td>
                        <td className="p-4 text-[10px] font-mono text-[#666]">{v.cliente_cnpj}</td>
                        <td className={`p-4 text-sm font-black text-right tracking-tight ${v.distrato === 'S' ? 'text-red-500/50 line-through' : 'text-[#ff4d00]'}`}>
                           {formatCurrency(v.total)}
                        </td>
                        <td className="p-4 text-center">
                           <div className="flex items-center justify-center gap-1.5">
                              {v.distrato === 'S' ? (
                                <span className="bg-red-500/10 text-red-500 text-[8px] uppercase tracking-widest font-bold py-1 px-3 rounded">Rescindido</span>
                              ) : (
                                <>
                                  <button onClick={() => openCondicoes(v)} className="bg-[#222] hover:bg-white hover:text-black text-[#888] border border-white/10 text-[9px] uppercase tracking-widest font-bold py-1.5 px-3 rounded transition-colors flex items-center justify-center gap-1" title="Ver Detalhes Bancários">
                                     <Eye size={12}/> Detalhes
                                  </button>
                                  <button onClick={() => setDistratoModal(v)} className="text-[#666] hover:text-red-500 hover:bg-red-500/10 text-[9px] uppercase tracking-widest font-bold py-1.5 px-2 rounded transition-colors" title="Efetuar Distrato">
                                     <X size={14}/>
                                  </button>
                                </>
                              )}
                           </div>
                        </td>
                     </tr>
                  ))}
                  {paginatedData.length === 0 && !loading && (
                     <tr><td colSpan="8" className="py-20 text-center text-[#555] text-[10px] uppercase tracking-widest">Nenhuma venda encontrada p/ os filtros aplicados.</td></tr>
                  )}
               </tbody>
            </table>
         </div>
         {/* PAGINATION */}
         <div className="p-4 border-t border-white/5 flex justify-between items-center bg-[#181818] shrink-0">
             <span className="text-[9px] text-[#555] uppercase font-black tracking-[0.2em]">
                Exibindo {currentPage * ITEMS_PER_PAGE - ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)} de {filtered.length} Vendas
             </span>
             <div className="flex gap-1.5 items-center">
                 <button onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))} disabled={currentPage === 1} className="bg-[#222] p-1.5 px-4 text-[#777] rounded hover:text-white disabled:opacity-30 transition-colors text-[9px] font-bold uppercase tracking-widest">ANTERIOR</button>
                 <div className="flex items-center bg-[#ff4d00] text-black font-black h-8 w-8 justify-center rounded text-xs mx-2 shadow-[0_0_10px_rgba(255,77,0,0.3)]">{currentPage}</div>
                 <button onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))} disabled={currentPage >= totalPages && totalPages > 0} className="bg-[#222] p-1.5 px-4 text-[#777] rounded hover:text-white disabled:opacity-30 transition-colors text-[9px] font-bold uppercase tracking-widest">PRÓXIMO</button>
             </div>
         </div>
      </div>

      {/* FOOTER KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 shrink-0">
         <div className="border border-white/5 bg-[#121212] rounded p-6 relative">
            <h4 className="text-[10px] text-[#888] font-bold uppercase tracking-[0.2em] mb-2">VGV Lançado (Métricas Atuais)</h4>
            <div className="text-3xl font-bold tracking-tight text-white mb-2">{formatCurrency(totalVgv)}</div>
            <p className="text-[10px] font-bold text-[#60A5FA] bg-[#60A5FA]/10 inline-block px-2 py-0.5 rounded"><Activity size={10} className="inline mr-1"/> Com base em {filtered.length} transações</p>
         </div>
         <div className="border border-white/5 bg-[#121212] rounded p-6 relative border-l border-l-white/10">
            <h4 className="text-[10px] text-[#888] font-bold uppercase tracking-[0.2em] mb-2">TICKET MÉDIO</h4>
            <div className="text-3xl font-bold tracking-tight text-white mb-2">{formatCurrency(ticketMedio)}</div>
            <p className="text-[10px] font-bold text-[#888]">Unidade padrão (Global)</p>
         </div>
         <div className="border border-white/5 bg-[#121212] rounded p-6 relative">
            <h4 className="text-[10px] text-[#888] font-bold uppercase tracking-[0.2em] mb-4">STATUS DE ESTOQUE (PROJEÇÃO)</h4>
            <div className="text-3xl font-bold tracking-tight text-white mb-2">{Math.round(porcentagemVendido)}%</div>
            <div className="w-full bg-[#222] rounded-full h-1.5 mb-1 overflow-hidden">
               <div className="bg-[#ff4d00] h-1.5 rounded-full" style={{ width: `${porcentagemVendido}%` }}></div>
            </div>
            <p className="text-[9px] text-[#777] uppercase tracking-widest font-bold text-right pt-1">ESGOTANDO</p>
         </div>
      </div>

      {/* MODAL DETALHES (CONDICOES) */}
      {condicoesModal && (
        <div className="fixed inset-0 bg-[#000000FA] backdrop-blur-md flex justify-end z-[400] animate-in slide-in-from-right-4 duration-300">
           <div className="w-full max-w-xl h-full bg-[#111] border-l border-[#333] flex flex-col shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
              <div className="p-6 border-b border-[#333] flex justify-between items-center bg-[#151515]">
                 <div>
                    <h3 className="text-lg font-black text-white uppercase tracking-widest">Detalhes do Contrato</h3>
                    <p className="text-[#ff4d00] text-[10px] font-bold uppercase tracking-[0.2em] mt-1">{condicoesModal.venda?.descricao}</p>
                 </div>
                 <button onClick={() => setCondicoesModal(null)} className="w-8 h-8 rounded-full bg-[#222] hover:bg-white hover:text-black flex items-center justify-center text-[#777] transition-colors">
                    <X size={16}/>
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                {condicoesModal.loading && (
                   <div className="flex flex-col items-center justify-center p-12 text-[#ff4d00]">
                      <Loader2 size={32} className="animate-spin mb-4" />
                      <span className="text-[10px] uppercase font-bold tracking-widest">Compilando Ledger...</span>
                   </div>
                )}
                {!condicoesModal.loading && condicoesModal.error && (
                   <div className="text-red-500 p-6 border border-red-500/20 bg-red-500/5 rounded text-sm">
                     {condicoesModal.error}
                   </div>
                )}
                {!condicoesModal.loading && condicoesModal.payload && (
                   <div className="space-y-8 animate-in fade-in">
                      {/* Resumo Caixa */}
                      <div className="bg-[#151515] p-5 rounded border border-[#222]">
                         <span className="text-[10px] text-[#777] uppercase tracking-widest font-bold mb-1 block">Valor Bruto Lançado</span>
                         <span className="text-2xl font-black text-[#ff4d00]">{formatCurrency(condicoesModal.payload.venda?.total || 0)}</span>
                         <div className="mt-4 flex flex-col gap-1">
                            <span className="text-xs text-white font-bold">{condicoesModal.payload.venda?.cliente?.nome || '-'}</span>
                            <span className="text-[10px] text-[#666] font-mono">{condicoesModal.payload.venda?.cliente?.cnpj || ''}</span>
                         </div>
                      </div>

                      {/* Quadro Negocial */}
                      <div>
                         <h4 className="border-b border-[#222] pb-2 text-[10px] uppercase text-[#777] tracking-[0.2em] font-black mb-4">Quadro Resumo de Pagamentos</h4>
                         <div className="flex flex-col gap-2">
                           {(condicoesModal.payload.formas_pagto || []).map(f => (
                              <div key={f.id} className="bg-[#151515] p-3 border border-[#222] rounded flex justify-between items-center text-xs">
                                 <span className="text-[#aaa] font-bold">{f.descricao} <span className="text-[#555] ml-2">x{f.quantidade_parcelas}</span></span>
                                 <span className="text-white font-mono font-black">{formatCurrency(f.valor || 0)}</span>
                              </div>
                           ))}
                           {(condicoesModal.payload.formas_pagto || []).length === 0 && (
                              <div className="text-[#555] text-xs">Sem condições atreladas ao VGV.</div>
                           )}
                         </div>
                      </div>

                      {/* Boletos/Parcelas Projetadas */}
                      <div>
                         <h4 className="border-b border-[#222] pb-2 text-[10px] uppercase text-[#777] tracking-[0.2em] font-black mb-4">Ledger Financeiro / Boletos</h4>
                         <div className="flex flex-col gap-[2px]">
                           {(condicoesModal.payload.parcelas || []).map(p => (
                              <div key={p.id} className="bg-[#151515] p-3 border border-[#222] flex justify-between items-center hover:border-[#ff4d00]/30 transition-colors">
                                 <div className="flex flex-col gap-1 w-24">
                                    <span className="text-[#555] text-[9px] font-bold uppercase tracking-widest">VENCIMENTO</span>
                                    <span className="text-[#ccc] text-xs font-mono">{p.data} <span className="text-[#444] text-[10px]">#{p.parcela}</span></span>
                                 </div>
                                 <div className="flex flex-col gap-1 flex-1 text-right">
                                    <span className="text-[#555] text-[9px] font-bold uppercase tracking-widest text-right">VALOR ORIGINAL</span>
                                    <span className="text-white text-xs font-mono font-bold">{formatCurrency(p.valor_parcela || 0)}</span>
                                 </div>
                                 <div className="flex flex-col gap-1 w-28 text-right">
                                    <span className="text-[#555] text-[9px] font-bold uppercase tracking-widest text-right">LIQUIDAÇÃO</span>
                                    {(p.total_pago || 0) > 0 ? (
                                       <span className="text-[#34C759] text-xs font-mono font-black">{formatCurrency(p.total_pago)}</span>
                                    ) : (
                                       <span className="text-[#ff4d00] text-xs font-mono font-bold">Em Aberto</span>
                                    )}
                                 </div>
                              </div>
                           ))}
                           {(condicoesModal.payload.parcelas || []).length === 0 && (
                              <div className="text-[#555] text-xs">O Vulcano ERP não gerou fluxo de caixa futuro.</div>
                           )}
                         </div>
                      </div>
                   </div>
                )}
              </div>
           </div>
        </div>
      )}

      {/* MODAL DISTRATO */}
      {distratoModal && (
        <div className="fixed inset-0 bg-[#000000FA] backdrop-blur-sm flex items-center justify-center z-[500] animate-in fade-in p-6">
           <div className="bg-[#111] max-w-[400px] w-full border border-red-500/30 rounded p-8 shadow-[0_0_50px_rgba(239,68,68,0.15)]">
              <h3 className="text-lg uppercase tracking-widest text-red-500 font-black mb-1">Averbação de Distrato</h3>
              <p className="text-[10px] text-[#555] font-bold uppercase tracking-widest mb-6">Quebra Contratual Irreversível</p>

              <div className="bg-[#181818] border border-red-500/10 p-4 rounded mb-6 text-left">
                 <span className="text-[10px] text-[#555] uppercase font-bold tracking-widest mb-1 block">ALVO DA RESCISÃO</span>
                 <span className="text-white font-bold text-sm block truncate mb-1">{distratoModal.descricao}</span>
                 <span className="text-[10px] text-[#ff4d00] font-mono tracking-wider">{distratoModal.cliente_nome}</span>
              </div>

              <form className="flex flex-col gap-4 text-left" onSubmit={async (e) => {
                 e.preventDefault();
                 const fd = new FormData(e.target);
                 fd.append('id_venda', distratoModal.id);
                 try {
                   await fetch(`${API_BASE}/api/distratos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
                   alert("Rescisão contratual averbada no ERP."); 
                   setDistratoModal(null);
                   fetchVendas();
                 } catch (err) { alert("Falha na rede ou API Vulcano."); }
              }}>
                 <div>
                    <label className="text-[10px] text-[#777] uppercase font-bold tracking-widest mb-2 block">Data Formal do Distrato</label>
                    <input name="data_distrato" type="date" required className="w-full bg-[#181818] text-[#ccc] border border-white/10 rounded p-3 text-xs focus:outline-none focus:border-red-500/50" />
                 </div>
                 <div>
                    <label className="text-[10px] text-[#777] uppercase font-bold tracking-widest mb-2 block">Montante Devolvido / Multa (R$)</label>
                    <input name="valor_devolvido" type="number" step="0.01" required className="w-full bg-[#181818] text-[#ccc] border border-white/10 rounded p-3 text-xs focus:outline-none focus:border-red-500/50 text-right font-mono" placeholder="0.00" />
                 </div>
                 <div>
                    <label className="text-[10px] text-[#777] uppercase font-bold tracking-widest mb-2 block">Previsão Acordo/Estorno</label>
                    <input name="data_pagamento" type="date" required className="w-full bg-[#181818] text-[#ccc] border border-white/10 rounded p-3 text-xs focus:outline-none focus:border-red-500/50" />
                 </div>

                 <div className="flex justify-end gap-3 mt-8">
                    <button type="button" onClick={() => setDistratoModal(null)} className="text-[#888] hover:text-white text-[10px] font-bold uppercase tracking-widest px-4 py-3 transition-colors">Abortar</button>
                    <button type="submit" className="bg-red-500 text-white text-[10px] font-bold uppercase tracking-widest px-6 py-3 rounded hover:bg-red-600 transition-colors shadow-[0_0_15px_rgba(239,68,68,0.4)]">Executar Rescisão</button>
                 </div>
              </form>
           </div>
        </div>
      )}
    </div>
  );
};
"""

new_code = code[:start_idx] + new_component + code[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_code)

print("VendasView successfully replaced.")
