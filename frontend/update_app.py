import re

with open("src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update fetchReceitas to include dates
old_fetch_receitas = """
  const fetchReceitas = () => {
    setSelectedTable(null);
    setLoadingReceitas(true);
    const params = new URLSearchParams();
    if (selectedEmpresa) params.set('empresa_id', selectedEmpresa);
    fetch(`${API_BASE}/api/receitas-caixa?${params.toString()}`)
"""

new_fetch_receitas = """
  const fetchReceitas = () => {
    setSelectedTable(null);
    setLoadingReceitas(true);
    const params = new URLSearchParams();
    if (selectedEmpresa) params.set('empresa_id', selectedEmpresa);
    if (filterStartDate) params.set('data_ini', filterStartDate + "-01");
    if (filterEndDate) {
      // Pega último dia do mês para o data_fim
      const [y, m] = filterEndDate.split('-');
      const lastDay = new Date(y, m, 0).getDate();
      params.set('data_fim', `${filterEndDate}-${lastDay}`);
    }
    fetch(`${API_BASE}/api/receitas-caixa?${params.toString()}`)
"""
content = content.replace(old_fetch_receitas.strip(), new_fetch_receitas.strip())

# 2. Add expandedEmps and aggregatedReceitas, ensure they are before the main returns
# Find the line `const formatCurrency =`
agg_code = """
  const [expandedEmps, setExpandedEmps] = useState({});
  const toggleEmp = (emp) => setExpandedEmps(prev => ({...prev, [emp]: !prev[emp]}));

  const aggregatedReceitas = React.useMemo(() => {
      const map = {};
      filteredReceitasData.forEach(r => {
          const emp = r.empreendimento || "Sem Nome";
          if (!map[emp]) {
              map[emp] = {
                  empreendimento: emp,
                  receita_caixa: 0, receita_societaria: 0,
                  tributos_total: 0, tributos_societario: 0,
                  pis: 0, cofins: 0, irpj: 0, csll: 0, ret: 0,
                  poc: r.poc,
                  unidades: []
              };
          }
          let agg = map[emp];
          agg.receita_caixa += r.receita_caixa || 0;
          agg.receita_societaria += r.receita_societaria || 0;
          agg.tributos_total += r.tributos_total || 0;
          agg.tributos_societario += r.tributos_societario || 0;
          agg.pis += r.pis || 0;
          agg.cofins += r.cofins || 0;
          agg.irpj += r.irpj || 0;
          agg.csll += r.csll || 0;
          agg.unidades.push(r);
      });
      return Object.values(map);
  }, [filteredReceitasData]);

  const formatCurrency ="""
content = content.replace("  const formatCurrency =", agg_code)


# 3. Add Date inputs to the header of Dashboard Receitas
old_header = """
                <div className="flex justify-between items-end">
                  <div>
                    <h2 className="text-4xl font-bold tracking-tighter uppercase mb-2 text-white">Dashboard de Receitas</h2>
                    <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Visão Financeira Consolidada • {receitaGlobal > 0 ? 'Atualizado' : 'Buscando'}</p>
                  </div>
                </div>
"""
new_header = """
                <div className="flex justify-between items-end">
                  <div>
                    <h2 className="text-4xl font-bold tracking-tighter uppercase mb-2 text-white">Dashboard de Receitas</h2>
                    <p className="text-xs text-[#555] uppercase tracking-[0.3em]">Visão Financeira Consolidada • {receitaGlobal > 0 ? 'Atualizado' : 'Buscando'}</p>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex flex-col">
                      <label className="text-[10px] text-[#888] font-bold uppercase tracking-widest mb-1">Período Incial</label>
                      <input type="month" value={filterStartDate} onChange={e => setFilterStartDate(e.target.value)} className="bg-[#111] border border-[#222] text-[#ccc] p-2 rounded outline-none h-[40px]" />
                    </div>
                    <div className="flex flex-col">
                      <label className="text-[10px] text-[#888] font-bold uppercase tracking-widest mb-1">Período Final</label>
                      <input type="month" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="bg-[#111] border border-[#222] text-[#ccc] p-2 rounded outline-none h-[40px]" />
                    </div>
                    <button onClick={fetchReceitas} className="bg-[#ff4d00] text-black font-black uppercase text-xs tracking-widest px-6 h-[40px] mt-auto rounded hover:bg-[#ff5f1a]">Sincronizar</button>
                  </div>
                </div>
"""
content = content.replace(old_header.strip(), new_header.strip())


# 4. Replace the <tbody> of the table with the drill-down version
old_tbody = """
                      <tbody>
                        {filteredReceitasData.length > 0 ? filteredReceitasData.map((row, i) => {
                           const impostoFiscal = (row.pis || 0) + (row.cofins || 0) + (row.irpj || 0) + (row.csll || 0) + (row.ret || 0);
                           const liquidoFiscal = row.receita_caixa - impostoFiscal;
                           const recSocietaria = row.receita_societaria || 0;
                           const impostoSocietario = (row.receita_caixa > 0) ? (impostoFiscal / row.receita_caixa) * recSocietaria : 0;
                           const diferimento = row.receita_caixa - recSocietaria;
                           
                           return (
                           <tr key={i} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                             <td className="p-3 font-bold text-[#ccc] border-r border-[#333]">{row.empreendimento} <span className="text-[#555]">({row.unidade})</span></td>
                             
                             <td className="p-3 text-right text-[#ffcc00] font-black">{formatCurrency(row.receita_caixa)}</td>
                             <td className="p-3 text-right text-[#ff4d00] font-bold">-{formatCurrency(impostoFiscal)}</td>
                             <td className="p-3 text-right text-white font-bold border-r border-[#333]">{formatCurrency(liquidoFiscal)}</td>
                             
                             <td className="p-3 text-right text-[#555] font-bold">{row.poc}%</td>
                             <td className="p-3 text-right text-[#34c759] font-black">{formatCurrency(recSocietaria)}</td>
                             <td className="p-3 text-right text-[#ff4d00] font-bold">-{formatCurrency(impostoSocietario)}</td>
                             <td className={`p-3 text-right font-black ${diferimento > 0 ? 'text-[#00c2ff]' : diferimento < 0 ? 'text-[#ff4d00]' : 'text-[#555]'}`}>
                               {diferimento > 0 ? `+${formatCurrency(diferimento)} (Passivo)` : diferimento < 0 ? `${formatCurrency(diferimento)} (Ativo)` : '-'}
                             </td>
                           </tr>
                         )}) : <tr><td colSpan={8} className="text-center p-8 text-[#555] tracking-widest uppercase text-xs">Sem dados processados.</td></tr>}
                      </tbody>
"""

new_tbody = """
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
                             <tr onClick={() => toggleEmp(agg.empreendimento)} className="border-b border-[#111] bg-[#1a1a1a] hover:bg-[#222] cursor-pointer transition-colors">
                               <td className="p-3 font-bold text-white border-r border-[#333] flex items-center justify-between">
                                  <span>{agg.empreendimento}</span>
                                  <span className="text-[#888] text-[9px]">{isExpanded ? '▼ OCULTAR' : '▶ DETALHES'}</span>
                               </td>
                               <td className="p-3 text-right text-[#ffcc00] font-black">{formatCurrency(agg.receita_caixa)}</td>
                               <td className="p-3 text-right text-[#ff4d00] font-bold">-{formatCurrency(impostoFiscal)}</td>
                               <td className="p-3 text-right text-white font-bold border-r border-[#333]">{formatCurrency(liquidoFiscal)}</td>
                               
                               <td className="p-3 text-right text-[#555] font-bold">{agg.poc.toFixed(2)}%</td>
                               <td className="p-3 text-right text-[#34c759] font-black">{formatCurrency(recSocietaria)}</td>
                               <td className="p-3 text-right text-[#ff4d00] font-bold">-{formatCurrency(impostoSocietario)}</td>
                               <td className={`p-3 text-right font-black ${diferimento > 0 ? 'text-[#00c2ff]' : diferimento < 0 ? 'text-[#ff4d00]' : 'text-[#555]'}`}>
                                 {diferimento > 0 ? `+${formatCurrency(diferimento)} (Passivo)` : diferimento < 0 ? `${formatCurrency(diferimento)} (Ativo)` : '-'}
                               </td>
                             </tr>
                             {isExpanded && agg.unidades.map((u, j) => {
                                 const pDiferimento = (u.receita_caixa || 0) - (u.receita_societaria || 0);
                                 return (
                                 <tr key={`u-${j}`} className="border-b border-[#0a0a0a] bg-[#0b0b0b]">
                                    <td className="p-2 pl-8 border-r border-[#222]">
                                        <div className="flex flex-col">
                                           <span className="text-[#a259ff] font-bold text-[11px]">{u.unidade}</span>
                                           <span className="text-[#666] text-[9px] truncate max-w-[150px]">{u.comprador}</span>
                                        </div>
                                    </td>
                                    <td className="p-2 text-right text-[#aaa] font-bold">{formatCurrency(u.receita_caixa)}</td>
                                    <td className="p-2 text-right text-[#ff4d00] font-bold text-[10px]">
                                        <div className="flex flex-col">
                                           <span>-{formatCurrency(u.tributos_total)}</span>
                                           <span className="text-[#444]">P:{formatCurrency(u.pis)} I:{formatCurrency(u.irpj)}</span>
                                        </div>
                                    </td>
                                    <td className="p-2 text-right border-r border-[#222] text-[#888]">{formatCurrency((u.receita_caixa||0) - (u.tributos_total||0))}</td>
                                    <td className="p-2 text-right text-[#444]">{u.poc.toFixed(2)}%</td>
                                    <td className="p-2 text-right text-[#34c759]">{formatCurrency(u.receita_societaria)}</td>
                                    <td className="p-2 text-right text-[#ff4d00] text-[10px]">-{formatCurrency(u.tributos_societario)}</td>
                                    <td className={`p-2 text-right text-[10px] font-bold ${pDiferimento > 0 ? 'text-[#007aff]' : 'text-[#ff4d00]'}`}>
                                        {formatCurrency(pDiferimento)}
                                    </td>
                                 </tr>
                                 )
                             })}
                           </React.Fragment>
                         )}) : <tr><td colSpan={8} className="text-center p-8 text-[#555] tracking-widest uppercase text-xs">Sem dados processados.</td></tr>}
                      </tbody>
"""

content = content.replace(old_tbody.strip(), new_tbody.strip())

with open("src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("SUCESSO FRONTEND!")
