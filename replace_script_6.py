import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

# 2. handleSavePoc Function Replacement
# Search manually without regex for handleSavePoc
target_handle_poc = """  const handleSavePoc = (e) => {
    e.preventDefault();
    if (!pocEmpreendimento || !pocPeriodo || !pocPercentual) return;
    
    setLoadingPoc(true);
    fetch(`${API_BASE}/api/poc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empreendimento: pocEmpreendimento,
        periodo: pocPeriodo,
        percentual: parseFloat(pocPercentual)
      })
    }).then(() => {
      alert('Evolução salva com sucesso!');
      fetchPoc();
      setPocEmpreendimento('');
      setPocPeriodo('');
      setPocPercentual('');
    }).catch(err => console.error(err))
      .finally(() => setLoadingPoc(false));
  };"""

new_handle_poc = """  const handleSaveSinglePoc = (emp, pct) => {
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

if target_handle_poc in app_code:
    app_code = app_code.replace(target_handle_poc, new_handle_poc)
    print("SUCCESS HANDLE POC")
else:
    print("FAILED TO MATCH HANDLE POC STRING")

# 3. View Router POC
old_poc_view_pattern = re.compile(r'           \{/\* =============== POC DASHBOARD \(Stitch Img Match\) =============== \*/\}\n           \{currentView === \'poc\' && \(\n(.*?)\s*\}\)\}\s*(?=\{/\* Area Removida: Llama Painel \*/\})', re.DOTALL)

new_poc_view = """           {/* =============== POC DASHBOARD (Stitch Img Match) =============== */}
           {currentView === 'poc' && (
             <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full pb-20">
               <div className="flex justify-between items-end bg-surface-container-lowest p-6 rounded-sm border border-outline-variant/10 shadow-sm">
                 <div>
                   <h2 className="font-headline text-3xl font-bold text-on-surface tracking-tight uppercase">Dashboard de Evolução Físico-Financeira</h2>
                   <p className="text-on-surface-variant font-body text-[10px] mt-1 uppercase tracking-[0.2em] font-bold">Apropriação Contábil IFRS 15 • {pocData.length} registros no Lote</p>
                 </div>
                 <div className="flex gap-4 items-end">
                   <div className="flex flex-col">
                     <label className="text-[9px] text-on-surface-variant font-bold uppercase tracking-widest mb-2 flex items-center gap-1"><Calendar size={12}/> Mês/Ano Referência (Global)</label>
                     <input type="month" value={pocPeriodo} onChange={e => setPocPeriodo(e.target.value)} className="bg-surface-container border border-outline-variant/20 text-on-surface p-2 rounded-sm outline-none focus:border-primary/50 text-xs font-mono uppercase transition-colors h-[40px] w-48 shadow-inner" required />
                   </div>
                 </div>
               </div>

               {/* Master KPI */}
               <div className="bg-primary/5 border border-primary/20 p-6 flex items-center justify-between rounded-sm relative overflow-hidden group shadow-lg">
                  <div className="flex gap-4 items-center relative z-10">
                      <div className="w-12 h-12 bg-primary/20 rounded-sm flex items-center justify-center shrink-0 text-primary">
                         <Construction size={24} />
                      </div>
                      <div>
                         <p className="text-[10px] text-primary font-bold uppercase tracking-widest leading-tight">Média Global do Portfólio</p>
                         <p className="text-[10px] text-on-surface-variant uppercase tracking-[0.2em] mt-1">Nível de Execução Custo-Incorrido</p>
                      </div>
                  </div>
                  <div className="flex items-center gap-6 relative z-10">
                      <div className="w-64 h-2 bg-surface-container rounded-full overflow-hidden shadow-inner">
                          <div className="h-full bg-primary shadow-[0_0_10px_rgba(var(--color-primary),0.5)] transition-all duration-1000" style={{width: `${pocData.length > 0 ? (pocData.reduce((acc, curr) => acc + curr.percentual, 0) / pocData.length).toFixed(1) : 0}%`}}></div>
                      </div>
                      <h3 className="text-5xl font-headline font-black text-primary">
                          {pocData.length > 0 ? (pocData.reduce((acc, curr) => acc + curr.percentual, 0) / pocData.length).toFixed(1) : '0.0'}%
                      </h3>
                  </div>
               </div>

               <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                 {/* Lado Esquerdo - Formulário Lista */}
                 <div className="bg-surface-container-lowest border border-outline-variant/20 rounded-sm overflow-hidden flex flex-col shadow-xl">
                    <div className="p-6 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-low">
                       <div>
                         <h3 className="text-sm font-headline font-bold text-on-surface uppercase tracking-[0.2em] flex items-center gap-2"><PieChart size={16} className="text-primary"/> Tabela de Avaliação (WIP)</h3>
                         <p className="text-[9px] text-on-surface-variant tracking-[0.3em] uppercase mt-2">Ponto Focal: Obra a Obra</p>
                       </div>
                    </div>
                    <div className="overflow-y-auto max-h-[600px] p-0">
                      <table className="w-full text-left border-collapse text-xs whitespace-nowrap font-body">
                         <thead className="sticky top-0 z-10">
                           <tr>
                              <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-r border-outline-variant/10 text-[10px] bg-surface-container-low">Empreendimento Ativo</th>
                              <th className="p-4 font-bold text-primary uppercase tracking-widest border-b border-r border-outline-variant/10 text-[10px] bg-primary/5 text-right w-[100px]">POC Gravado</th>
                              <th className="p-4 font-bold text-secondary uppercase tracking-widest border-b border-outline-variant/10 text-[10px] bg-secondary/5 text-center" colSpan={2}>Lançamento Ref.</th>
                           </tr>
                         </thead>
                         <tbody>
                            {uniqueEmpreendimentos.length > 0 ? uniqueEmpreendimentos.map((emp, i) => {
                               const projPoc = pocData.filter(p => p.empreendimento === emp).sort((a,b) => b.periodo.localeCompare(a.periodo))[0];
                               const pct = projPoc ? projPoc.percentual : 0;
                               if (pct >= 100) return null; // Esconde obras 100% finalizadas

                               return (
                                 <tr key={i} className="border-b border-outline-variant/10 hover:bg-surface-container-highest transition-colors">
                                    <td className="p-4 font-bold text-on-surface uppercase tracking-widest text-[11px] truncate max-w-[200px] border-r border-outline-variant/10" title={emp}>{emp}</td>
                                    <td className="p-4 text-primary font-mono font-black text-right border-r border-outline-variant/10">{pct.toFixed(2)}%</td>
                                    <td className="p-4 align-middle w-[150px] bg-secondary/5 border-b border-secondary/10">
                                       <div className="relative">
                                         <input type="number" step="0.01" value={pocDrafts[emp] !== undefined ? pocDrafts[emp] : ''} onChange={(e) => setPocDrafts(prev => ({...prev, [emp]: e.target.value}))} className="w-full bg-surface-container border border-outline-variant/30 p-2 text-right font-mono font-bold text-on-surface focus:border-secondary transition-colors outline-none rounded-sm shadow-inner" placeholder="Poc..." />
                                         <span className="absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/50 text-[10px] font-bold">%</span>
                                       </div>
                                    </td>
                                    <td className="p-4 align-middle text-right bg-secondary/5 border-b border-secondary/10 w-[80px]">
                                       <button onClick={(e) => handleSaveSinglePoc(emp, pocDrafts[emp])} disabled={loadingPoc[emp]} className="w-full bg-secondary text-on-secondary font-black uppercase tracking-[0.2em] text-[10px] px-3 h-[32px] rounded-sm hover:opacity-90 disabled:opacity-50 transition-opacity">
                                          {loadingPoc[emp] ? '...' : 'Salvar'}
                                       </button>
                                    </td>
                                 </tr>
                               )
                            }) : <tr><td colSpan={4} className="p-8 text-center text-on-surface-variant tracking-widest uppercase text-[10px]">A matriz não encontrou projetos não-finalizados.</td></tr>}
                         </tbody>
                      </table>
                    </div>
                 </div>

                 {/* Lado Direito - Tabela Histórico */}
                 <div className="bg-surface-container-lowest border border-outline-variant/20 rounded-sm overflow-hidden flex flex-col shadow-xl">
                    <div className="p-6 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-low">
                       <div>
                         <h3 className="text-sm font-headline font-bold text-on-surface uppercase tracking-[0.2em] flex items-center gap-2"><ArrowUpRight size={16} className="text-tertiary"/> Ledger Global (POC)</h3>
                         <p className="text-[9px] text-on-surface-variant tracking-[0.3em] uppercase mt-2">Log Direto da API Firebird</p>
                       </div>
                    </div>
                    <div className="overflow-auto max-h-[600px] p-0">
                      <table className="w-full text-left border-collapse text-xs whitespace-nowrap font-body">
                         <thead className="sticky top-0 z-10">
                           <tr>
                             <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-lowest text-[10px]">Ocorrência</th>
                             <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-lowest text-[10px]">Empreendimento</th>
                             <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-lowest text-[10px]">Mês Ref.</th>
                             <th className="p-4 font-bold text-primary uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-lowest text-[10px] text-right">Evolução %</th>
                             <th className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 bg-surface-container-lowest text-[10px] text-center">Auditoria</th>
                           </tr>
                         </thead>
                         <tbody>
                            {pocData.map((row, idx) => (
                              <tr key={idx} className="border-b border-outline-variant/5 bg-surface-container hover:bg-surface-container-highest transition-colors group">
                                <td className="p-4 text-on-surface-variant font-mono text-[9px]">Histórico Batch</td>
                                <td className="p-4 text-on-surface font-bold uppercase tracking-widest text-[10px] truncate max-w-[150px]">{row.empreendimento}</td>
                                <td className="p-4 text-on-surface-variant font-mono text-[10px]">{row.periodo}</td>
                                <td className="p-4 font-black text-primary font-mono tracking-tight text-right">{row.percentual.toFixed(2)}%</td>
                                <td className="p-4 text-center">
                                  <span className="px-2 py-1 bg-tertiary-container/30 text-tertiary rounded-sm uppercase tracking-widest border border-tertiary/20 text-[8px] font-bold">Consolidado</span>
                                </td>
                              </tr>
                            ))}
                            {pocData.length === 0 && (
                              <tr><td colSpan={5} className="p-8 text-center text-on-surface-variant tracking-widest uppercase text-[10px]">Audit Log Vazio. Inicie uma nova campanha de preenchimento.</td></tr>
                            )}
                         </tbody>
                      </table>
                    </div>
                 </div>
               </div>
             </div>
           )}"""

if old_poc_view_pattern.search(app_code):
    app_code = old_poc_view_pattern.sub(new_poc_view, app_code)
    print("SUCCESS VIEW POC")
else:
    print("FAILED TO MATCH VIEW POC")

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)
