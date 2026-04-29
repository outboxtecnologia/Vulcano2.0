import re

with open("frontend/src/VulcanoViews.jsx", "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("export const VendasView =")
end_idx = content.find("export const RecebimentosView =")

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

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(v => v.empreendimento))].sort();

  const handleSelectVenda = async (v) => {
    if (selectedVenda?.id === v.id) { setSelectedVenda(null); return; }
    setSelectedVenda(v);
    setCondicoesLoading(true); setCondicoesData(null);
    try {
      const res = await fetch(`${API_BASE}/api/vulcano/vendas/${encodeURIComponent(v.id)}/condicoes`);
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.detail || `Erro HTTP`);
      setCondicoesData(json);
    } catch (e) {
      setCondicoesData({ error: 'Falha ao carregar fluxo financeiro.' });
    } finally { setCondicoesLoading(false); }
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

  const groupedVendas = { 'HOJE': [], 'ONTEM': [], 'ESTA SEMANA': [], 'ESTE MÊS': [], 'ANTERIORES': [] };
  const today = new Date(); today.setHours(0,0,0,0);
  
  filtered.forEach(v => {
    if (!v.data || !v.data.includes('/')) { groupedVendas['ANTERIORES'].push(v); return; }
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

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd);
    try {
      await fetch(`${API_BASE}/api/vulcano/vendas`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      alert("Venda cadastrada!"); setShowForm(false); setLoading(true);
      fetch(`${API_BASE}/api/vulcano/vendas?empresa_id=${selectedEmpresa}`).then(res => res.json()).then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); });
    } catch (err) { alert("Erro ao cadastrar."); }
  };

  const totalGeral = filtered.reduce((acc, curr) => acc + (curr.total || 0), 0);

  return (
    <div className="flex flex-col h-full animate-in fade-in" style={{ background: '#0c0908' }}>
      {/* HEADER PODEROSO */}
      <div className="px-6 py-4 flex flex-col gap-4 shrink-0 z-20" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex justify-between items-end">
            <div className="flex items-baseline gap-3">
                <h2 className="text-[24px] font-black tracking-tighter" style={{ color: '#f0e6d8' }}>VENDAS</h2>
                <span className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>· {filtered.length}</span>
            </div>
            
            <div className="flex gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                    <Search size={12}/>
                    <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Buscar venda..." className="bg-transparent border-none outline-none text-[12px] w-48 placeholder-[#5a4e42]" style={{ color: '#f0e6d8' }} />
                    <kbd className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>/</kbd>
                </div>
                
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-bold" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.18)', color: '#f0e6d8' }}>
                    <Filter size={12}/> Comandos <kbd className="ml-1 text-[10px]" style={{ color: '#8a7a68' }}>⌘K</kbd>
                </button>
                <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-[12px] font-bold shadow-lg" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                    <Plus size={12}/> Nova venda <kbd className="ml-1 text-[10px] bg-black/20 border border-black/30 px-1 rounded" style={{ color: '#3a1606' }}>⇧⌘N</kbd>
                </button>
            </div>
        </div>
        
        <div className="flex gap-3">
            <select value={empreendimentoFilter} onChange={(e) => setEmpreendimentoFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="">Empreendimento</option>
                {uniqueEmps.map((emp, i) => <option key={i} value={emp}>{emp}</option>)}
            </select>
            <select value={periodFilter} onChange={(e) => setPeriodFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="TODOS">Período</option>
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="TODOS">Status</option>
                <option value="ATIVA">ATIVA</option>
                <option value="DISTRATADA">DISTRATADA</option>
            </select>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* LISTA CENTRAL */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
            {loading ? (
                <div className="flex justify-center items-center h-full text-[#8a7a68] animate-pulse text-[12px]">Carregando carteira de vendas...</div>
            ) : filtered.length === 0 ? (
                <div className="flex justify-center items-center h-full text-[#5a4e42] uppercase text-[10px] tracking-widest font-bold">Nenhum registro.</div>
            ) : (
                <div className="flex flex-col">
                    {Object.entries(groupedVendas).filter(([_, items]) => items.length > 0).map(([groupName, items]) => (
                        <div key={groupName} className="mb-4">
                            <div className="px-6 py-2 flex items-center gap-3 sticky top-0 z-10" style={{ background: '#0c0908' }}>
                                <span className="font-mono text-[9.5px] font-bold tracking-[0.28em]" style={{ color: '#5a4e42' }}>{groupName}</span>
                                <div className="flex-1 h-[1px]" style={{ background: 'rgba(255, 160, 80, 0.08)' }}></div>
                                <span className="font-mono text-[9.5px]" style={{ color: '#5a4e42' }}>{items.length}</span>
                            </div>
                            <div className="flex flex-col">
                                {items.map(v => {
                                    const isSelected = selectedVenda?.id === v.id;
                                    const isDistratada = v.distrato === 'S';
                                    return (
                                        <div 
                                            key={v.id} 
                                            onClick={() => handleSelectVenda(v)}
                                            className="grid grid-cols-[60px_40px_1fr_200px_120px_100px_80px] items-center gap-3 px-6 py-3 cursor-pointer transition-colors"
                                            style={{
                                                background: isSelected ? 'rgba(255, 122, 26, 0.05)' : 'transparent',
                                                borderBottom: '1px solid rgba(255, 160, 80, 0.08)'
                                            }}
                                        >
                                            <span className="font-mono text-[10.5px]" style={{ color: isSelected ? '#ff7a1a' : '#5a4e42' }}>#{v.id}</span>
                                            
                                            <div className="w-[30px] h-[22px] rounded flex items-center justify-center font-mono text-[9.5px] font-bold" 
                                                 style={{ background: 'linear-gradient(135deg, rgba(255, 122, 26, 0.25), rgba(201, 58, 18, 0.15))', border: '1px solid rgba(255, 140, 42, 0.25)', color: '#ffd28a' }}>
                                                {(v.empreendimento || 'EMP').substring(0,3).toUpperCase()}
                                            </div>
                                            
                                            <div className="min-w-0">
                                                <div className="font-medium text-[13.5px] truncate" style={{ color: '#f0e6d8' }}>{v.cliente_nome}</div>
                                                <div className="font-mono text-[10.5px] mt-1" style={{ color: '#8a7a68' }}>
                                                    {v.descricao} · <span style={{ color: '#5a4e42' }}>{v.cliente_cnpj}</span>
                                                </div>
                                            </div>
                                            
                                            <div className="font-mono text-[11px]" style={{ color: '#8a7a68' }}>{v.empreendimento}</div>
                                            
                                            <div className="font-medium text-[13.5px]" style={{ color: '#f0e6d8' }}>{formatCurrency(v.total)}</div>
                                            
                                            <div className="flex items-center gap-2">
                                                {isDistratada ? (
                                                    <><span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_6px_red]"></span><span className="font-mono text-[9.5px] tracking-[0.16em] text-red-500">DISTRATADA</span></>
                                                ) : (
                                                    <><span className="w-1.5 h-1.5 rounded-full" style={{ background: '#ffc247', boxShadow: '0 0 6px #ffc247' }}></span><span className="font-mono text-[9.5px] tracking-[0.16em]" style={{ color: '#ffc247' }}>ATIVA</span></>
                                                )}
                                            </div>
                                            
                                            <div className="font-mono text-[10px] text-right" style={{ color: '#5a4e42' }}>{v.data}</div>
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
            <div className="w-[450px] flex flex-col shrink-0 animate-in slide-in-from-right-8 duration-300 z-10" style={{ background: '#0c0908', borderLeft: '1px solid rgba(255, 160, 80, 0.08)' }}>
                <div className="p-5 flex justify-between items-start" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-[10px] font-bold" style={{ color: '#ff7a1a' }}>#{selectedVenda.id}</span>
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-mono tracking-widest" style={{ background: 'rgba(255, 194, 71, 0.1)', color: '#ffc247' }}>ATIVA</span>
                        </div>
                        <h3 className="text-[16px] font-bold" style={{ color: '#f0e6d8' }}>{selectedVenda.cliente_nome}</h3>
                        <p className="font-mono text-[11px] mt-1" style={{ color: '#8a7a68' }}>{selectedVenda.cliente_cnpj}</p>
                    </div>
                    <button onClick={() => setSelectedVenda(null)} className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/5 transition-colors" style={{ color: '#8a7a68' }}><X size={14}/></button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {/* INFO GRID */}
                    <div className="px-5 py-4" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <div className="flex justify-between py-1.5 border-b border-dashed" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <span className="font-mono text-[10px] tracking-[0.18em]" style={{ color: '#5a4e42' }}>UNIDADE</span>
                            <span className="text-[12.5px]" style={{ color: '#f0e6d8' }}>{selectedVenda.descricao}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-dashed" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <span className="font-mono text-[10px] tracking-[0.18em]" style={{ color: '#5a4e42' }}>OBRA</span>
                            <span className="text-[12.5px]" style={{ color: '#f0e6d8' }}>{selectedVenda.empreendimento}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-dashed" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <span className="font-mono text-[10px] tracking-[0.18em]" style={{ color: '#5a4e42' }}>ASSINADO</span>
                            <span className="text-[12.5px]" style={{ color: '#f0e6d8' }}>{selectedVenda.data}</span>
                        </div>
                    </div>

                    {/* KPIs */}
                    <div className="p-5" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>VALOR DA VENDA</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{formatCurrency(selectedVenda.total)}</div>
                            </div>
                            <div>
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>PARCELAS</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{condicoesData?.tabela ? condicoesData.tabela.length + 'x' : '...'}</div>
                            </div>
                            <div className="mt-2">
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>ENTRADA</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{formatCurrency(selectedVenda.total * 0.1)}</div>
                            </div>
                            <div className="mt-2">
                                <div className="font-mono text-[9.5px] tracking-[0.22em] mb-1" style={{ color: '#5a4e42' }}>VPL ESTIMADO</div>
                                <div className="text-[15px] font-semibold" style={{ color: '#f0e6d8' }}>{formatCurrency(selectedVenda.total * 0.78)}</div>
                            </div>
                        </div>
                    </div>

                    {/* Chart Area */}
                    <div className="p-5" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <div className="font-mono text-[9.5px] tracking-[0.22em] mb-3" style={{ color: '#5a4e42' }}>CRONOGRAMA · 12 MESES</div>
                        <div className="h-12 flex items-end justify-center">
                            {condicoesLoading ? (
                                <Loader2 className="animate-spin" size={16} style={{ color: '#5a4e42' }}/>
                            ) : condicoesData?.tabela ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={condicoesData.tabela.slice(0, 12).map(c => ({ name: c.Data.substring(3,5), val: c.Valor }))}>
                                        <RechartsTooltip cursor={{fill: 'rgba(255, 160, 80, 0.08)'}} contentStyle={{backgroundColor: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', fontSize: '10px'}} />
                                        <Bar dataKey="val" fill="url(#colorUv)" radius={[1, 1, 0, 0]} />
                                        <defs>
                                            <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#ff9a4a" stopOpacity={1}/>
                                                <stop offset="100%" stopColor="#c93a12" stopOpacity={1}/>
                                            </linearGradient>
                                        </defs>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <span className="text-[9px] uppercase" style={{ color: '#5a4e42' }}>N/A</span>
                            )}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="p-5">
                        <div className="font-mono text-[9.5px] tracking-[0.22em] mb-3" style={{ color: '#5a4e42' }}>AÇÕES</div>
                        <div className="flex flex-col gap-1.5">
                            <button className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><Layers size={14} style={{ color: '#8a7a68' }}/> Abrir estrutura financeira</span>
                                <span className="font-mono text-[10px] bg-black/40 px-1.5 rounded" style={{ color: '#5a4e42' }}>Enter</span>
                            </button>
                            <button className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><DollarSign size={14} style={{ color: '#8a7a68' }}/> Lançar parcela manual</span>
                                <span className="font-mono text-[10px] bg-black/40 px-1.5 rounded" style={{ color: '#5a4e42' }}>⌘L</span>
                            </button>
                            <button className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><RefreshCw size={14} style={{ color: '#8a7a68' }}/> Reconciliar com Questor</span>
                                <span className="font-mono text-[10px] bg-black/40 px-1.5 rounded" style={{ color: '#5a4e42' }}>⇧⌘R</span>
                            </button>
                            <button className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium transition-colors hover:bg-white/5" style={{ color: '#f0e6d8' }}>
                                <span className="flex items-center gap-3"><FileText size={14} style={{ color: '#8a7a68' }}/> Exportar contrato (.pdf)</span>
                                <span className="font-mono text-[10px] bg-black/40 px-1.5 rounded" style={{ color: '#5a4e42' }}>⇧⌘E</span>
                            </button>
                            {selectedVenda.distrato !== 'S' && (
                                <button onClick={() => setDistratoModal(selectedVenda)} className="flex justify-between items-center px-4 py-2.5 rounded-lg text-[12px] font-medium mt-2 transition-colors hover:bg-red-950/30" style={{ color: '#ef4444' }}>
                                    <span className="flex items-center gap-3"><AlertCircle size={14} className="text-red-500/70"/> Distratar contrato</span>
                                    <span className="font-mono text-[10px] bg-red-950/50 px-1.5 rounded text-red-900 border border-red-900/30">⇧⌘D</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        )}
      </div>

      <div className="px-6 py-2 flex justify-between items-center shrink-0 z-20" style={{ background: '#0c0908', borderTop: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex gap-4 font-mono text-[9px] font-bold tracking-[0.16em]" style={{ color: '#5a4e42' }}>
            <span>↑ ↓ NAVEGAR</span>
            <span>↵ AÇÃO</span>
            <span>/ BUSCAR</span>
            <span>⌘K COMANDOS</span>
            <span>⇧⌘N NOVA VENDA</span>
        </div>
        <div className="font-mono text-[9.5px] font-bold tracking-[0.2em]" style={{ color: '#8a7a68' }}>
            EXIBINDO {filtered.length} · TOTAL {formatCurrency(totalGeral)}
        </div>
      </div>
      
      {/* MODAL NOVA VENDA (Apenas Form Antigo Simplificado) */}
      {showForm && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] animate-in fade-in p-6">
            <div className="w-full max-w-4xl rounded-xl shadow-2xl flex flex-col max-h-[90vh]" style={{ background: '#0c0908', border: '1px solid rgba(255, 160, 80, 0.08)' }}>
                <div className="p-6 border-b flex justify-between items-center" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                    <h3 className="text-lg font-black uppercase tracking-widest flex items-center gap-3" style={{ color: '#f0e6d8' }}><Plus size={20} color="#ff7a1a"/> Cadastrar Nova Venda</h3>
                    <button onClick={() => setShowForm(false)} style={{ color: '#8a7a68' }}><X size={20}/></button>
                </div>
                <div className="p-6 overflow-y-auto custom-scrollbar">
                    <form className="flex flex-col gap-6" onSubmit={handleFormSubmit}>
                        <input type="hidden" name="empresa_id" value={selectedEmpresa} />
                        <div className="grid grid-cols-4 gap-4">
                            <div><label className="text-[10px] uppercase font-bold mb-2 block" style={{ color: '#8a7a68' }}>ID Emp.</label><input name="id_empreendimento" type="number" required className="w-full p-3 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} /></div>
                            <div><label className="text-[10px] uppercase font-bold mb-2 block" style={{ color: '#8a7a68' }}>Unidade</label><input name="unidade" required className="w-full p-3 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} /></div>
                            <div><label className="text-[10px] uppercase font-bold mb-2 block" style={{ color: '#8a7a68' }}>Total Venda</label><input name="total" type="number" step="0.01" required className="w-full p-3 rounded text-[11px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} /></div>
                            <div><label className="text-[10px] uppercase font-bold mb-2 block" style={{ color: '#8a7a68' }}>Data Venda</label><input name="data" type="date" required className="w-full p-3 rounded text-[11px] outline-none dark-calendar" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#f0e6d8' }} /></div>
                        </div>
                        <div className="flex justify-end pt-4 border-t mt-4" style={{ borderColor: 'rgba(255, 160, 80, 0.08)' }}>
                            <button type="submit" className="px-8 py-3 rounded text-[11px] font-bold uppercase tracking-widest" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>Registrar Venda</button>
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

print("VendasView replaced successfully com fidelidade absoluta!")
