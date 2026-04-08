import sys

file_path = r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\VulcanoViews.jsx"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Modificar RecebimentosView
# Remove const paginatedData = currentLevelData.slice(...)
# Troca paginatedData.map para currentLevelData.map
# Remove o paginator footer 

# Remove definition
code = code.replace(
    "const paginatedData = currentLevelData.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);",
    ""
)

# RecebimentosView map loops
code = code.replace(
    "paginatedData.map((r, idx)",
    "currentLevelData.map((r, idx)"
).replace(
    "paginatedData.length === 0",
    "currentLevelData.length === 0"
).replace(
    "paginatedData.length",
    "currentLevelData.length"
)

# Remove Recebimentos pagination div manually by searching for its signature
# It looks like:
# <div className="p-4 border-t border-white/5 flex justify-between items-center bg-[#181818]">
#    <span className="text-[9px] text-[#555] uppercase font-black tracking-[0.2em]">
#       EXIBINDO {currentLevelData.length} DE {currentLevelData.length} REGISTROS PENDENTES ...

receb_footer_start = code.find('<div className="p-4 border-t border-white/5 flex justify-between items-center bg-[#181818]">')
if receb_footer_start != -1:
    receb_footer_end = code.find('</div>\n         </div>\n      </div>\n\n      {/* FOOTER KPIs */}', receb_footer_start)
    if receb_footer_end != -1:
        # replace the block with an empty generic span or just nothing
        code = code[:receb_footer_start] + code[receb_footer_end + 6:]

# 2. Modificar VendasView
code = code.replace(
    "const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);",
    ""
)

code = code.replace(
    "paginatedData.map((v)",
    "filtered.map((v)"
)

# Vendas pagination div
vendas_footer_start = code.find('{/* PAGINATION */}')
if vendas_footer_start != -1:
    vendas_footer_end = code.find('</div>\n      </div>\n\n      {/* FOOTER KPIs */}', vendas_footer_start)
    if vendas_footer_end != -1:
        code = code[:vendas_footer_start] + code[vendas_footer_end + 6:]

# Ensure infinite scroll wrapper works nicely for both 
code = code.replace('flex-col flex-1 overflow-hidden relative min-h-[300px]"', 'flex-col flex-1 overflow-hidden relative min-h-[300px] max-h-[70vh]"')
code = code.replace('flex-col flex-1 overflow-hidden min-h-[400px]"', 'flex-col flex-1 overflow-hidden min-h-[400px] max-h-[80vh]"')
code = code.replace('className="overflow-auto flex-1"', 'className="overflow-y-auto flex-1 custom-scrollbar"')

# Write back
with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Pagination removed. Using infinite scroll layout now.")
