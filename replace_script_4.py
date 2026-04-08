import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

# 1. Add filterStartDate state
app_code = app_code.replace(
    "// Receitas State\n",
    "// Receitas State\n  const [filterStartDate, setFilterStartDate] = useState('');\n"
)

# 2. Fix isDateInRange
old_isDate = """  const isDateInRange = (periodo, start, end) => {
    if (!periodo) return true;
    const pStr = typeof periodo === 'string' ? periodo.substring(0, 7) : periodo.toString().substring(0, 7);
    // Filtro Mestre de Competência Acumulada: Tudo antes da data final é aceito.
    if (end) return pStr <= end;
    return true;
  };"""

new_isDate = """  const isDateInRange = (periodo, start, end) => {
    if (!periodo) return true;
    const pStr = typeof periodo === 'string' ? periodo.substring(0, 7) : periodo.toString().substring(0, 7);
    if (start && pStr < start) return false;
    if (end && pStr > end) return false;
    return true;
  };"""
app_code = app_code.replace(old_isDate, new_isDate)

# 3. Add totalTributosSocietarios
old_tot_soc = "const totalSocietario = Object.values(window.dashboard_meta || {}).reduce((acc, m) => acc + (m.receita_societaria || 0), 0);"
new_tot_soc = """const totalSocietario = Object.values(window.dashboard_meta || {}).reduce((acc, m) => acc + (m.receita_societaria || 0), 0);
  const totalTributosSocietarios = Object.values(window.dashboard_meta || {}).reduce((acc, m) => acc + (m.tributos_societarios || m.tributos_societario || 0), 0);"""
app_code = app_code.replace(old_tot_soc, new_tot_soc)

# 4. Update Header and KPI grids (including filterStartDate input and 5th card)
app_code = app_code.replace(
    '<h2 className="font-headline text-3xl font-bold text-on-surface tracking-tight uppercase">Dashboard Gerencial</h2>',
    '<h2 className="font-headline text-3xl font-bold text-on-surface tracking-tight uppercase">Dashboard Contábil</h2>'
)

old_inputs = """<label className="text-[9px] text-on-surface-variant font-bold uppercase tracking-widest mb-2 flex items-center gap-1"><Calendar size={12}/> Competência Acumulativo</label>
                       <input type="month" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="bg-surface-container border border-outline-variant/20 text-on-surface p-2 rounded-sm outline-none focus:border-primary/50 text-xs font-mono uppercase transition-colors h-[40px] w-48 shadow-inner" />"""
new_inputs = """<label className="text-[9px] text-on-surface-variant font-bold uppercase tracking-widest mb-2 flex items-center gap-1"><Calendar size={12}/> Período de Apuração</label>
                       <div className="flex items-center gap-2">
                         <input type="month" value={filterStartDate} onChange={e => setFilterStartDate(e.target.value)} className="bg-surface-container border border-outline-variant/20 text-on-surface p-2 rounded-sm outline-none focus:border-primary/50 text-[10px] font-mono uppercase transition-colors h-[40px] w-32 shadow-inner" title="Data Inicial (em branco = Acumulado)" />
                         <span className="text-on-surface-variant text-[10px] uppercase font-bold tracking-widest">Até</span>
                         <input type="month" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="bg-surface-container border border-outline-variant/20 text-on-surface p-2 rounded-sm outline-none focus:border-primary/50 text-[10px] font-mono uppercase transition-colors h-[40px] w-32 shadow-inner" title="Data Final" />
                       </div>"""
app_code = app_code.replace(old_inputs, new_inputs)

app_code = app_code.replace(
    '<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 w-full">',
    '<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6 w-full">'
)

kpi_5 = """<div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Activity size={64}/></div>
                      <span className="text-error font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Tributação Societária</span>
                      <h4 className="text-3xl font-headline font-black text-error mb-2 relative z-10">-{formatCurrency(totalTributosSocietarios)}</h4>
                      <p className="text-[9px] text-error uppercase tracking-widest font-bold mt-auto pt-4 border-t border-error/20 relative z-10">Provisão Competência</p>
                   </div>
                 </div>"""
app_code = app_code.replace('Aprovado Diretoria</p>\n                   </div>\n                 </div>', 'Aprovado Diretoria</p>\n                   </div>\n                   ' + kpi_5)

