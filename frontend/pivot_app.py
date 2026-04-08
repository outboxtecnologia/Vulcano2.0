import re

filepath = "src/App.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update fetchReceitas state mapping
fetch_receitas = """
      .then(res => res.json())
      .then(data => {
        setReceitasData(data.dashboard_data || []);
        setRetData(data.ret_consolidado || []);
        setLoadingReceitas(false);
      })
"""
fetch_receitas_new = """
      .then(res => res.json())
      .then(data => {
        setReceitasData(data.dashboard_data || []);
        setRetData(data.ret_consolidado || []);
        window.dashboard_meta = data.dashboard_meta || {}; // Save globally for rendering
        setLoadingReceitas(false);
      })
"""
if fetch_receitas in content:
   content = content.replace(fetch_receitas, fetch_receitas_new)

# 2. Update filter validation logic - Discard filterStartDate usage, only use End Date for Accumulative <= end
filter_dates = """
  const isDateInRange = (periodo, start, end) => {
    if (!periodo) return true;
    const pStr = typeof periodo === 'string' ? periodo.substring(0, 7) : periodo.toString().substring(0, 7);
    let valid = true;
    if (start) valid = valid && pStr >= start;
    if (end) valid = valid && pStr <= end;
    return valid;
  };
"""
filter_dates_new = """
  const isDateInRange = (periodo, start, end) => {
    if (!periodo) return true;
    const pStr = typeof periodo === 'string' ? periodo.substring(0, 7) : periodo.toString().substring(0, 7);
    // Filtro Mestre de Competência Acumulada: Tudo antes da data final é aceito.
    if (end) return pStr <= end;
    return true;
  };
"""
content = content.replace(filter_dates.strip(), filter_dates_new.strip())

# 3. Update aggregatedReceitas to pick up from dashboard_meta
aggregated_receitas = """
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
"""
aggregated_receitas_new = """
          let agg = map[emp];
          agg.receita_caixa += r.receita_caixa || 0;
          agg.tributos_total += r.tributos_total || 0;
          agg.pis += r.pis || 0;
          agg.cofins += r.cofins || 0;
          agg.irpj += r.irpj || 0;
          agg.csll += r.csll || 0;
          agg.unidades.push(r);
      });
      
      // Inject global metadata values
      Object.keys(map).forEach(emp => {
          if (window.dashboard_meta && window.dashboard_meta[emp]) {
              map[emp].poc = window.dashboard_meta[emp].poc;
              map[emp].receita_societaria = window.dashboard_meta[emp].receita_societaria;
              
              // Oposto as parcelas, o tributo_societario global é a % real mitigada na nota?
              // Podemos refazer a aproximação global aqui para a obra toda:
              let globalEffRate = map[emp].receita_caixa > 0 ? (map[emp].tributos_total / map[emp].receita_caixa) : 0;
              map[emp].tributos_societario = map[emp].receita_societaria * globalEffRate;
          }
      });
      return Object.values(map);
"""
content = content.replace(aggregated_receitas.strip(), aggregated_receitas_new.strip())

# 4. Total values - totalSocietario needs to reflect meta, not sum of rows.
total_soc = """
  const totalSocietario = filteredReceitasData.reduce((acc, r) => acc + (r.receita_societaria || 0), 0) + filteredRetData.reduce((acc, r) => acc + (r.receita_societaria || 0), 0);
"""
total_soc_new = """
  const totalSocietario = Object.values(window.dashboard_meta || {}).reduce((acc, m) => acc + (m.receita_societaria || 0), 0);
"""
content = content.replace(total_soc.strip(), total_soc_new.strip())

# 5. UI Filter Changes
ui_filters = """
                  <div className="flex gap-4">
                    <div className="flex flex-col">
                      <label className="text-[9px] uppercase tracking-[0.2em] font-bold text-[#888] mb-1">Período Inicial</label>
                      <input type="month" value={filterStartDate} onChange={e => setFilterStartDate(e.target.value)} className="bg-[#111] text-[#fff] border border-[#222] p-2 rounded-sm text-sm outline-none w-36" />
                    </div>
                    <div className="flex flex-col">
                      <label className="text-[9px] uppercase tracking-[0.2em] font-bold text-[#888] mb-1">Período Final</label>
                      <input type="month" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="bg-[#111] text-[#fff] border border-[#222] p-2 rounded-sm text-sm outline-none w-36" />
                    </div>
"""
ui_filters_new = """
                  <div className="flex gap-4">
                    <div className="flex flex-col">
                      <label className="text-[9px] uppercase tracking-[0.2em] font-bold text-[#888] mb-1">Mes de Competência (Filtro Acumulativo)</label>
                      <input type="month" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} className="bg-[#111] text-[#fff] border border-[#222] p-2 rounded-sm text-sm outline-none w-48" />
                    </div>
"""
content = content.replace(ui_filters.strip(), ui_filters_new.strip())


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("App.jsx patched for cumulative view!")
