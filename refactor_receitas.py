import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Make sure we add necessary icons
required_icons = ['TrendingUp', 'Landmark', 'Activity', 'Receipt', 'AlertCircle', 'Calendar']
for icon in required_icons:
    if icon not in app_code:
        app_code = app_code.replace("import { Search,", f"import {{ Search, {icon},")

receitas_pattern = re.compile(
    r"\{\s*/\*\s*Outras telas \(Auditoria ERP, Receitas, Questor Schema\)\s*\*/\s*\}(.*?)\{\s*/\*\s*ROTEAMENTO DE OUTRAS VIEWS\s*\*/\s*\}",
    re.DOTALL
)

new_receitas_block = """
           {/* Outras telas (Auditoria ERP, Receitas, Questor Schema) */}
           {currentView === 'receitas' && (
             <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full pb-20">
               
               {/* Header / Configuração */}
               <div className="flex justify-between items-end bg-surface-container-lowest p-6 rounded-sm border border-outline-variant/10 shadow-sm">
                 <div>
                   <h2 className="font-headline text-3xl font-bold text-on-surface tracking-tight uppercase">Dashboard Gerencial</h2>
                   <p className="text-on-surface-variant font-body text-[10px] mt-1 uppercase tracking-[0.2em] font-bold">Visão Consolidada de Operações & Tributos • {receitaGlobal > 0 ? 'Sincronizado' : 'Aguardando'}</p>
                 </div>
                 <div className="flex gap-4 items-end">
                   <div className="flex flex-col">
                     <label className="text-[9px] text-on-surface-variant font-bold uppercase tracking-widest mb-2 flex items-center gap-1"><Calendar size={12}/> Competência Acumulativo</label>
                     <input type="month" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="bg-surface-container border border-outline-variant/20 text-on-surface p-2 rounded-sm outline-none focus:border-primary/50 text-xs font-mono uppercase transition-colors h-[40px] w-48 shadow-inner" />
                   </div>
                   <button onClick={fetchReceitas} className="bg-primary-container text-on-primary-container font-black uppercase text-[10px] tracking-widest px-8 h-[40px] rounded-sm hover:opacity-90 transition-opacity flex items-center gap-2">
                      <Activity size={14} /> Sincronizar
                   </button>
                 </div>
               </div>

               {/* Bento Grid Top KPIs */}
               <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 w-full">
                 {/* KPI 1 */}
                 <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><TrendingUp size={64}/></div>
                    <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Receita / VGV Total</span>
                    <h4 className="text-3xl font-headline font-black text-on-surface mb-2 relative z-10">{formatCurrency(receitaGlobal)}</h4>
                    <p className="text-[9px] text-on-surface-variant uppercase tracking-widest font-bold mt-auto pt-4 border-t border-outline-variant/10 relative z-10">VGV Consolidado</p>
                 </div>
                 {/* KPI 2 */}
                 <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Receipt size={64}/></div>
                    <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">PIS/COFINS + IRPJ/CSLL</span>
                    <h4 className="text-3xl font-headline font-black text-error mb-2 relative z-10">{formatCurrency(totalPisCofins + totalIrpjCsll)}</h4>
                    <p className="text-[9px] text-error uppercase tracking-widest font-bold mt-auto pt-4 border-t border-error/20 relative z-10">Custo Estimado Oficial</p>
                 </div>
                 {/* KPI 3 */}
                 <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Landmark size={64}/></div>
                    <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Total RET (4%)</span>
                    <h4 className="text-3xl font-headline font-black text-secondary mb-2 relative z-10">{formatCurrency(totalRetMacro)}</h4>
                    <p className="text-[9px] text-secondary uppercase tracking-widest font-bold mt-auto pt-4 border-t border-secondary/20 relative z-10">Provisão RET Questor</p>
                 </div>
                 {/* KPI 4 */}
                 <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Building2 size={64}/></div>
                    <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Receita Societária</span>
                    <h4 className="text-3xl font-headline font-black text-tertiary mb-2 relative z-10">{formatCurrency(totalSocietario)}</h4>
                    <p className="text-[9px] text-tertiary uppercase tracking-widest font-bold mt-auto pt-4 border-t border-tertiary/20 relative z-10">Aprovado p/ Diretoria (POC)</p>
                 </div>
               </div>

               {/* Painel de Controladoria em Tempo Real (Tabela Principal) */}
               <div className="bg-surface-container-lowest border border-outline-variant/20 rounded-sm">
                 <div className="p-6 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-low">
                   <div>
                     <h3 className="text-sm font-headline font-bold text-on-surface uppercase tracking-[0.2em] flex items-center gap-2"><Activity size={16} className="text-primary"/> Controladoria Corporativa</h3>
                     <p className="text-[9px] text-on-surface-variant tracking-[0.3em] uppercase mt-2">Comparativo de Regras: Societária (POC) vs Fiscal (Caixa)</p>
                   </div>
                   <div className="flex bg-surface-container p-1 rounded-sm">
                      <span className="text-[9px] px-3 py-1 font-bold uppercase tracking-widest text-on-surface-variant">Modo Analítico</span>
                   </div>
                 </div>
                 
                 <div className="overflow-x-auto w-full p-0">
                   <table className="w-full text-left border-collapse text-xs whitespace-nowrap font-body">
                     <thead>
                       <tr>
                         <th rowSpan="2" className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-r border-outline-variant/10 bg-surface-container-lowest text-[10px]">Unidade de Negócio</th>
                         <th colSpan="2" className="p-3 font-bold text-primary uppercase tracking-widest text-center border-b border-r border-outline-variant/10 bg-primary/5 text-[10px]">Tributação Base Caixa</th>
                         <th colSpan="4" className="p-3 font-bold text-secondary uppercase tracking-widest text-center border-b border-outline-variant/10 bg-secondary/5 text-[10px]">Reconhecimento POC (Societário)</th>
                       </tr>
                       <tr>
                         {/* Fiscal Columns */}
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-primary/5 text-[9px]">Faturamento Bruto</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-r border-outline-variant/10 text-right bg-primary/5 text-[9px]">Despesa Tributária</th>
                         
                         {/* Societario Columns */}
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Avanço Global (%)</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Receita Computada</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Despesa Tributária</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-[0.2em] border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Cálculo IFRS (Ativo/Passivo)</th>
                       </tr>
                     </thead>
                     <tbody>
                       {aggregatedReceitas.length > 0 ? aggregatedReceitas.map((agg, i) => {
                          const impostoFiscal = agg.tributos_total;
                          const liquidoFiscal = agg.receita_caixa - impostoFiscal;
                          const recSocietaria = agg.receita_societaria;
                          const impostoSocietario = agg.tributos_societario;
                          const diferimento = agg.receita_caixa - recSocietaria;
                          const isExpanded = expandedEmps[agg.empreendimento];
                          
                          return (
                          <React.Fragment key={i}>
                            <tr onClick={() => toggleEmp(agg.empreendimento)} className="border-b border-outline-variant/10 bg-surface-container hover:bg-surface-container-highest cursor-pointer transition-colors group">
                              <td className="p-4 font-bold text-on-surface border-r border-outline-variant/10 flex items-center justify-between">
                                 <span className="uppercase tracking-widest text-[11px] group-hover:text-primary transition-colors">{agg.empreendimento}</span>
                                 <span className="text-on-surface-variant text-[9px] font-bold">{isExpanded ? '▼ OCULTAR' : '▶ EXPLORAR'}</span>
                              </td>
                              <td className="p-4 text-right text-primary font-black font-mono tracking-tight">{formatCurrency(agg.receita_caixa)}</td>
                              <td className="p-4 text-right text-error font-bold border-r border-outline-variant/10 font-mono tracking-tight">-{formatCurrency(impostoFiscal)}</td>
                              
                              <td className="p-4 text-right text-on-surface-variant font-bold font-mono bg-surface-container-lowest/50">{agg.poc.toFixed(2)}%</td>
                              <td className="p-4 text-right text-secondary font-black font-mono tracking-tight bg-surface-container-lowest/50">{formatCurrency(recSocietaria)}</td>
                              <td className="p-4 text-right text-error font-bold font-mono tracking-tight bg-surface-container-lowest/50">-{formatCurrency(impostoSocietario)}</td>
                              <td className={`p-4 text-right font-black font-mono tracking-tight bg-surface-container-lowest/50 ${diferimento > 0 ? 'text-secondary' : diferimento < 0 ? 'text-error' : 'text-on-surface-variant'}`}>
                                {diferimento > 0 ? `+${formatCurrency(diferimento)} (Passivo)` : diferimento < 0 ? `${formatCurrency(diferimento)} (Ativo)` : '-'}
                              </td>
                            </tr>
                            {isExpanded && agg.unidades.map((u, j) => {
                                const pDiferimento = (u.receita_caixa || 0) - (u.receita_societaria || 0);
                                return (
                                <tr key={`u-${j}`} className="border-b border-outline-variant/5 bg-surface-container-lowest">
                                   <td className="p-3 pl-8 border-r border-outline-variant/10">
                                       <div className="flex flex-col">
                                          <span className="text-tertiary font-bold text-[10px] uppercase tracking-widest">{u.unidade}</span>
                                          <span className="text-on-surface-variant/50 text-[9px] break-all block w-full uppercase" title={u.comprador}>{u.comprador || "CLIENTE NÃO INFORMADO"}</span>
                                       </div>
                                   </td>
                                   <td className="p-3 text-right">
                                        <div className="text-on-surface font-bold font-mono tracking-tight">{formatCurrency(u.receita_caixa)}</div>
                                        <div className="text-[9px] text-on-surface-variant uppercase tracking-widest">Acu: {formatCurrency(u.caixa_acumulado || 0)}</div>
                                    </td>
                                    <td className="p-3 text-right text-error font-bold text-[10px] border-r border-outline-variant/10">
                                        <div className="flex flex-col font-mono tracking-tight">
                                           <span>-{formatCurrency(u.tributos_total)}</span>
                                           <span className="text-on-surface-variant/50">Acu: -{formatCurrency(u.tributos_caixa_acumulado || 0)}</span>
                                        </div>
                                    </td>
                                    <td className="p-3 text-right text-on-surface-variant font-mono">{u.poc.toFixed(2)}%</td>
                                    <td className="p-3 text-right">
                                        <div className="text-secondary font-bold font-mono tracking-tight">{formatCurrency(u.soc_acumulado || 0)}</div>
                                        <div className="text-[9px] text-on-surface-variant uppercase tracking-widest">Mês: {formatCurrency(u.receita_societaria || 0)}</div>
                                    </td>
                                    <td className="p-3 text-right text-error font-bold text-[10px]">
                                        <div className="flex flex-col font-mono tracking-tight">
                                           <span>-{formatCurrency(u.tributos_soc_acumulado || 0)}</span>
                                           <span className="text-on-surface-variant/50">Mês: -{formatCurrency(u.tributos_societario || 0)}</span>
                                        </div>
                                    </td>
                                    <td className={`p-3 text-right text-[10px] font-bold font-mono tracking-tight ${((u.caixa_acumulado||0) - (u.soc_acumulado||0)) > 0 ? 'text-secondary' : 'text-error'}`}>
                                        {formatCurrency((u.caixa_acumulado||0) - (u.soc_acumulado||0))}
                                    </td>
                                </tr>
                                )
                            })}
                            {isExpanded && (
                               <tr className="bg-surface-container text-center"><td colSpan={8} className="p-4 border-b border-outline-variant/10"><button onClick={() => setLedgerModalData({emp: agg.empreendimento, context: 'receitas', data: null})} className="inline-flex items-center gap-2 bg-primary-container hover:opacity-90 text-on-primary-container px-6 py-3 rounded-sm uppercase tracking-[0.2em] text-[10px] font-black transition-all">Analisar Livro Razão D/C</button></td></tr>
                            )}
                          </React.Fragment>
                        )}) : <tr><td colSpan={8} className="text-center p-12 text-on-surface-variant tracking-widest uppercase text-xs">Aguardando telemetria fiscal.</td></tr>}
                     </tbody>
                   </table>
                 </div>
               </div>

               {/* MÓDULO CONTÁBIL BENTO GRID */}
               <div className="bg-surface-container-low border border-outline-variant/10 rounded-sm p-8 mt-8 mx-auto w-full max-w-7xl animate-in fade-in slide-in-from-bottom-4 shadow-xl">
                 <div className="flex items-center justify-between mb-8 pb-6 border-b border-outline-variant/10">
                   <div>
                       <h3 className="text-lg font-headline font-bold tracking-[0.2em] uppercase text-on-surface flex items-center gap-3">
                         <div className="p-2 bg-tertiary-container text-on-tertiary-container rounded-sm"><Activity size={18}/></div>
                         Motor de Contabilização Oculto
                       </h3>
                       <p className="text-[10px] text-on-surface-variant uppercase tracking-widest mt-2 ml-11">Mapeamento Duplo de Fechamento (Cash vs Accrual Basis)</p>
                   </div>
                   {selectedEmpresa === "959" && <span className="bg-tertiary/10 text-tertiary px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] rounded-sm border border-tertiary/20 flex items-center gap-2"><AlertCircle size={14}/> Mapeamento Questor 959 Ativo</span>}
                 </div>

                 {receitasData.length === 0 ? (
                   <div className="text-center p-8 text-on-surface-variant text-[10px] uppercase tracking-widest border border-dashed border-outline-variant/30 rounded-sm">Motor Suspenso - Sem Dados Alocados</div>
                 ) : (
                   <div className="space-y-12">
                      {(() => {
                         const empNames = window.dashboard_meta ? Object.keys(window.dashboard_meta) : [];
                         if (empNames.length === 0) return <div className="text-center p-8 text-on-surface-variant/50 text-xs">Falha na consolidação matriz.</div>;

                         let totalSocMes = 0;
                         let totalCaixaMes = 0;
                         
                         empNames.forEach(emp => {
                            const m = window.dashboard_meta[emp];
                            if (m) {
                               totalSocMes += m.receita_soc_mes || 0;
                               totalCaixaMes += m.caixa_mes || 0;
                            }
                         });
                         
                         const renderMovimentoMensal = (valCaixa, valSoc) => {
                             const diferimento = valCaixa - valSoc;
                             const isPassivo = diferimento > 0;
                             return (
                               <div className="border border-outline-variant/20 rounded-sm p-6 bg-surface-container-lowest">
                                 <h4 className="text-tertiary font-headline font-bold text-xs tracking-[0.2em] uppercase mb-1">Log de Movimentos Consolidados</h4>
                                 <p className="text-[10px] text-on-surface-variant mb-6 tracking-widest uppercase pb-4 border-b border-outline-variant/10">Plano de Contas Oficial em Vigor (Geral)</p>
                                 
                                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                   {/* LANÇAMENTO FISCAL / CAIXA */}
                                   <div className="space-y-3 bg-surface-container-low p-5 rounded-sm border border-outline-variant/10">
                                     <div className="border-b border-outline-variant/20 pb-2 mb-3">
                                        <span className="text-on-surface-variant font-bold text-[10px] uppercase tracking-[0.2em] flex items-center gap-2"><Receipt size={14} className="text-primary"/> Fato 1: Evento Fiscal (Caixa Mensal)</span>
                                     </div>
                                     <table className="w-full text-xs text-left">
                                       <tbody className="font-mono text-[10px]">
                                          <tr className="hover:bg-surface-container transition-colors">
                                             <td className="py-2 px-2 text-secondary font-black w-8 border-r border-outline-variant/10">D</td>
                                             <td className="py-2 px-3 text-on-surface-variant truncate max-w-[150px]">{selectedEmpresa === "959" && questorContas ? (questorContas.find(c => c.descricao.includes('BANCO'))?.classificacao || '1.1.1.02') + ' - Bancos / Caixa' : 'Bancos / Caixa (Ativo)'}</td>
                                             <td className="py-2 px-2 text-right text-secondary font-bold tracking-tight">{formatCurrency(valCaixa)}</td>
                                          </tr>
                                          <tr className="hover:bg-surface-container transition-colors border-t border-outline-variant/5">
                                             <td className="py-2 px-2 text-error font-black border-r border-outline-variant/10">C</td>
                                             <td className="py-2 px-3 text-on-surface-variant truncate max-w-[150px]">{selectedEmpresa === "959" && questorContas ? (questorContas.find(c => c.descricao.includes('ANTECIPAD'))?.classificacao || '5666') + ' - Adiantamentos de Clientes' : 'Adiantamentos de Clientes'}</td>
                                             <td className="py-2 px-2 text-right text-error font-bold tracking-tight">{formatCurrency(valCaixa)}</td>
                                          </tr>
                                       </tbody>
                                     </table>
                                   </div>

                                   {/* LANÇAMENTO SOCIETARIO / POC */}
                                   <div className="space-y-3 bg-surface-container-low p-5 rounded-sm border border-outline-variant/10">
                                     <div className="border-b border-outline-variant/20 pb-2 mb-3">
                                        <span className="text-on-surface-variant font-bold text-[10px] uppercase tracking-[0.2em] flex items-center gap-2"><Building2 size={14} className="text-tertiary"/> Fato 2: Reconhecimento Competência (Evolução Físico-Financeira)</span>
                                     </div>
                                     <table className="w-full text-xs text-left">
                                       <tbody className="font-mono text-[10px]">
                                          <tr className="hover:bg-surface-container transition-colors">
                                             <td className="py-2 px-2 text-secondary font-black w-8 border-r border-outline-variant/10">D</td>
                                             <td className="py-2 px-3 text-on-surface-variant truncate max-w-[150px]">{selectedEmpresa === "959" && questorContas ? (questorContas.find(c => c.descricao.includes('CLIENTE'))?.classificacao || '1.1.2.01') + ' - Clientes Obras' : 'Clientes (Ativo)'}</td>
                                             <td className="py-2 px-2 text-right text-secondary font-bold tracking-tight">{formatCurrency(valSoc)}</td>
                                          </tr>
                                          <tr className="hover:bg-surface-container transition-colors border-t border-outline-variant/5">
                                             <td className="py-2 px-2 text-error font-black border-r border-outline-variant/10">C</td>
                                             <td className="py-2 px-3 text-on-surface-variant truncate max-w-[150px]">{selectedEmpresa === "959" && questorContas ? (questorContas.find(c => c.descricao.includes('RECEITA'))?.classificacao || '3.1.1.01') + ' - Receitas de Obras' : 'Receita de Obras (Resultado)'}</td>
                                             <td className="py-2 px-2 text-right text-error font-bold tracking-tight">{formatCurrency(valSoc)}</td>
                                          </tr>
                                       </tbody>
                                     </table>
                                   </div>
                                 </div>
                               </div>
                             );
                         };

                         return renderMovimentoMensal(totalCaixaMes, totalSocMes);
                      })()}
                   </div>
                 )}
               </div>
             </div>
           )}
           {/* ROTEAMENTO DE OUTRAS VIEWS */}
"""

app_code = receitas_pattern.sub(new_receitas_block, app_code)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Receitas refactor finished!")
