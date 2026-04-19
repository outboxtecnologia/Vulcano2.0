import sys

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

tabular_span = '<div className={`flex items-center justify-between px-3 py-2 bg-[#151515] border-b border-[var(--v-border)] ${isDragOver ? \\\'bg-[#ff6b1a]/10\\\' : \\\'\\\'}`}>\n                    <span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span>'

tabular_replacement = '<div className={`flex items-center justify-between px-3 py-2 bg-[#151515] border-b border-[var(--v-border)] ${isDragOver ? \\\'bg-[#ff6b1a]/10\\\' : \\\'\\\'}`}>\n                    <div className="flex items-center gap-3"><span className="font-black text-[12px] text-white tracking-widest uppercase">{k.replace(\'_\', \' \')}</span> <button onClick={() => setDetalheApto(k)} className="px-1.5 py-0.5 rounded bg-[#1f1a11] border border-[#ff6b1a] text-[#ff6b1a] hover:bg-[#ff6b1a] hover:text-white text-[9px] font-mono tracking-widest transition-colors font-bold z-10 cursor-pointer">INFO</button></div>'

code = code.replace(tabular_span, tabular_replacement)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied to Tabular.")
