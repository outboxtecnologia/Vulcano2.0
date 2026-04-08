import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

pattern = re.compile(
    r'<h2 className="text-4xl font-bold tracking-tighter uppercase mb-2 text-\[var\(--v-text-bold\)\]">Dashboard de Receitas</h2>.*?Aprovado Diretoria</p>\s*</div>\s*</div>',
    re.DOTALL
)

new_chunk = """<h2 className="font-headline text-3xl font-bold text-on-surface tracking-tight uppercase">Dashboard Gerencial</h2>
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
                   <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><TrendingUp size={64}/></div>
                      <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Receita Total / VGV</span>
                      <h4 className="text-3xl font-headline font-black text-on-surface mb-2 relative z-10">{formatCurrency(receitaGlobal)}</h4>
                      <p className="text-[9px] text-on-surface-variant uppercase tracking-widest font-bold mt-auto pt-4 border-t border-outline-variant/10 relative z-10">VGV Consolidado</p>
                   </div>
                   <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Receipt size={64}/></div>
                      <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">PIS/COFINS e IRPJ/CSLL</span>
                      <h4 className="text-3xl font-headline font-black text-error mb-2 relative z-10">{formatCurrency(totalPisCofins + totalIrpjCsll)}</h4>
                      <p className="text-[9px] text-error uppercase tracking-widest font-bold mt-auto pt-4 border-t border-error/20 relative z-10">• Custo Estimado</p>
                   </div>
                   <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Landmark size={64}/></div>
                      <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Total RET (4%)</span>
                      <h4 className="text-3xl font-headline font-black text-secondary mb-2 relative z-10">{formatCurrency(totalRetMacro)}</h4>
                      <p className="text-[9px] text-secondary uppercase tracking-widest font-bold mt-auto pt-4 border-t border-secondary/20 relative z-10">Consolidado Questor</p>
                   </div>
                   <div className="bg-surface-container-low border border-outline-variant/10 p-6 flex flex-col group hover:bg-surface-container transition-colors rounded-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity"><Activity size={64}/></div>
                      <span className="text-primary font-headline text-[10px] font-bold uppercase tracking-widest mb-6 relative z-10">Receita Societária</span>
                      <h4 className="text-3xl font-headline font-black text-tertiary mb-2 relative z-10">{formatCurrency(totalSocietario)}</h4>
                      <p className="text-[9px] text-tertiary uppercase tracking-widest font-bold mt-auto pt-4 border-t border-tertiary/20 relative z-10">Aprovado Diretoria</p>
                   </div>
                 </div>"""

app_code, count = pattern.subn(new_chunk, app_code)
if count > 0:
    print("SUCCESS Header")
    
    # Also fix the outer container slightly, finding 'max-w-7xl mx-auto'
    app_code = app_code.replace('className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full"', 'className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto w-full pb-20"')
    
    # Also fix the Top Header layout container which originally was:
    app_code = app_code.replace('<div className="flex justify-between items-end">', '<div className="flex justify-between items-end bg-surface-container-lowest p-6 rounded-sm border border-outline-variant/10 shadow-sm">', 1)
    
else:
    print("FAILED")

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)
