with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

bad = 'className="p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] {dossierExpanded ? \"min-w-[800px]\" : \"min-w-[400px]\"}"'
good = 'className={p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] }'

text = text.replace(bad, good)

# Also check for any other literal curly braces inside classNames
# Wait, let's also fix the row data! The ui_expand.py replaced:
# <div className="grid grid-cols-7 gap-4 pt-2 mt-2 border-t border-dashed border-[#555] text-[10.5px] uppercase tracking-wider text-gray-400">
# The script replaced it correctly with className={grid }

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed JSX Syntax!")
