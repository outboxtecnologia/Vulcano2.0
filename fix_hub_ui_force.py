import os
import re

app_path = r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\App.jsx"
with open(app_path, "r", encoding="utf-8") as f:
    app_text = f.read()

app_text = re.sub(r'label=[\"\']Conversor XML[\"\']', 'label="IMPORTAÇÃO"', app_text)
with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_text)

vulcano_path = r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\VulcanoViews.jsx"
with open(vulcano_path, "r", encoding="utf-8") as f:
    vulcano_text = f.read()

vulcano_text = re.sub(
    r'Universal PDF <span className=\"text-\[\#007aff\]\">Generator</span>',
    'HUB DE <span className="text-[#007aff]">IMPORTAÇÃO</span>',
    vulcano_text
)

# Insert selector before extractForceAi
html_selector = """
              <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest font-bold text-[#888] cursor-pointer select-none justify-center">
                <select className="bg-[#0a0a0a] border border-[#333] text-white p-2 text-xs rounded-sm outline-none focus:border-[#007aff]">
                  <option value="">Destino Automático / IA</option>
                  <option value="venda">Forçar: Vendas (NF-e/NFS-e)</option>
                  <option value="recebimento">Forçar: Recebimentos Financeiros</option>
                  <option value="conciliacao">Forçar: Conciliação Bancária</option>
                </select>
              </label>
"""

# Find extractForceAi checkbox and prepend
pattern = r'(<label[^>]*>\s*<input[^>]*checked=\{extractForceAi\}[^>]*>\s*Só IA.*?</label>)'
vulcano_text = re.sub(pattern, html_selector + r'\n              \1', vulcano_text, flags=re.DOTALL)

with open(vulcano_path, "w", encoding="utf-8") as f:
    f.write(vulcano_text)

print("Forced replacement done.")
