with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Look for the broken className
# <th key={i} className={p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] }>
broken_pattern = r'className=\{p-3 border-b border-r border-\[#333\] font-bold bg-\[#1a1a1a\] \}'
new_str = 'className={p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] }'

text = re.sub(broken_pattern, new_str, text)

# Just in case the previous bad one still exists
broken2 = r'className="p-3 border-b border-r border-\[#333\] font-bold bg-\[#1a1a1a\] \{dossierExpanded \? \\"min-w-\[800px\]\\" : \\"min-w-\[400px\]\\"}"'
text = re.sub(broken2, new_str, text)

# Just in case there's another unquoted string:
broken3 = r'className="p-3 border-b border-r border-\[#333\] font-bold bg-\[#1a1a1a\] \{dossierExpanded \? "min-w-\[800px\]" : "min-w-\[400px\]"\}"'
text = re.sub(broken3, new_str, text)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Regex Fixed!")
