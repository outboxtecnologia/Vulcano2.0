import codecs

with codecs.open('frontend/src/App.jsx', 'r', 'utf-8') as f:
    app_code = f.read()

# 1. State Replacement
old_state = """  // POC State
  const [pocData, setPocData] = useState([]);
  const [pocPeriodo, setPocPeriodo] = useState('');
  const [pocDrafts, setPocDrafts] = useState({});
  const [loadingPoc, setLoadingPoc] = useState({});"""

new_state = """  // POC State
  const [pocData, setPocData] = useState([]);
  const [pocPeriodo, setPocPeriodo] = useState(''); // Keep global period as requested
  const [selectedPocEmp, setSelectedPocEmp] = useState(null);
  const [pocInputPct, setPocInputPct] = useState('');
  const [loadingPoc, setLoadingPoc] = useState(false);"""

app_code = app_code.replace(old_state, new_state)

# 2. Logic Replacement
old_logic = """  const handleSaveSinglePoc = (emp, pct) => {
    if (!pocPeriodo || pct === undefined || pct === '') {
       alert('Selecione o mês de referência (Período) no topo e preencha um percentual válido!');
       return;
    }
    
    setLoadingPoc(prev => ({...prev, [emp]: true}));
    fetch(`${API_BASE}/api/poc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empreendimento: emp,
        periodo: pocPeriodo,
        percentual: parseFloat(pct)
      })
    })
    .then(res => res.json())
    .then(() => {
       fetchPoc();
       setPocDrafts(prev => { const n = {...prev}; delete n[emp]; return n; });
    })
    .catch((err) => console.error("Erro", err))
    .finally(() => setLoadingPoc(prev => ({...prev, [emp]: false})));
  };"""

new_logic = """  const handleSavePocDetail = (e) => {
    e.preventDefault();
    if (!selectedPocEmp || !pocPeriodo || !pocInputPct) {
       alert('Selecione um Empreendimento, informe o Mês/Ano Referência no topo e digite o POC Novo %!');
       return;
    }
    
    setLoadingPoc(true);
    fetch(`${API_BASE}/api/poc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empreendimento: selectedPocEmp,
        periodo: pocPeriodo,
        percentual: parseFloat(pocInputPct)
      })
    })
    .then(res => res.json())
    .then(() => {
       fetchPoc();
       setPocInputPct('');
    })
    .catch((err) => console.error("Erro", err))
    .finally(() => setLoadingPoc(false));
  };"""

app_code = app_code.replace(old_logic, new_logic)

# 3. View Block Replacement
start_str = "{currentView === 'poc' && ("
start_idx = app_code.find(start_str)

end_marker = "{/* Area Removida: Llama Painel */}"
end_marker_idx = app_code.find(end_marker)

slice_before_marker = app_code[start_idx:end_marker_idx]
local_end_idx = slice_before_marker.rfind("           )}")

