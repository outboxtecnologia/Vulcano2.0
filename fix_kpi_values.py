import sys

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Fix 1: totalRetMacro now pulls from filteredReceitasData.ret instead of retData (since backend returns empty [])
old_ret = "const totalRetMacro = filteredRetData.reduce((acc, r) => acc + (r.valor_ret || 0), 0);"
new_ret = "const totalRetMacro = filteredReceitasData.reduce((acc, r) => acc + (r.ret || 0), 0);"
app_code = app_code.replace(old_ret, new_ret)

# Fix 2: Remove the globally declared 'totalTributosSocietarios' which returns 0 due to missing metadata in backend
# It was around line 508.
old_tot_soc = "const totalTributosSocietarios = Object.values(window.dashboard_meta || {}).reduce((acc, m) => acc + (m.tributos_societarios || m.tributos_societario || 0), 0);"
app_code = app_code.replace(old_tot_soc, "")

# Fix 3: In the JSX, compute it directly out of aggregatedReceitas
# Look for where it renders:
# <h4 className="text-3xl font-headline font-black text-error mb-2 relative z-10">-{formatCurrency(totalTributosSocietarios)}</h4>
app_code = app_code.replace(
    '{formatCurrency(totalTributosSocietarios)}',
    '{formatCurrency(aggregatedReceitas.reduce((acc, r) => acc + (r.tributos_societario || 0), 0))}'
)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("SUCCESS KPI FIX")
