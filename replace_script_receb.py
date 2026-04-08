import codecs
import re

with codecs.open('frontend/src/VulcanoViews.jsx', 'r', 'utf-8') as f:
    content = f.read()

# Match the exact RecebimentosView block
pattern = re.compile(r'^export const RecebimentosView =.*?(?=\nexport const )', re.MULTILINE | re.DOTALL)
match = pattern.search(content)

if not match:
    # If not found using lookahead (e.g. if RecebimentosView is the last export), try matching until the end
    pattern = re.compile(r'^export const RecebimentosView =.*', re.MULTILINE | re.DOTALL)
    match = pattern.search(content)

if match:
    new_recebimentos_view = """export const RecebimentosView = ({ selectedEmpresa }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [empreendimentoFilter, setEmpreendimentoFilter] = useState('');
  const [unidadeFilter, setUnidadeFilter] = useState('');
  const [clienteFilter, setClienteFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showConferencia, setShowConferencia] = useState(false);
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 100;

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
      .then(res => res.json())
      .then(d => {
        if (!Array.isArray(d)) {
           setData([]);
           setLoading(false);
           return;
        }
        setData(d);
        const emps = [...new Set(d.map(r => r.empreendimento))].sort();
        if (emps.length > 0) setEmpreendimentoFilter(emps[0]);
        else setEmpreendimentoFilter('');
        
        setUnidadeFilter(''); setClienteFilter('');
        setDateFrom(''); setDateTo('');
        setLoading(false);
      })
      .catch(err => { console.error(err); setLoading(false); });
  }, [selectedEmpresa]);

  const uniqueEmps = [...new Set(data.map(r => r.empreendimento))].sort();
  const filteredBase = data.filter(r => !empreendimentoFilter || r.empreendimento === empreendimentoFilter);
  const uniqueUnidades = [...new Set(filteredBase.map(r => r.descricao_venda).filter(Boolean))].sort();
  const uniqueClientes = [...new Set(filteredBase.map(r => r.cliente).filter(Boolean))].sort();

  const inDateRange = (dateStr) => {
    if (!dateFrom && !dateTo) return true;
    if (!dateStr || typeof dateStr !== 'string') return false;
    if (dateFrom && dateStr < dateFrom) return false;
    if (dateTo && dateStr > dateTo) return false;
    return true;
  };

  const filtered = filteredBase.filter(r =>
    inDateRange(r.data) &&
    (!unidadeFilter || r.descricao_venda === unidadeFilter) &&
    (!clienteFilter || r.cliente === clienteFilter)
  );

  useEffect(() => {
    setUnidadeFilter(''); setClienteFilter('');
    setDateFrom(''); setDateTo('');
    setCurrentPage(1); // Reset pagination on master filter change
  }, [empreendimentoFilter]);
  
  // When sub-filters change, reset page
  useEffect(() => {
     setCurrentPage(1);
  }, [unidadeFilter, clienteFilter, dateFrom, dateTo]);

  const totalPago = filtered.reduce((acc, curr) => acc + ((curr.total > 0) ? curr.total : 0), 0);
  const totalParcela = filtered.reduce((acc, curr) => acc + (curr.parcela || 0), 0);
  const totalVariacao = filtered.reduce((acc, curr) => acc + (curr.variacao || 0), 0);
  
  // Pagination Math
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const handleDarBaixa = async (r) => {
    if (!r.id) return alert("Parcela não possui ID vinculado.");
    const valorInput = prompt(`Dar baixa na parcela ${r.num_parcela} de ${formatCurrency(r.parcela)}?\\nDigite o valor pago:`, r.parcela);
    if (!valorInput) return;
    const valorPago = parseFloat(valorInput.replace(',', '.'));
    if (isNaN(valorPago) || valorPago <= 0) return alert("Valor inválido");

    try {
      setLoading(true);
      await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_receber: r.id, valor_pago: valorPago })
      });
      fetch(`${API_BASE}/api/vulcano/recebimentos?empresa_id=${selectedEmpresa}`)
        .then(res => res.json()).then(d => { setData(d); setLoading(false); });
    } catch (err) {
      alert("Erro ao dar baixa");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in max-w-7xl mx-auto w-full h-full flex flex-col pt-4">
      {/* HEADER STITCH */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black tracking-tighter uppercase mb-1 text-[var(--v-text-bold)] flex items-center gap-3">
             <DollarSign className="text-[var(--v-accent)]" size={32}/> 
             Extrato de Recebimentos
          </h2>
          <p className="text-xs text-[var(--v-text-faint)] uppercase tracking-[0.2em] ml-11">Industrial Master-Detail Ledger</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowConferencia(true)} className="bento-button flex items-center gap-2">
            <CheckCircle2 size={16}/> Modo Conferência
          </button>
          <button onClick={() => {
            const csvContent = "data:text/csv;charset=utf-8," + "Data,Total_Pago,Parcela,Variacao,Venda,Cliente\\n" + filtered.map(e => `${e.data},${e.total},${e.parcela},${e.variacao},"${e.descricao_venda}","${e.cliente}"`).join("\\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "recebimentos.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }} className="bento-button flex items-center gap-2">
            <Download size={16}/> Baixar CSV
          </button>
          <button onClick={() => setShowForm(!showForm)} className="bg-[var(--v-accent)] text-black text-[11px] font-bold uppercase tracking-widest px-4 py-3 rounded-sm hover:opacity-90 transition-opacity flex items-center gap-2">
            <Plus size={16}/> Lançar Manual
          </button>
        </div>
      </div>

      {showForm && (
        <div className="magma-card border border-[var(--v-accent)]/30 rounded-sm p-5 animate-in slide-in-from-top-4">
          <h3 className="text-xs uppercase tracking-widest text-[var(--v-accent)] font-bold mb-4">Novo Recebimento (Bypass Caixa)</h3>
          <form className="flex flex-wrap gap-4 items-end" onSubmit={async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await fetch(`${API_BASE}/api/vulcano/recebimentos/baixa`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(fd)) });
              alert("Recebimento cadastrado!"); e.target.reset(); setShowForm(false);
            } catch (err) { alert("Erro ao cadastrar."); }
          }}>
            <input type="hidden" name="empresa_id" value={selectedEmpresa} />
            <div className="w-24"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">ID Venda</label><input name="id_venda" type="number" required className="bento-input" /></div>
            <div className="w-28"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Parcela</label><input name="parcela" type="number" required className="bento-input" /></div>
            <div className="w-32"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Valor Venda</label><input name="valor" type="number" step="0.01" required className="bento-input" /></div>
            <div className="w-40"><label className="text-[10px] text-[#888] uppercase tracking-widest block mb-1">Data Pagto</label><input name="data" type="date" required className="bento-input" /></div>
            <button type="submit" className="bg-[var(--v-accent)] text-black text-[11px] font-bold uppercase tracking-widest px-8 py-3 rounded-sm hover:opacity-90">Confirmar</button>
          </form>
        </div>
      )}

      {/* STITCH MASTER-DETAIL LAYOUT */}
      <div className="flex gap-6 h-[calc(100vh-280px)] overflow-hidden">
        {/* SIDEBAR MASTER */}
        <div className="w-64 magma-card rounded-sm flex flex-col shrink-0 border border-[var(--v-border)]">
          <div className="p-4 border-b border-[var(--v-border)] bg-[var(--v-surface-container)] flex items-center gap-2">
            <Building2 size={16} className="text-[var(--v-text-faint)]"/>
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-[var(--v-text-muted)]">Obras/Empreendimentos</h3>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            <div 
              onClick={() => setEmpreendimentoFilter('')}
              className={`p-3 text-xs font-bold cursor-pointer transition-colors rounded-sm ${empreendimentoFilter === '' ? 'text-[var(--v-accent)] bg-[var(--v-hover)]' : 'text-[var(--v-text-muted)] hover:text-[var(--v-text)] hover:bg-[var(--v-border)]'}`}
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
                {emp}
              </div>
            ))}
          </div>
        </div>

        {/* DETAIL CONTENT */}
        <div className="flex-1 flex flex-col gap-5 overflow-hidden">
          {/* KPI BENTO GRIDS */}
          <div className="grid grid-cols-3 gap-5 shrink-0">
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Recebido (Caixa)</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalPago)}</h4>
               </div>
               <DollarSign size={40} className="text-[var(--v-accent)] opacity-20 absolute -right-2 -bottom-2 group-hover:scale-110 transition-transform"/>
            </div>
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent-3)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Origem Parcela</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalParcela)}</h4>
               </div>
            </div>
            <div className="magma-card overflow-hidden relative group p-5 border-l-4 border-l-[var(--v-accent-6)] flex justify-between">
               <div>
                  <p className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] font-bold mb-1">Variação Realizada</p>
                  <h4 className="text-3xl font-black text-[var(--v-text-bold)]">{formatCurrency(totalVariacao)}</h4>
               </div>
            </div>
          </div>

          {/* FILTER STRIP */}
          <div className="magma-card border border-[var(--v-border)] rounded-sm p-4 shrink-0 flex flex-wrap gap-4 items-end bg-[var(--v-surface-container)]">
            <div className="w-32"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">De</label><input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="bento-input w-full"/></div>
            <div className="w-32"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Até</label><input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="bento-input w-full"/></div>
            <div className="flex-1 min-w-[200px]"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Unidade</label>
              <select value={unidadeFilter} onChange={e => setUnidadeFilter(e.target.value)} className="bento-select w-full">
                 <option value="">TODAS AS UNIDADES</option>
                 {uniqueUnidades.map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <div className="flex-1 min-w-[200px]"><label className="text-[10px] uppercase tracking-widest text-[var(--v-text-faint)] block mb-2">Comprador</label>
              <select value={clienteFilter} onChange={e => setClienteFilter(e.target.value)} className="bento-select w-full">
                 <option value="">TODOS COMPRADORES</option>
                 {uniqueClientes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <button onClick={() => { setDateFrom(''); setDateTo(''); setUnidadeFilter(''); setClienteFilter(''); }} className="bento-button py-3">LIMPAR</button>
          </div>

          {/* TABLE DATA GRID (PAGINATED) */}
          <div className="magma-card border border-[var(--v-border)] rounded-sm flex flex-col flex-1 overflow-hidden relative">
            {loading && (
               <div className="absolute inset-0 bg-[#00000099] backdrop-blur-sm flex flex-col items-center justify-center z-50">
                   <Loader2 className="animate-spin text-[var(--v-accent)] mb-3" size={40} />
                   <span className="text-[10px] font-bold uppercase tracking-widest text-white">Carregando Diário de Caixa...</span>
               </div>
            )}
            <div className="overflow-auto flex-1">
               <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-[var(--v-surface-container)] sticky top-0 z-10 shadow-sm border-b border-[var(--v-border)]">
                     <tr>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold w-24">Data</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent)] uppercase font-bold text-right">Pago</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-accent-3)] uppercase font-bold text-right">Parcela</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-right">Variação</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Unidade</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Comprador</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold">Obs</th>
                       <th className="p-3 text-[10px] tracking-widest text-[var(--v-text-faint)] uppercase font-bold text-center w-24">Ação</th>
                     </tr>
                  </thead>
                  <tbody>
                     {paginatedData.map((r, idx) => {
                       const isAberto = !r.total || r.total <= 0;
                       let isAtrasada = false;
                       if (isAberto && r.data) {
                          const parts = r.data.split('/');
                          if (parts.length === 3) {
                             const vencDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}T00:00:00`);
                             const today = new Date(); today.setHours(0,0,0,0);
                             if (vencDate < today) isAtrasada = true;
                          }
                       }
                       return (
                         <tr key={idx} className={`border-b border-[var(--v-border)] transition-colors hover:bg-[var(--v-hover)] ${isAtrasada ? 'bg-[var(--v-accent)]/5 border-l-2 border-l-[var(--v-accent)]' : ''}`}>
                            <td className="p-3 text-[var(--v-text-muted)] font-mono">{r.data}</td>
                            <td className="p-3 text-right font-black text-[var(--v-accent)] text-[13px]">{!isAberto ? formatCurrency(r.total) : isAtrasada ? <span className="text-[var(--v-accent)] text-[9px] uppercase px-2 py-0.5 bg-[var(--v-accent)]/10 rounded">Atrasada</span> : <span className="text-[var(--v-text-faint)] text-[9px] uppercase">A Vencer</span>}</td>
                            <td className="p-3 text-right font-bold text-[var(--v-accent-3)] font-mono">{formatCurrency(r.parcela)}</td>
                            <td className="p-3 text-right font-bold text-[var(--v-accent-6)] font-mono">{formatCurrency(r.variacao)}</td>
                            <td className="p-3 text-[var(--v-text-muted)] truncate max-w-[150px]">{r.descricao_venda}</td>
                            <td className="p-3 text-[var(--v-text)] truncate max-w-[150px] font-bold">{r.cliente}</td>
                            <td className="p-3 text-[10px] uppercase text-[var(--v-text-faint)] truncate max-w-[100px]">{r.obs}</td>
                            <td className="p-3 text-center">
                               {isAberto ? (
                                   <button onClick={() => handleDarBaixa(r)} className="text-[var(--v-accent)] border border-[var(--v-accent)] hover:bg-[var(--v-accent)] hover:text-black transition-colors text-[9px] font-bold uppercase py-1 px-3 rounded-full">Liquidar</button>
                               ) : <span className="text-[var(--v-text-muted)] text-[9px] uppercase font-bold flex items-center justify-center gap-1"><CheckCircle size={10}/> Baixado</span>}
                            </td>
                         </tr>
                       )
                     })}
                     {paginatedData.length === 0 && !loading && (
                        <tr><td colSpan="8" className="p-12 text-center text-[var(--v-text-faint)] uppercase tracking-widest text-[10px]">Nenhuma parcela encontrada.</td></tr>
                     )}
                  </tbody>
               </table>
            </div>

            {/* OVERENGINEERED PAGINATION FOOTER */}
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

      {/* CONFERENCIA MODAL */}
      {showConferencia && (
         <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/95 p-6 animate-in fade-in">
           <div className="magma-card w-full h-full max-w-[1600px] flex flex-col border border-[var(--v-border)]">
             <div className="flex justify-between items-center p-5 border-b border-[var(--v-border)] bg-[var(--v-surface-container)] shrink-0">
               <div>
                 <h3 className="text-xl font-bold uppercase tracking-wider text-[var(--v-accent-3)] flex items-center gap-3">
                   <ShieldAlert size={24}/> Auditoria de Matriz Completa
                 </h3>
                 <p className="text-[10px] text-[var(--v-text-faint)] uppercase tracking-[0.2em] mt-1">Conferência Tabela de Vendas / Recebimentos ({filtered.length} linhas globais)</p>
               </div>
               <button onClick={() => setShowConferencia(false)} className="text-[var(--v-text-faint)] hover:text-white transition-colors p-2 bg-[var(--v-hover)] rounded border border-[var(--v-border)]">
                 <X size={20}/>
               </button>
             </div>
             
             <div className="flex-1 overflow-auto bg-[#0a0a0a]">
               <table className="w-full text-left text-[11px] border-collapse whitespace-nowrap">
                 <thead className="sticky top-0 bg-[var(--v-surface-container)] z-10 border-b border-[var(--v-border)]">
                   <tr>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">CNPJ/CPF</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Comprador</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Unidade</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Vlr Venda</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">Data</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-accent-3)]">Parcela</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-red)]">Desc.</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-accent-6)]">Variação</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-accent)]">Total Pago</th>
                     <th className="p-3 border-r border-[#222] font-bold uppercase tracking-wider text-[var(--v-text-muted)]">X/Y</th>
                   </tr>
                 </thead>
                 <tbody>
                   {/* Hard limiter to 1000 in Modal to prevent freeze if user clicks Conferencia without filters */}
                   {filtered.slice(0, 1000).map((r, i) => (
                     <tr key={i} className="border-b border-[var(--v-border)] hover:bg-[var(--v-hover)] text-[var(--v-text)] font-mono">
                       <td className="p-3 border-r border-[#222] text-[var(--v-text-muted)]">{r.cliente_cnpj || '-'}</td>
                       <td className="p-3 border-r border-[#222] font-sans truncate max-w-[200px]">{r.cliente}</td>
                       <td className="p-3 border-r border-[#222] font-sans truncate max-w-[150px]">{r.descricao_venda}</td>
                       <td className="p-3 border-r border-[#222] text-right text-[var(--v-text-muted)] bg-[#111]">{r.venda_total ? formatCurrency(r.venda_total) : '-'}</td>
                       <td className="p-3 border-r border-[#222]">{r.data || '-'}</td>
                       <td className="p-3 border-r border-[#222] text-right text-[var(--v-accent-3)] bg-[var(--v-accent-3)]/5">{formatCurrency(r.parcela)}</td>
                       <td className="p-3 border-r border-[#222] text-right text-[var(--v-text-red)]">{r.desconto > 0 ? formatCurrency(r.desconto) : '-'}</td>
                       <td className="p-3 border-r border-[#222] text-right text-[var(--v-accent-6)] font-semibold">{r.variacao > 0 ? formatCurrency(r.variacao) : '-'}</td>
                       <td className="p-3 border-r border-[#222] text-right text-[var(--v-accent)] font-bold bg-[var(--v-accent)]/10">{formatCurrency(r.total)}</td>
                       <td className="p-3 border-r border-[#222] text-center">{r.num_parcela || '-'}</td>
                     </tr>
                   ))}
                   {filtered.length > 1000 && (
                     <tr><td colSpan="10" className="p-6 text-center text-[var(--v-text-bold)] bg-[var(--v-accent)]/20 uppercase tracking-widest text-xs font-bold">Limitado a 1000 amostras na Conferência Visual. Exporte em CSV para visualizar os {filtered.length} registros.</td></tr>
                   )}
                 </tbody>
               </table>
             </div>
           </div>
         </div>
      )}
    </div>
  );
};"""

    modified_content = content[:match.start()] + new_recebimentos_view + "\n" + content[match.end():]
    with codecs.open('frontend/src/VulcanoViews.jsx', 'w', 'utf-8') as f:
        f.write(modified_content)
    print("SUCCESS: RecebimentosView replaced!")
else:
    print("ERROR: Could not find RecebimentosView in VulcanoViews.jsx")
