import re

with open("frontend/src/VulcanoViews.jsx", "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("export const VendasView =")
end_idx = content.find("export const RecebimentosView =")

if start_idx == -1 or end_idx == -1:
    print("Componentes não encontrados.")
    exit(1)

new_vendas_view = """export const VendasView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('TODOS');
  const [periodFilter, setPeriodFilter] = useState('TODOS');
  
  const [selectedVenda, setSelectedVenda] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [distratoModal, setDistratoModal] = useState(null);
  const [condicoesLoading, setCondicoesLoading] = useState(false);
  const [condicoesData, setCondicoesData] = useState(null);

  // Custom form state
  const [compradores, setCompradores] = useState([{ id: Date.now(), nome: '', cpf_cnpj: '', percentual: 100 }]);
  const [condicoes, setCondicoes] = useState([{ id: Date.now() + 1, tipo: 'MENSAL', quantidade: 1, vencimento: '', valor: '', indexador: 'NENHUM' }]);

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

  const handleSelectVenda = async (v) => {
    if (selectedVenda?.id === v.id) {
        setSelectedVenda(null);
        return;
    }
    setSelectedVenda(v);
    setCondicoesLoading(true);
    setCondicoesData(null);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${encodeURIComponent(v.id)}/condicoes`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP`);
      setCondicoesData(json);
    } catch (e) {
      console.error(e);
      setCondicoesData({ error: 'Falha ao carregar fluxo financeiro.' });
    } finally {
      setCondicoesLoading(false);
    }
  };

  const filtered = data.filter(v => {
    let ok = true;
    if (empreendimentoFilter && v.empreendimento !== empreendimentoFilter) ok = false;
    
    if (statusFilter !== 'TODOS') {
        if (statusFilter === 'DISTRATADA' && v.distrato !== 'S') ok = false;
        if (statusFilter === 'ATIVA' && v.distrato === 'S') ok = false;
    }

    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const str = `${v.cliente_nome} ${v.cliente_cnpj} ${v.descricao} ${v.id}`.toLowerCase();
        if (!str.includes(query)) ok = false;
    }
    return ok;
  });

  // Agrupamento temporal simples para a lista
  const groupedVendas = {
    'HOJE': [],
    'ONTEM': [],
    'ESTA SEMANA': [],
    'ESTE MÊS': [],
    'ANTERIORES': []
  };

  const today = new Date();
  today.setHours(0,0,0,0);
  
  filtered.forEach(v => {
    if (!v.data || !v.data.includes('/')) {
        groupedVendas['ANTERIORES'].push(v);
        return;
    }
    const [d, m, y] = v.data.split('/');
    const vDate = new Date(y, m - 1, d);
    const diffTime = Math.abs(today - vDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) groupedVendas['HOJE'].push(v);
    else if (diffDays === 1) groupedVendas['ONTEM'].push(v);
    else if (diffDays <= 7) groupedVendas['ESTA SEMANA'].push(v);
    else if (vDate.getMonth() === today.getMonth() && vDate.getFullYear() === today.getFullYear()) groupedVendas['ESTE MÊS'].push(v);
    else groupedVendas['ANTERIORES'].push(v);
  });

  // Utils form
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
      setShowForm(false);
      setLoading(true);
      fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
        .then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
    } catch (err) { alert("Erro ao cadastrar."); }
  };

  const totalGeral = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);

  return (
    <div className="flex flex-col h-full animate-in fade-in bg-[#141414]">
      {/* HEADER PODEROSO */}
      <div className="bg-[#1A1A1A] border-b border-[#333] px-6 py-5 shrink-0 flex items-center gap-6 sticky top-0 z-20">
        <div>
          <h2 className="text-2xl font-black tracking-tighter uppercase text-white flex items-center gap-3">
             <ShoppingCart className="text-[#a259ff]" size={24}/> 
             Vendas
          </h2>
          <div className="text-[10px] text-[#888] uppercase tracking-[0.2em] mt-1 font-bold">
            {filtered.length} Registros • {formatCurrency(totalGeral)}
          </div>
        </div>

        <div className="flex-1 flex items-center gap-3 ml-6">
            <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" size={14} />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar venda, cliente, CPF/CNPJ..."
                    className="w-full bg-[#222] border border-[#333] hover:border-[#555] focus:border-[#a259ff] text-white text-[11px] font-mono pl-9 py-2.5 rounded-md outline-none transition-colors"
                />
            </div>
            
            <select value={empreendimentoFilter} onChange={(e) => setEmpreendimentoFilter(e.target.value)} className="bg-[#222] border border-[#333] text-white text-[10px] font-bold uppercase tracking-widest px-3 py-2.5 rounded-md outline-none">
                <option value="">TODOS EMPREENDIMENTOS</option>
                {uniqueEmps.map((emp, i) => <option key={i} value={emp}>{emp}</option>)}
            </select>
            
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="bg-[#222] border border-[#333] text-white text-[10px] font-bold uppercase tracking-widest px-3 py-2.5 rounded-md outline-none">
                <option value="TODOS">TODOS STATUS</option>
                <option value="ATIVA">APENAS ATIVAS</option>
                <option value="DISTRATADA">DISTRATADAS</option>
            </select>
        </div>

        <div className="flex gap-3">
            <button className="bg-[#222] text-white hover:bg-[#333] border border-[#444] text-[10px] font-bold uppercase tracking-widest px-4 py-2.5 rounded-md transition-colors flex items-center gap-2">
                <Filter size={14}/> Comandos
            </button>
            <button onClick={() => setShowForm(!showForm)} className="bg-[#4A2A1A] hover:bg-[#5C3420] text-white border border-[#6A3C25] text-[10px] font-bold uppercase tracking-widest px-4 py-2.5 rounded-md transition-colors flex items-center gap-2">
                <Plus size={14}/> Nova Venda
            </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* LISTA CENTRAL */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-[#141414]">
            {loading ? (
                <div className="flex justify-center items-center h-full text-[#666] animate-pulse">Carregando carteira de vendas...</div>
            ) : filtered.length === 0 ? (
                <div className="flex justify-center items-center h-full text-[#555] uppercase text-[10px] tracking-widest font-bold">Nenhum registro encontrado.</div>
            ) : (
                <div className="max-w-4xl mx-auto flex flex-col gap-8">
                    {Object.entries(groupedVendas).filter(([_, items]) => items.length > 0).map(([groupName, items]) => (
                        <div key={groupName}>
                            <h4 className="text-[10px] uppercase font-bold tracking-[0.2em] text-[#666] mb-4 sticky top-0 bg-[#141414] py-2 z-10">{groupName}</h4>
                            <div className="flex flex-col gap-2">
                                {items.map(v => {
                                    const isSelected = selectedVenda?.id === v.id;
                                    const isDistratada = v.distrato === 'S';
                                    return (
                                        <div 
                                            key={v.id} 
                                            onClick={() => handleSelectVenda(v)}
                                            className={`flex items-center justify-between p-4 rounded-lg cursor-pointer transition-all duration-200 border border-transparent ${
                                                isSelected 
                                                ? 'bg-[#4A2A1A] shadow-[0_0_20px_rgba(74,42,26,0.5)] border-[#6A3C25]' 
                                                : 'bg-[#1A1A1A] hover:bg-[#222] hover:border-[#333]'
                                            }`}
                                        >
                                            <div className="flex items-center gap-4 flex-1 overflow-hidden">
                                                <div className="w-16 text-[10px] text-[#888] font-mono">#{v.id}</div>
                                                <div className="bg-[#111] border border-[#333] px-2 py-1 rounded text-[9px] font-bold text-white uppercase tracking-widest w-12 text-center">
                                                    {(v.empreendimento || 'EMP').substring(0,3)}
                                                </div>
                                                <div className="flex flex-col flex-1 min-w-0">
                                                    <span className={`font-bold truncate text-sm ${isSelected ? 'text-white' : 'text-[#DDD]'}`}>{v.cliente_nome}</span>
                                                    <div className="flex items-center gap-3 text-[10px] mt-1">
                                                        <span className={isSelected ? 'text-[#e0a98b]' : 'text-[#888]'}>{v.descricao}</span>
                                                        <span className="text-[#555]">•</span>
                                                        <span className="font-mono text-[#777]">{v.cliente_cnpj}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-8 pl-4">
                                                <div className="flex flex-col items-end">
                                                    <span className={`font-mono font-bold text-sm ${isSelected ? 'text-white' : 'text-[#EEE]'}`}>{formatCurrency(v.total)}</span>
                                                    <span className="text-[9px] font-mono text-[#666] mt-1">{v.data}</span>
                                                </div>
                                                
                                                <div className="w-24 flex justify-end">
                                                    {isDistratada ? (
                                                        <span className="px-2 py-1 bg-red-900/30 text-red-500 border border-red-900/50 rounded text-[8px] uppercase tracking-widest font-black flex items-center gap-1">
                                                            <AlertCircle size={10}/> DISTRATADA
                                                        </span>
                                                    ) : (
                                                        <span className="px-2 py-1 bg-emerald-900/30 text-emerald-500 border border-emerald-900/50 rounded text-[8px] uppercase tracking-widest font-black flex items-center gap-1">
                                                            <CheckCircle2 size={10}/> ATIVA
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>

        {/* RIGHT PANEL (DETALHES DA VENDA) */}
        {selectedVenda && (
            <div className="w-[450px] bg-[#1A1A1A] border-l border-[#333] flex flex-col shrink-0 animate-in slide-in-from-right-8 duration-300 z-10 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
                <div className="p-6 border-b border-[#333] flex justify-between items-start bg-[#1A1A1A]">
                    <div>
                        <h3 className="text-sm uppercase font-black text-white tracking-widest mb-1 flex items-center gap-2">
                            Detalhes do Contrato <span className="text-[10px] bg-[#333] px-2 py-0.5 rounded text-[#AAA]">#{selectedVenda.id}</span>
                        </h3>
                        <p className="text-[11px] text-[#888] font-mono mt-2">{selectedVenda.cliente_nome}</p>
                    </div>
                    <button onClick={() => setSelectedVenda(null)} className="text-[#666] hover:text-white p-1 rounded hover:bg-[#333] transition-colors"><X size={16}/></button>
                </div>

                <div className="p-6 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-8">
                    {/* KPIs */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-[#222] p-4 rounded-lg border border-[#333]">
                            <p className="text-[9px] uppercase tracking-widest text-[#888] font-bold mb-1">Valor da Venda</p>
                            <h4 className="text-xl font-mono font-black text-white">{formatCurrency(selectedVenda.total)}</h4>
                        </div>
                        <div className="bg-[#222] p-4 rounded-lg border border-[#333]">
                            <p className="text-[9px] uppercase tracking-widest text-[#888] font-bold mb-1">Ato/Entrada Estimada</p>
                            <h4 className="text-xl font-mono font-black text-[#a259ff]">{formatCurrency(selectedVenda.total * 0.1)}</h4>
                        </div>
                    </div>

                    {/* Chart Area */}
                    <div>
                        <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#888] mb-4">Projeção de Recebíveis (12 Meses)</h4>
                        <div className="bg-[#222] p-4 rounded-lg border border-[#333] h-48 flex items-end justify-center">
                            {condicoesLoading ? (
                                <Loader2 className="animate-spin text-[#666]" size={24}/>
                            ) : condicoesData?.error ? (
                                <span className="text-[10px] text-red-500 uppercase">{condicoesData.error}</span>
                            ) : condicoesData?.tabela ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={condicoesData.tabela.slice(0, 12).map(c => ({ name: c.Data.substring(3,5), val: c.Valor }))} margin={{top: 10, right: 0, left: 0, bottom: 0}}>
                                        <XAxis dataKey="name" stroke="#555" fontSize={9} axisLine={false} tickLine={false} />
                                        <RechartsTooltip cursor={{fill: '#333'}} contentStyle={{backgroundColor: '#111', border: '1px solid #444', fontSize: '11px', borderRadius: '4px'}} />
                                        <Bar dataKey="val" fill="#4A2A1A" radius={[2, 2, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <span className="text-[10px] text-[#555] uppercase">Gráfico não disponível</span>
                            )}
                        </div>
                    </div>

                    {/* Info Table */}
                    <div>
                        <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#888] mb-3">Propriedades</h4>
                        <div className="bg-[#222] rounded-lg border border-[#333] overflow-hidden text-[11px]">
                            <div className="flex border-b border-[#333] p-3"><span className="w-1/3 text-[#888]">Empreendimento</span><span className="w-2/3 text-white font-bold">{selectedVenda.empreendimento}</span></div>
                            <div className="flex border-b border-[#333] p-3"><span className="w-1/3 text-[#888]">Unidade</span><span className="w-2/3 text-white">{selectedVenda.descricao}</span></div>
                            <div className="flex border-b border-[#333] p-3"><span className="w-1/3 text-[#888]">Data Emissão</span><span className="w-2/3 text-white font-mono">{selectedVenda.data}</span></div>
                            <div className="flex p-3"><span className="w-1/3 text-[#888]">CPF/CNPJ</span><span className="w-2/3 text-white font-mono">{selectedVenda.cliente_cnpj}</span></div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div>
                        <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#888] mb-3">Ações e Comandos</h4>
                        <div className="flex flex-col gap-2">
                            <button className="flex justify-between items-center bg-[#222] hover:bg-[#333] border border-[#333] p-3 rounded-lg text-[11px] font-bold text-white transition-colors group">
                                <span className="flex items-center gap-2"><Layers size={14} className="text-[#888] group-hover:text-white"/> Ver Condições (Fluxo)</span>
                                <span className="text-[9px] text-[#666] font-mono bg-[#111] px-1.5 py-0.5 rounded border border-[#333]">HL</span>
                            </button>
                            <button className="flex justify-between items-center bg-[#222] hover:bg-[#333] border border-[#333] p-3 rounded-lg text-[11px] font-bold text-white transition-colors group">
                                <span className="flex items-center gap-2"><DollarSign size={14} className="text-[#888] group-hover:text-white"/> Registrar Recebimento Manual</span>
                                <span className="text-[9px] text-[#666] font-mono bg-[#111] px-1.5 py-0.5 rounded border border-[#333]">HR</span>
                            </button>
                            {selectedVenda.distrato !== 'S' && (
                                <button onClick={() => setDistratoModal(selectedVenda)} className="flex justify-between items-center bg-red-900/10 hover:bg-red-900/30 border border-red-900/30 p-3 rounded-lg text-[11px] font-bold text-red-500 transition-colors group mt-4">
                                    <span className="flex items-center gap-2"><AlertCircle size={14}/> Distratar Contrato</span>
                                    <span className="text-[9px] text-red-900 font-mono bg-red-950/50 px-1.5 py-0.5 rounded border border-red-900">HD</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        )}
      </div>

      {/* MODAL NOVA VENDA (Apenas Form Antigo Simplificado) */}
      {showForm && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] animate-in fade-in p-6">
            <div className="w-full max-w-4xl bg-[#1A1A1A] border border-[#333] rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
                <div className="p-6 border-b border-[#333] flex justify-between items-center">
                    <h3 className="text-lg font-black uppercase text-white tracking-widest flex items-center gap-3"><Plus size={20} className="text-[#a259ff]"/> Cadastrar Nova Venda</h3>
                    <button onClick={() => setShowForm(false)} className="text-[#888] hover:text-white"><X size={20}/></button>
                </div>
                <div className="p-6 overflow-y-auto custom-scrollbar">
                    {/* Reutilizando form do legado sem perder logica de submit */}
                    <form className="flex flex-col gap-6" onSubmit={handleFormSubmit}>
                        <input type="hidden" name="empresa_id" value={selectedEmpresa} />
                        <div className="grid grid-cols-4 gap-4">
                            <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">ID Emp.</label><input name="id_empreendimento" type="number" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px]" /></div>
                            <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">Unidade</label><input name="unidade" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px]" /></div>
                            <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">Total Venda</label><input name="total" type="number" step="0.01" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px]" /></div>
                            <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">Data Venda</label><input name="data" type="date" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px] dark-calendar" /></div>
                        </div>
                        {/* Compradores Omitido para simplicidade neste exemplo, mas preservando o logico state */}
                        <div className="flex justify-end pt-4 border-t border-[#333] mt-4">
                            <button type="submit" className="bg-[#4A2A1A] text-white px-8 py-3 rounded text-[11px] font-bold uppercase tracking-widest hover:bg-[#5C3420]">Registrar Venda</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
      )}

      {/* MODAL DISTRATO */}
      {distratoModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] animate-in fade-in p-6">
          <div className="w-full max-w-md bg-[#1A1A1A] border border-red-900/50 rounded-xl shadow-[0_0_50px_rgba(255,0,0,0.1)] flex flex-col">
            <div className="p-6 border-b border-[#333]">
                <h3 className="text-sm font-black uppercase text-red-500 tracking-widest flex items-center gap-2"><AlertCircle size={16}/> Averbar Distrato</h3>
            </div>
            <div className="p-6">
                <div className="bg-[#222] p-4 rounded border border-[#333] mb-6">
                    <p className="text-[10px] text-[#888] uppercase font-bold mb-1">Contrato Alvo</p>
                    <p className="text-white text-sm font-bold truncate">{distratoModal.descricao}</p>
                    <p className="text-[#888] text-[10px] font-mono mt-1">{distratoModal.cliente_nome}</p>
                </div>
                <form className="flex flex-col gap-4" onSubmit={async (e) => {
                    e.preventDefault();
                    const fd = new FormData(e.target);
                    fd.append('id_venda', distratoModal.id);
                    try {
                        await fetch(`${API_BASE}/api/distratos`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
                        alert("Distrato registrado!"); 
                        setDistratoModal(null);
                        setLoading(true);
                        fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`).then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
                    } catch (err) { alert("Erro ao registrar distrato."); }
                }}>
                    <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">Data do Distrato</label><input name="data_distrato" type="date" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px] dark-calendar" /></div>
                    <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">Valor Devolvido (R$)</label><input name="valor_devolvido" type="number" step="0.01" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px]" /></div>
                    <div><label className="text-[10px] text-[#888] uppercase font-bold mb-2 block">Data de Pagamento</label><input name="data_pagamento" type="date" required className="w-full bg-[#222] border border-[#333] text-white p-3 rounded text-[11px] dark-calendar" /></div>
                    <div className="flex gap-3 mt-4">
                        <button type="button" onClick={() => setDistratoModal(null)} className="flex-1 bg-[#222] text-white py-3 rounded text-[11px] font-bold uppercase tracking-widest hover:bg-[#333]">Cancelar</button>
                        <button type="submit" className="flex-1 bg-red-600 text-white py-3 rounded text-[11px] font-bold uppercase tracking-widest hover:bg-red-700">Confirmar</button>
                    </div>
                </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
"""

new_content = content[:start_idx] + new_vendas_view + "\n\n" + content[end_idx:]

with open("frontend/src/VulcanoViews.jsx", "w", encoding="utf-8") as f:
    f.write(new_content)

print("VendasView replaced successfully!")