if start_idx != -1 and local_end_idx != -1:
    absolute_end_idx = start_idx + local_end_idx + len("           )}")
    
    new_poc_view = """           {currentView === 'poc' && (
             <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full pb-20">
               <div className="flex justify-between items-end bg-surface-container-lowest p-6 rounded-sm border border-outline-variant/10 shadow-sm">
                 <div>
                   <h2 className="font-headline text-3xl font-bold text-on-surface tracking-tight uppercase">Dashboard de Evolução Físico-Financeira</h2>
                   <p className="text-on-surface-variant font-body text-[10px] mt-1 uppercase tracking-[0.2em] font-bold">Apropriação Contábil IFRS 15 • {uniqueEmpreendimentos.length} Projetos Ativos</p>
                 </div>
                 <div className="flex gap-4 items-end">
                   <div className="flex flex-col">
                     <label className="text-[9px] text-on-surface-variant font-bold uppercase tracking-widest mb-2 flex items-center gap-1"><Calendar size={12}/> Mês/Ano Referência (Global)</label>
                     <input type="month" value={pocPeriodo} onChange={e => setPocPeriodo(e.target.value)} className="bg-surface-container border border-outline-variant/20 text-on-surface p-2 rounded-sm outline-none focus:border-primary/50 text-xs font-mono uppercase transition-colors h-[40px] w-48 shadow-inner" required />
                   </div>
                 </div>
               </div>

               <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                 {/* ===== MASTER LIST (Esquerda) ===== */}
                 <div className="lg:col-span-4 bg-surface-container-lowest border border-outline-variant/20 rounded-sm overflow-hidden flex flex-col shadow-xl h-[700px]">
                    <div className="p-6 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-low shrink-0">
                       <div>
                         <h3 className="text-sm font-headline font-bold text-on-surface uppercase tracking-[0.2em] flex items-center gap-2"><PieChart size={16} className="text-primary"/> Projetos (Master)</h3>
                         <p className="text-[9px] text-on-surface-variant tracking-[0.3em] uppercase mt-2">Clique para Detalhar</p>
                       </div>
                    </div>
                    <div className="overflow-y-auto flex-1 p-0">
                      <table className="w-full text-left border-collapse text-xs whitespace-nowrap font-body">
                         <thead className="sticky top-0 z-10">
                           <tr>
                              <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-r border-outline-variant/10 text-[10px] bg-surface-container-low">Empreendimento</th>
                              <th className="p-4 font-bold text-primary uppercase tracking-widest border-b border-outline-variant/10 text-[10px] bg-primary/5 text-right w-[80px]">POC Atual</th>
                           </tr>
                         </thead>
                         <tbody>
                            {uniqueEmpreendimentos.length > 0 ? uniqueEmpreendimentos.map((emp, i) => {
                               // Safe string matching
                               const safeEmp = emp ? emp.trim().toUpperCase() : '';
                               const projPoc = pocData.filter(p => p.empreendimento && p.empreendimento.trim().toUpperCase() === safeEmp).sort((a,b) => b.periodo.localeCompare(a.periodo))[0];
                               const pct = projPoc ? projPoc.percentual : 0;
                               const isSelected = selectedPocEmp === emp;

                               return (
                                 <tr key={i} onClick={() => setSelectedPocEmp(emp)} className={`border-b border-outline-variant/10 transition-colors cursor-pointer ${isSelected ? 'bg-primary/10 border-l-4 border-l-primary' : 'hover:bg-surface-container-highest'}`}>
                                    <td className="p-4 font-bold uppercase tracking-widest text-[11px] truncate max-w-[200px] border-r border-outline-variant/10 text-on-surface" title={emp}>{emp}</td>
                                    <td className="p-4 text-primary font-mono font-black text-right">{pct.toFixed(2)}%</td>
                                 </tr>
                               )
                            }) : <tr><td colSpan={2} className="p-8 text-center text-on-surface-variant tracking-widest uppercase text-[10px]">Nenhum Empreendimento Encontrado. Verifique os Filtros.</td></tr>}
                         </tbody>
                      </table>
                    </div>
                 </div>

                 {/* ===== DETAIL VIEW (Direita) ===== */}
                 <div className="lg:col-span-8 bg-surface-container-lowest border border-outline-variant/20 rounded-sm flex flex-col shadow-xl h-[700px]">
                    {!selectedPocEmp ? (
                       <div className="flex-1 flex flex-col items-center justify-center text-center p-8 opacity-50">
                          <Construction size={64} className="text-on-surface-variant mb-6" />
                          <h2 className="text-2xl font-headline font-black text-on-surface mb-2 uppercase tracking-tight">Nenhuma Obra Selecionada</h2>
                          <p className="text-on-surface-variant uppercase tracking-widest text-[10px] max-w-sm">Selecione um projeto na lista Master (à esquerda) para auditar seu histórico e informar um novo valor de evolução referencial.</p>
                       </div>
                    ) : (
                       <div className="flex flex-col h-full fade-in animate-in">
                          {/* Topo do Detail (Header + Form) */}
                          <div className="p-6 border-b border-outline-variant/20 bg-surface-container-low shrink-0 relative overflow-hidden">
                             <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none"><Construction size={120}/></div>
                             <div className="flex justify-between items-start mb-6">
                               <div className="relative z-10 w-full">
                                  <h3 className="text-on-surface-variant text-[10px] uppercase font-bold tracking-[0.3em] mb-1">Visão Detalhe (WIP)</h3>
                                  <h2 className="text-2xl font-headline font-black text-primary uppercase tracking-tight truncate max-w-[90%]" title={selectedPocEmp}>{selectedPocEmp}</h2>
                               </div>
                             </div>

                             <form onSubmit={handleSavePocDetail} className="bg-surface-container-lowest p-6 border border-primary/20 rounded-sm shadow-inner relative z-10 flex gap-4 items-end">
                                <div className="flex-1">
                                   <label className="text-[9px] text-on-surface-variant font-bold uppercase tracking-widest mb-2 flex items-center gap-1">Lançar Novo POC (%)</label>
                                   <div className="relative">
                                     <input type="number" step="0.01" value={pocInputPct} onChange={(e) => setPocInputPct(e.target.value)} className="w-full bg-surface-container border border-outline-variant/30 p-3 text-right font-mono font-black text-primary focus:border-primary transition-colors outline-none rounded-sm text-xl" placeholder="0.00" autoFocus />
                                     <span className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant/50 text-[12px] font-bold">%</span>
                                   </div>
                                </div>
                                <button type="submit" disabled={loadingPoc} className="bg-primary text-on-primary font-black uppercase tracking-[0.2em] text-[10px] px-8 h-[54px] rounded-sm hover:opacity-90 disabled:opacity-50 transition-opacity whitespace-nowrap flex items-center gap-2">
                                  <ArrowUpRight size={14} /> {loadingPoc ? 'Processando...' : 'Gravar (IFRS 15)'}
                                </button>
                             </form>
                          </div>

                          {/* Tabela de Histórico (Bottom Detail) */}
                          <div className="flex-1 overflow-y-auto p-0 bg-surface-container-lowest">
                             <table className="w-full text-left border-collapse text-xs whitespace-nowrap font-body">
                               <thead className="sticky top-0 z-10 shadow-sm">
                                 <tr>
                                   <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-low text-[10px]">Mês Ref.</th>
                                   <th className="p-4 font-bold text-primary uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-low text-[10px] text-right">Evolução Adquirida (POC)</th>
                                   <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-low text-[10px] text-center">Auditoria</th>
                                 </tr>
                               </thead>
                               <tbody>
                                  {pocData.filter(p => p.empreendimento && p.empreendimento.trim().toUpperCase() === selectedPocEmp.trim().toUpperCase())
                                      .sort((a,b) => b.periodo.localeCompare(a.periodo))
                                      .map((row, idx) => (
                                    <tr key={idx} className="border-b border-outline-variant/5 bg-surface-container hover:bg-surface-container-highest transition-colors group">
                                      <td className="p-4 text-on-surface font-mono font-bold text-[12px]">{row.periodo}</td>
                                      <td className="p-4 font-black text-primary font-mono tracking-tight text-right text-lg">{row.percentual.toFixed(2)}%</td>
                                      <td className="p-4 text-center">
                                        <span className="px-2 py-1 bg-tertiary-container/30 text-tertiary rounded-sm uppercase tracking-widest border border-tertiary/20 text-[8px] font-bold">Consolidado</span>
                                      </td>
                                    </tr>
                                  ))}
                                  {pocData.filter(p => p.empreendimento && p.empreendimento.trim().toUpperCase() === selectedPocEmp.trim().toUpperCase()).length === 0 && (
                                    <tr><td colSpan={3} className="p-12 text-center text-on-surface-variant tracking-widest uppercase text-[10px]">Sem histórico registrado para esta obra.</td></tr>
                                  )}
                               </tbody>
                             </table>
                          </div>
                       </div>
                    )}
                 </div>
               </div>
             </div>
           )}"""
    
    app_code = app_code[:start_idx] + new_poc_view + app_code[absolute_end_idx:]

    with codecs.open('frontend/src/App.jsx', 'w', 'utf-8') as f:
        f.write(app_code)
    print("SUCCESS POC MASTER DETAIL")
else:
    print("ERROR FINDING STRINGS")