# 5. Fix the Controladoria Table UI
old_table_pattern = re.compile(r'<div className="magma-card p-8 rounded-sm">(.*?)</tbody>\s*</table>\s*</div>\s*</div>', re.DOTALL)
new_table_block = """<div className="bg-surface-container-lowest border border-outline-variant/20 rounded-sm">
                 <div className="p-6 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-low">
                   <div>
                     <h3 className="text-sm font-headline font-bold text-on-surface uppercase tracking-[0.2em] flex items-center gap-2"><Activity size={16} className="text-primary"/> Controladoria Corporativa</h3>
                     <p className="text-[9px] text-on-surface-variant tracking-[0.3em] uppercase mt-2">Comparativo Dinâmico DRE: Societária (POC) vs Fiscal (Caixa)</p>
                   </div>
                 </div>
                 
                 <div className="overflow-x-auto w-full p-0">
                   <table className="w-full text-left border-collapse text-xs whitespace-nowrap font-body">
                     <thead>
                       <tr>
                         <th rowSpan="2" className="p-4 font-bold text-on-surface-variant uppercase tracking-widest border-b border-r border-outline-variant/10 bg-surface-container-lowest text-[10px] w-[250px]">Unidade de Negócio</th>
                         <th colSpan="2" className="p-3 font-bold text-primary uppercase tracking-widest text-center border-b border-r border-outline-variant/10 bg-primary/5 text-[10px]">Tributação Base Caixa</th>
                         <th colSpan="4" className="p-3 font-bold text-secondary uppercase tracking-widest text-center border-b border-outline-variant/10 bg-secondary/5 text-[10px]">Reconhecimento POC (Societário)</th>
                       </tr>
                       <tr>
                         {/* Fiscal Columns */}
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-primary/5 text-[9px]">Faturamento Bruto</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-r border-outline-variant/10 text-right bg-primary/5 text-[9px]">Impostos Declarados</th>
                         
                         {/* Societario Columns */}
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Avanço (POC)</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Receita Computada</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px]">Provisão Tributária</th>
                         <th className="p-3 font-bold text-on-surface-variant uppercase tracking-[0.2em] border-b border-outline-variant/10 text-right bg-secondary/5 text-[9px] w-[200px]">Auditoria Passivo/Ativo IFRS</th>
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
                                 <span className="uppercase tracking-widest text-[11px] group-hover:text-primary transition-colors truncate max-w-[200px]">{agg.empreendimento}</span>
                                 <span className="text-on-surface-variant text-[9px] font-bold">{isExpanded ? '▼' : '▶'}</span>
                              </td>
                              <td className="p-4 text-right text-primary font-black font-mono tracking-tight">{formatCurrency(agg.receita_caixa)}</td>
                              <td className="p-4 text-right border-r border-outline-variant/10 align-top">
                                 <div className="flex flex-col items-end">
                                    <span className="text-error font-bold font-mono tracking-tight text-sm">-{formatCurrency(impostoFiscal)}</span>
                                    <span className="text-[8px] text-on-surface-variant font-mono uppercase opacity-70">PIS: {formatCurrency(agg.pis)} | COF: {formatCurrency(agg.cofins)}</span>
                                    <span className="text-[8px] text-on-surface-variant font-mono uppercase opacity-70">IR: {formatCurrency(agg.irpj)} | CS: {formatCurrency(agg.csll)} | RET: {formatCurrency(agg.ret||0)}</span>
                                 </div>
                              </td>
                              
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
                                          <span className="text-on-surface-variant/50 text-[9px] break-all block w-full uppercase truncate max-w-[180px]" title={u.comprador}>{u.comprador || "CLIENTE NÃO INFORMADO"}</span>
                                       </div>
                                   </td>
                                   <td className="p-3 text-right">
                                        <div className="text-on-surface font-bold font-mono tracking-tight">{formatCurrency(u.receita_caixa)}</div>
                                        <div className="text-[9px] text-on-surface-variant uppercase tracking-widest">Acu: {formatCurrency(u.caixa_acumulado || 0)}</div>
                                    </td>
                                    <td className="p-3 text-right border-r border-outline-variant/10 align-top">
                                        <div className="flex flex-col items-end">
                                           <span className="text-error font-bold font-mono tracking-tight">-{formatCurrency(u.tributos_total)}</span>
                                           <span className="text-[8px] text-on-surface-variant font-mono uppercase opacity-70">Acu: -{formatCurrency(u.tributos_caixa_acumulado || 0)}</span>
                                        </div>
                                    </td>
                                    <td className="p-3 text-right text-on-surface-variant font-mono">{u.poc.toFixed(2)}%</td>
                                    <td className="p-3 text-right">
                                        <div className="text-secondary font-bold font-mono tracking-tight">{formatCurrency(u.soc_acumulado || 0)}</div>
                                        <div className="text-[9px] text-on-surface-variant uppercase tracking-widest">Mês: {formatCurrency(u.receita_societaria || 0)}</div>
                                    </td>
                                    <td className="p-3 text-right text-error font-bold text-[10px] align-top">
                                        <div className="flex flex-col items-end">
                                           <span className="text-error font-bold font-mono tracking-tight">-{formatCurrency(u.tributos_soc_acumulado || 0)}</span>
                                           <span className="text-[8px] text-on-surface-variant font-mono uppercase opacity-70">Mês: -{formatCurrency(u.tributos_societario || 0)}</span>
                                        </div>
                                    </td>
                                    <td className={`p-3 text-right text-[10px] font-bold font-mono tracking-tight ${((u.caixa_acumulado||0) - (u.soc_acumulado||0)) > 0 ? 'text-secondary' : 'text-error'}`}>
                                        {formatCurrency((u.caixa_acumulado||0) - (u.soc_acumulado||0))}
                                    </td>
                                </tr>
                                )
                            })}
                            {isExpanded && (
                               <tr className="bg-surface-container text-center"><td colSpan={8} className="p-4 border-b border-outline-variant/10"><button onClick={() => setLedgerModalData({emp: agg.empreendimento, context: 'receitas', data: null})} className="inline-flex items-center gap-2 bg-primary-container hover:opacity-90 text-on-primary-container px-6 py-3 rounded-sm uppercase tracking-[0.2em] text-[10px] font-black transition-all">Auditoria D/C Razão Auxiliar</button></td></tr>
                            )}
                          </React.Fragment>
                        )}) : <tr><td colSpan={8} className="text-center p-12 text-on-surface-variant tracking-widest uppercase text-xs">Sem dados no período apurado.</td></tr>}
                     </tbody>
                   </table>
                 </div>
               </div>"""

if old_table_pattern.search(app_code):
    app_code = old_table_pattern.sub(new_table_block, app_code)
    print("SUCCESS TABLE")
else:
    print("FAILED TO MATCH TABLE")

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)
