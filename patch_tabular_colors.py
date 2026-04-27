import sys

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Tabular colors from standard view matching Kanban
code = code.replace(
    'className="flex flex-col border border-[#34c759]/30 bg-[#111] p-1.5 rounded hover:bg-[#1a1a1a]">',
    'className="flex flex-col border border-[#3b82f6]/30 bg-[#121c2d] p-1.5 rounded hover:bg-[#1a3a66]">'
)

code = code.replace(
    'className="text-[10px] font-black uppercase tracking-widest text-[#22c55e] mb-1.5 px-1 text-center">Questor ({d.questor.length})</div>',
    'className="text-[10px] font-black uppercase tracking-widest text-[#3b82f6] mb-1.5 px-1 text-center">Questor ({d.questor.length})</div>'
)

code = code.replace(
    'className="text-[10px] font-black uppercase tracking-widest text-[#ffb020] mb-1.5 px-1 text-center">VU 2.0 ({d.vulcano2.length})</div>',
    'className="text-[10px] font-black uppercase tracking-widest text-[#ff4500] mb-1.5 px-1 text-center">VU 2.0 ({d.vulcano2.length})</div>'
)

code = code.replace(
    'className="flex flex-col border border-[#ffb020]/30 bg-[#111] p-1.5 rounded hover:bg-[#1a1a1a]">',
    'className="flex flex-col border border-[#ff4500]/30 bg-[#26120e] p-1.5 rounded hover:bg-[#662211]">'
)

# Replace "Bateu" badge color in Tabular header to Blue to match the theme
code = code.replace(
    '<span className="px-1.5 py-0.5 rounded text-xs font-black uppercase tracking-widest bg-[#34c759]/20 text-[#34c759]">Bateu</span>',
    '<span className="px-1.5 py-0.5 rounded text-xs font-black uppercase tracking-widest bg-[#3b82f6]/20 text-[#3b82f6]">Bateu</span>'
)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied for Tabular colors.")
