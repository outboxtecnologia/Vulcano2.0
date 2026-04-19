import os

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix Kanban headers that were reset
code = code.replace(
    '<span className="text-[#22c55e] text-[8px] leading-none mb-0.5">■</span>',
    '<span className="text-[#3b82f6] text-[8px] leading-none mb-0.5">■</span>'
)
code = code.replace(
    '<span className="text-[#22c55e] font-mono text-[9px] font-bold tracking-widest leading-none">QUESTOR</span>',
    '<span className="text-[#3b82f6] font-mono text-[9px] font-bold tracking-widest leading-none">QUESTOR</span>'
)
code = code.replace(
    '<span className="bg-[#1a331a] text-[#22c55e] text-[9px] px-1 rounded leading-none">{d.questor.length}</span>',
    '<span className="bg-[#1a3a66] text-[#3b82f6] text-[9px] px-1 rounded leading-none">{d.questor.length}</span>'
)
code = code.replace(
    '<div className="px-3 py-1.5 bg-[#141814] border-b border-[#222] flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm bg-opacity-90">',
    '<div className="mb-2 pb-1 border-b border-[#333] flex justify-between items-center bg-[#111] sticky top-0 z-10 px-1 py-1 pt-2 -mx-1">'
)

code = code.replace(
    '<span className="text-[#ffb020] text-[8px] leading-none mb-0.5">■</span>',
    '<span className="text-[#ff4500] text-[8px] leading-none mb-0.5">■</span>'
)
code = code.replace(
    '<span className="text-[#ffb020] font-mono text-[9px] font-bold tracking-widest leading-none">VU 2.0</span>',
    '<span className="text-[#ff4500] font-mono text-[9px] font-bold tracking-widest leading-none">VU 2.0</span>'
)
code = code.replace(
    '<span className="bg-[#4d3311] text-[#ffb020] text-[9px] px-1 rounded leading-none">{d.vulcano2.length}</span>',
    '<span className="bg-[#662211] text-[#ff4500] text-[9px] px-1 rounded leading-none">{d.vulcano2.length}</span>'
)


# Fix map/tabular grid summaries that were reset
code = code.replace(
    '<span className="text-[#22c55e] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalQuestor)}</span>',
    '<span className="text-[#3b82f6] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalQuestor)}</span>'
)
code = code.replace(
    '<span className="text-[#ffb020] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalVulcano2)}</span>',
    '<span className="text-[#ff4500] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalVulcano2)}</span>'
)

# Fix map/tabular details that were reset
code = code.replace(
    'const badgeColor = colorKey === \'Q\' ? \'#22c55e\' : colorKey === \'V1\' ? \'#9945ff\' : \'#ffb020\';',
    'const badgeColor = colorKey === \'Q\' ? \'#3b82f6\' : colorKey === \'V1\' ? \'#9945ff\' : \'#ff4500\';'
)
code = code.replace(
    'const bgVar = colorKey === \'Q\' ? \'bg-[#151a15]\' : colorKey === \'V1\' ? \'bg-[#181120]\' : \'bg-[#1f1a11]\';',
    'const bgVar = colorKey === \'Q\' ? \'bg-[#121c2d]\' : colorKey === \'V1\' ? \'bg-[#181120]\' : \'bg-[#26120e]\';'
)
code = code.replace(
    'const borderVar = colorKey === \'Q\' ? \'border-[#1a331a]\' : colorKey === \'V1\' ? \'border-[#33114d]\' : \'border-[#4d3311]\';',
    'const borderVar = colorKey === \'Q\' ? \'border-[#1a3a66]\' : colorKey === \'V1\' ? \'border-[#33114d]\' : \'border-[#662211]\';'
)


with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch 3 aplicado.")
