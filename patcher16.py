import re

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. State
code = re.sub(
    r'(const \[soDivergentes, setSoDivergentes\] = useState\(false\);)',
    r'\1\n  const [fontesFaltantes, setFontesFaltantes] = useState(false);',
    code
)

# 2. Checkbox UI
code = re.sub(
    r'(<input type="checkbox" checked=\{soDivergentes\}.*?SÓ DIVERGENTES\s*</label>)',
    r'\1\n                   <label className="flex items-center gap-2 cursor-pointer text-[#888] text-[10px] font-mono uppercase tracking-widest hover:text-white transition-colors">\n                      <input type="checkbox" checked={fontesFaltantes} onChange={e => setFontesFaltantes(e.target.checked)} className="accent-[#ff4500] w-3 h-3" />\n                      FONTES FALTANTES\n                   </label>',
    code,
    flags=re.DOTALL
)

# 3. Filter logic
code = re.sub(
    r'(const hasDiff = Math\.abs\(d\.totalQuestor - d\.totalVulcano2\) > 0\.5;)',
    r'\1\n      const isFaltante = d.questor.length === 0 || d.vulcano2.length === 0;',
    code
)
code = re.sub(
    r'(if \(soDivergentes && !hasDiff\) return false;)',
    r'\1\n      if (fontesFaltantes && !isFaltante) return false;',
    code
)

# 4. Color Replacements for Questor and VU 2.0
code = code.replace(
    '<span className="text-[#22c55e]">■</span> <span className="text-[#888]">QUESTOR</span>',
    '<span className="text-[#3b82f6]">■</span> <span className="text-[#888]">QUESTOR</span>'
)
code = code.replace(
    "const badgeColor = colorKey === 'Q' ? '#22c55e' : colorKey === 'V1' ? '#9945ff' : '#ffb020';",
    "const badgeColor = colorKey === 'Q' ? '#3b82f6' : colorKey === 'V1' ? '#9945ff' : '#ff4500';"
)
code = code.replace(
    "const bgVar = colorKey === 'Q' ? 'bg-[#151a15]' : colorKey === 'V1' ? 'bg-[#181120]' : 'bg-[#1f1a11]';",
    "const bgVar = colorKey === 'Q' ? 'bg-[#121c2d]' : colorKey === 'V1' ? 'bg-[#181120]' : 'bg-[#26120e]';"
)
code = code.replace(
    "const borderVar = colorKey === 'Q' ? 'border-[#1a331a]' : colorKey === 'V1' ? 'border-[#33114d]' : 'border-[#4d3311]';",
    "const borderVar = colorKey === 'Q' ? 'border-[#1a3a66]' : colorKey === 'V1' ? 'border-[#33114d]' : 'border-[#662211]';"
)

code = code.replace(
    '<span className="text-[#22c55e] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalQuestor)}</span>',
    '<span className="text-[#3b82f6] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalQuestor)}</span>'
)
code = code.replace(
    '<span className="text-[#ffb020] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalVulcano2)}</span>',
    '<span className="text-[#ff4500] text-[10px] font-bold font-mono leading-none">{fmtK(d.totalVulcano2)}</span>'
)

code = code.replace(
    '<span className="text-[#ffb020]">■</span> <span className="text-[#888]">VU 2.0</span>',
    '<span className="text-[#ff4500]">■</span> <span className="text-[#888]">VU 2.0</span>'
)

code = code.replace(
    '<span className="text-[#22c55e] text-[8px] leading-none mb-0.5">■</span>',
    '<span className="text-[#3b82f6] text-[8px] leading-none mb-0.5">■</span>'
)
code = code.replace(
    '<span className="text-[#22c55e] font-mono text-[9px] font-bold tracking-widest leading-none">QUESTOR</span>',
    '<span className="text-[#3b82f6] font-mono text-[9px] font-bold tracking-widest leading-none">QUESTOR</span>'
)
code = code.replace(
    '<span className="bg-[#1a331a] text-[#22c55e] text-[9px] px-1 rounded leading-none">',
    '<span className="bg-[#1a3a66] text-[#3b82f6] text-[9px] px-1 rounded leading-none">'
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
    '<span className="bg-[#4d3311] text-[#ffb020] text-[9px] px-1 rounded leading-none">',
    '<span className="bg-[#662211] text-[#ff4500] text-[9px] px-1 rounded leading-none">'
)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print('Success')
