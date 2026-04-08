import os
import re

app_path = r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\App.jsx"
with open(app_path, "r", encoding="utf-8") as f:
    app_text = f.read()

app_text = app_text.replace(
    '<NavItem icon={<Zap size={16}/>} label="Conversor XML" active={currentView === \'conciliador\'}',
    '<NavItem icon={<Zap size={16}/>} label="IMPORTAÇÃO" active={currentView === \'conciliador\'}'
)
with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_text)

vulcano_path = r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx"
with open(vulcano_path, "r", encoding="utf-8") as f:
    vulcano_text = f.read()

# Replace Universal PDF Generator header
vulcano_text = vulcano_text.replace(
    'Universal PDF <span className="text-[#007aff]">Generator</span>',
    'HUB DE <span className="text-[#007aff]">IMPORTAÇÃO</span>'
)

# Replace Extrator + Chat de Ajuste header
vulcano_text = vulcano_text.replace(
    'Extrator + Chat de Ajuste',
    'Extrator IA + Chat de Ajuste'
)

# Add the selector
html_selector = """
              <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[#888] cursor-pointer select-none justify-center">
                <select className="bg-[#0a0a0a] border border-[#333] text-white p-2 rounded-sm outline-none focus:border-[#007aff]">
                  <option value="">Tipo: Autodetectar</option>
                  <option value="venda">Venda</option>
                  <option value="recebimento">Recebimento</option>
                  <option value="conciliacao">Conciliação Bancária</option>
                </select>
              </label>
"""
if 'Só IA (ignorar modelo' in vulcano_text:
    vulcano_text = vulcano_text.replace(
        '<label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[#888] cursor-pointer select-none justify-center">\n              <input\n                type="checkbox"\n                checked={extractForceAi}',
        html_selector + '\n              <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[#888] cursor-pointer select-none justify-center">\n              <input\n                type="checkbox"\n                checked={extractForceAi}'
    )

with open(vulcano_path, "w", encoding="utf-8") as f:
    f.write(vulcano_text)

print("Hub de Importação UI restored and patched.")
