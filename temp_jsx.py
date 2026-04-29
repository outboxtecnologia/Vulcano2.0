import sys

with open('frontend/src/VulcanoViews.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('export const RecebimentosView = ({ selectedEmpresa }) => {')
end_idx = content.find('export const ConciliadorView =', start_idx)

new_func = """export const RecebimentosView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('ABERTA');
  const [dataIniFilter, setDataIniFilter] = useState('');
  const [dataFimFilter, setDataFimFilter] = useState('');
  
  const [selectedRecebimento, setSelectedRecebimento] = useState(null);
  
  const [baixaForm, setBaixaForm] = useState({ valor_pago: '', data_pagamento: '', acrescimos: '', descontos: '' });

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => { setData(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(r => r.empreendimento))].sort();

  const handleSelectRecebimento = (r) => {
    if (selectedRecebimento?.id === r.id) { setSelectedRecebimento(null); return; }
    setSelectedRecebimento(r);
    setBaixaForm({
      valor_pago: r.parcela || 0,
      data_pagamento: new Date().toISOString().split('T')[0],
      acrescimos: 0,
      descontos: 0
    });
  };

  const filtered = data.filter(r => {
    let ok = true;
    if (empreendimentoFilter && r.empreendimento !== empreendimentoFilter) ok = false;
    
    const isAberto = !r.total || r.total <= 0;
    if (statusFilter === 'ABERTA' && !isAberto) ok = false;
    if (statusFilter === 'BAIXADA' && isAberto) ok = false;

    if (dataIniFilter && r.vencimento_iso && r.vencimento_iso < dataIniFilter) ok = false;
    if (dataFimFilter && r.vencimento_iso && r.vencimento_iso > dataFimFilter) ok = false;

    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const str = `${r.cliente} ${r.descricao_venda} ${r.id} ${r.cliente_cnpj}`.toLowerCase();
        if (!str.includes(query)) ok = false;
    }
    return ok;
  });

  const grouped = { 'VENCIDAS': [], 'VENCE HOJE': [], 'VENCE ESTA SEMANA': [], 'VENCE ESTE MÊS': [], 'PRÓXIMOS MESES': [], 'BAIXADAS': [] };
  const today = new Date(); today.setHours(0,0,0,0);
  
  filtered.forEach(r => {
    const isAberto = !r.total || r.total <= 0;
    if (!isAberto) { grouped['BAIXADAS'].push(r); return; }

    if (!r.vencimento_iso) { grouped['PRÓXIMOS MESES'].push(r); return; }
    
    const vDate = new Date(`${r.vencimento_iso}T00:00:00`);
    const diffTime = vDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) grouped['VENCIDAS'].push(r);
    else if (diffDays === 0) grouped['VENCE HOJE'].push(r);
    else if (diffDays <= 7) grouped['VENCE ESTA SEMANA'].push(r);
    else if (vDate.getMonth() === today.getMonth() && vDate.getFullYear() === today.getFullYear()) grouped['VENCE ESTE MÊS'].push(r);
    else grouped['PRÓXIMOS MESES'].push(r);
  });

  const flatGrouped = [
      ...grouped['VENCIDAS'], ...grouped['VENCE HOJE'], ...grouped['VENCE ESTA SEMANA'], ...grouped['VENCE ESTE MÊS'], ...grouped['PRÓXIMOS MESES'], ...grouped['BAIXADAS']
  ];

  const submitBaixa = async (e, r_id) => {
    e.preventDefault();
    try {
      setLoading(true);
      await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          id_receber: r_id.toString().replace('prazo_', ''), // Handle projected ones later if needed, right now we just send ID
          empresa_id: parseInt(selectedEmpresa, 10),
          valor_pago: parseFloat(baixaForm.valor_pago) || 0,
          data_pagamento: baixaForm.data_pagamento,
          acrescimos: parseFloat(baixaForm.acrescimos) || 0,
          descontos: parseFloat(baixaForm.descontos) || 0
        })
      });
      
      const res = await fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`);
      const d = await res.json();
      setData(Array.isArray(d) ? d : []);
      
      const idx = flatGrouped.findIndex(x => x.id === r_id);
      if (idx !== -1 && idx + 1 < flatGrouped.length) {
          const nextR = flatGrouped[idx + 1];
          setSelectedRecebimento(nextR);
          setBaixaForm({
              valor_pago: nextR.parcela || 0,
              data_pagamento: new Date().toISOString().split('T')[0],
              acrescimos: 0,
              descontos: 0
          });
      } else {
          setSelectedRecebimento(null);
      }
      setLoading(false);
    } catch (err) {
      alert("Erro ao dar baixa");
      setLoading(false);
    }
  };

  const totalGeral = filtered.reduce((acc, curr) => acc + (curr.parcela || 0), 0);

  return (
    <div className="flex flex-col h-full animate-in fade-in" style={{ background: '#0c0908' }}>
      <div className="px-6 py-4 flex flex-col gap-4 shrink-0 z-20" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex justify-between items-end">
            <div className="flex items-baseline gap-3">
                <h2 className="text-[24px] font-black tracking-tighter uppercase" style={{ color: '#f0e6d8' }}>Recebimentos</h2>
                <span className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>· {filtered.length} parcelas</span>
            </div>
            
            <div className="flex gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                    <Search size={12}/>
                    <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Buscar parcela..." className="bg-transparent border-none outline-none text-[12px] w-48 placeholder-[#5a4e42]" style={{ color: '#f0e6d8' }} />
                    <kbd className="font-mono text-[10px]" style={{ color: '#5a4e42' }}>/</kbd>
                </div>
                
                <button onClick={() => {
                  const csvContent = "data:text/csv;charset=utf-8," + "Data,Total_Pago,Parcela,Variacao,Venda,Cliente\\n" + filtered.map(e => `${e.data},${e.total},${e.parcela},${e.variacao},"${e.descricao_venda}","${e.cliente}"`).join("\\n");
                  const encodedUri = encodeURI(csvContent);
                  const link = document.createElement("a");
                  link.setAttribute("href", encodedUri);
                  link.setAttribute("download", "recebimentos.csv");
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }} className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-[12px] font-bold shadow-lg transition-colors hover:bg-[#ff7a1a]/90" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                    <Download size={12}/> Exportar CSV <kbd className="ml-1 text-[10px] bg-black/20 border border-black/30 px-1 rounded" style={{ color: '#3a1606' }}>⇧⌘E</kbd>
                </button>
            </div>
        </div>
        
        <div className="flex flex-wrap gap-3 items-center">
            <select value={empreendimentoFilter} onChange={(e) => setEmpreendimentoFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="">Todos Empreendimentos</option>
                {uniqueEmps.map((emp, i) => <option key={i} value={emp}>{emp}</option>)}
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 rounded-lg text-[12px] outline-none" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <option value="TODOS">Todas Parcelas</option>
                <option value="ABERTA">Abertas (Pendentes)</option>
                <option value="BAIXADA">Baixadas (Pagas)</option>
            </select>
            
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)', color: '#8a7a68' }}>
                <span className="text-[11px] font-mono">De</span>
                <input type="date" value={dataIniFilter} onChange={(e) => setDataIniFilter(e.target.value)} className="bg-transparent border-none outline-none text-[11px] font-mono dark-calendar" style={{ color: '#f0e6d8' }} />
                <span className="text-[11px] font-mono">Até</span>
                <input type="date" value={dataFimFilter} onChange={(e) => setDataFimFilter(e.target.value)} className="bg-transparent border-none outline-none text-[11px] font-mono dark-calendar" style={{ color: '#f0e6d8' }} />
                {(dataIniFilter || dataFimFilter) && (
                  <button onClick={() => {setDataIniFilter(''); setDataFimFilter('');}} className="ml-1 hover:text-[#ff7a1a]"><X size={12}/></button>
                )}
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg ml-auto" style={{ background: '#1a1614', border: '1px solid rgba(255, 160, 80, 0.08)' }}>
                <span className="text-[12px]" style={{ color: '#8a7a68' }}>Total Listado:</span>
                <span className="text-[12px] font-mono font-bold" style={{ color: '#f0e6d8' }}>{formatCurrency(totalGeral)}</span>
            </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto custom-scrollbar">
            {loading ? (
                <div className="flex flex-col justify-center items-center h-full gap-3 text-[#8a7a68] animate-pulse">
                    <Loader2 size={32} className="animate-spin text-[#ff7a1a]" />
                    <span className="text-[12px] uppercase font-bold tracking-widest">Carregando carteira...</span>
                </div>
            ) : filtered.length === 0 ? (
                <div className="flex justify-center items-center h-full text-[#5a4e42] uppercase text-[10px] tracking-widest font-bold">Nenhum registro encontrado.</div>
            ) : (
                <div className="flex flex-col">
                    {Object.entries(grouped).filter(([_, items]) => items.length > 0).map(([groupName, items]) => (
                        <div key={groupName} className="mb-4">
                            <div className="px-6 py-2 flex items-center gap-3 sticky top-0 z-10" style={{ background: '#0c0908' }}>
                                <span className={`font-mono text-[9.5px] font-bold tracking-[0.28em] ${groupName === 'VENCIDAS' ? 'text-red-500' : groupName === 'VENCE HOJE' ? 'text-orange-500' : 'text-[#5a4e42]'}`}>
                                    {groupName}
                                </span>
                                <div className="flex-1 h-[1px]" style={{ background: 'rgba(255, 160, 80, 0.08)' }}></div>
                                <span className="font-mono text-[9.5px]" style={{ color: '#5a4e42' }}>{items.length}</span>
                            </div>
                            <div className="flex flex-col">
                                {items.map(r => {
                                    const isSelected = selectedRecebimento?.id === r.id;
                                    const isAberto = !r.total || r.total <= 0;
                                    const isVencida = groupName === 'VENCIDAS';
                                    
                                    return (
                                        <div key={r.id} className="flex flex-col" style={{ borderBottom: '1px solid rgba(255, 160, 80, 0.08)' }}>
                                            <div 
                                                onClick={() => handleSelectRecebimento(r)}
                                                className="grid grid-cols-[80px_40px_1fr_200px_120px_100px_80px] items-center gap-3 px-6 py-3 cursor-pointer transition-colors"
                                                style={{
                                                    background: isSelected ? 'rgba(255, 122, 26, 0.05)' : isVencida ? 'rgba(239, 68, 68, 0.02)' : 'transparent',
                                                    borderLeft: isSelected ? '2px solid #ff7a1a' : isVencida ? '2px solid #ef4444' : '2px solid transparent'
                                                }}
                                            >
                                                <div className="flex flex-col">
                                                    <span className="font-mono text-[10.5px]" style={{ color: isSelected ? '#ff7a1a' : '#5a4e42' }}>#{r.id?.toString().replace('prazo_', 'pr_') || 'N/A'}</span>
                                                    <span className="font-mono text-[9px]" style={{ color: '#8a7a68' }}>{r.num_parcela || ''}</span>
                                                </div>
                                                
                                                <div className="w-[30px] h-[22px] rounded flex items-center justify-center font-mono text-[9.5px] font-bold" 
                                                     style={{ background: 'linear-gradient(135deg, rgba(255, 122, 26, 0.25), rgba(201, 58, 18, 0.15))', border: '1px solid rgba(255, 140, 42, 0.25)', color: '#ffd28a' }}>
                                                    {(r.empreendimento || 'EMP').substring(0,3).toUpperCase()}
                                                </div>
                                                
                                                <div className="min-w-0">
                                                    <div className="font-medium text-[13.5px] truncate" style={{ color: '#f0e6d8' }}>{r.cliente}</div>
                                                    <div className="font-mono text-[10.5px] mt-1" style={{ color: '#8a7a68' }}>
                                                        {r.descricao_venda} · <span style={{ color: '#5a4e42' }}>{r.cliente_cnpj || 'Sem CPF/CNPJ'}</span>
                                                    </div>
                                                </div>
                                                
                                                <div className="font-mono text-[11px] truncate" style={{ color: '#8a7a68' }}>{r.empreendimento}</div>
                                                
                                                <div className={`font-medium text-[13.5px] font-mono ${isVencida ? 'text-red-400' : 'text-[#f0e6d8]'}`}>{formatCurrency(r.parcela)}</div>
                                                
                                                <div className="flex items-center gap-2">
                                                    {!isAberto ? (
                                                        <><span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_6px_#22c55e]"></span><span className="font-mono text-[9.5px] tracking-[0.16em] text-green-500">PAGO</span></>
                                                    ) : isVencida ? (
                                                        <><span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_6px_#ef4444]"></span><span className="font-mono text-[9.5px] tracking-[0.16em] text-red-500">ATRASADA</span></>
                                                    ) : (
                                                        <><span className="w-1.5 h-1.5 rounded-full" style={{ background: '#ffc247', boxShadow: '0 0 6px #ffc247' }}></span><span className="font-mono text-[9.5px] tracking-[0.16em]" style={{ color: '#ffc247' }}>ABERTA</span></>
                                                    )}
                                                </div>
                                                
                                                <div className="font-mono text-[10px] text-right" style={{ color: '#5a4e42' }}>{r.data}</div>
                                            </div>

                                            {isSelected && isAberto && (
                                                <div className="px-6 py-4 animate-in slide-in-from-top-2" style={{ background: 'rgba(255, 122, 26, 0.02)', borderLeft: '2px solid #ff7a1a' }}>
                                                    <form onSubmit={(e) => submitBaixa(e, r.id)} className="flex items-end gap-4">
                                                        <div className="flex-1 grid grid-cols-4 gap-4">
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Data Pgto</label>
                                                                <input type="date" required value={baixaForm.data_pagamento} onChange={e => setBaixaForm({...baixaForm, data_pagamento: e.target.value})} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-[#f0e6d8] rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] dark-calendar font-mono" />
                                                            </div>
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Valor</label>
                                                                <input type="number" step="0.01" required value={baixaForm.valor_pago} onChange={e => setBaixaForm({...baixaForm, valor_pago: e.target.value})} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-[#f0e6d8] rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] font-mono" />
                                                            </div>
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Acréscimos</label>
                                                                <input type="number" step="0.01" value={baixaForm.acrescimos} onChange={e => setBaixaForm({...baixaForm, acrescimos: e.target.value})} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-green-400 rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] font-mono" />
                                                            </div>
                                                            <div>
                                                                <label className="text-[9.5px] uppercase font-bold text-[#8a7a68] block mb-1.5 tracking-widest">Descontos</label>
                                                                <input type="number" step="0.01" value={baixaForm.descontos} onChange={e => setBaixaForm({...baixaForm, descontos: e.target.value})} className="w-full bg-[#1a1614] border border-[rgba(255,160,80,0.08)] text-red-400 rounded p-2 text-[11px] outline-none focus:border-[#ff7a1a] font-mono" />
                                                            </div>
                                                        </div>
                                                        <button type="submit" className="h-[34px] px-6 rounded-lg text-[10px] font-bold uppercase tracking-widest shadow-[0_0_15px_rgba(255,122,26,0.2)] hover:opacity-90 transition-opacity flex items-center justify-center gap-2" style={{ background: 'linear-gradient(135deg, #ff7a1a, #c93a12)', color: '#1a0a04' }}>
                                                            <CheckCircle2 size={12} /> Salvar <kbd className="ml-1 text-[9px] bg-black/20 px-1 rounded">↵</kbd>
                                                        </button>
                                                    </form>
                                                </div>
                                            )}
                                            
                                            {isSelected && !isAberto && (
                                                <div className="px-6 py-4 flex gap-8 items-center animate-in slide-in-from-top-2" style={{ background: 'rgba(34, 197, 94, 0.02)', borderLeft: '2px solid #22c55e' }}>
                                                    <div>
                                                        <span className="font-mono text-[9px] tracking-[0.18em] text-green-600/70 block mb-1">DATA EFETIVA</span>
                                                        <span className="text-[12px] font-mono text-green-500 font-bold">{r.data_pagamento || r.data}</span>
                                                    </div>
                                                    <div>
                                                        <span className="font-mono text-[9px] tracking-[0.18em] text-green-600/70 block mb-1">TOTAL PAGO</span>
                                                        <span className="text-[12px] font-mono text-green-500 font-bold">{formatCurrency(r.total)}</span>
                                                    </div>
                                                    <div>
                                                        <span className="font-mono text-[9px] tracking-[0.18em] text-green-600/70 block mb-1">VARIAÇÃO</span>
                                                        <span className="text-[12px] font-mono text-green-500">{formatCurrency(r.variacao)}</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
      </div>

      <div className="px-6 py-2 flex justify-between items-center shrink-0 z-20" style={{ background: '#0c0908', borderTop: '1px solid rgba(255, 160, 80, 0.08)' }}>
        <div className="flex gap-4 font-mono text-[9px] font-bold tracking-[0.16em]" style={{ color: '#5a4e42' }}>
            <span>↑ ↓ NAVEGAR</span>
            <span>↵ AÇÃO RÁPIDA</span>
            <span>/ BUSCAR</span>
            <span>⇧⌘E EXPORTAR</span>
        </div>
      </div>

    </div>
  );
}
"""

new_content = content[:start_idx] + new_func + content[end_idx:]

with open('frontend/src/VulcanoViews.jsx', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated component RecebimentosView inline form successfully.')
