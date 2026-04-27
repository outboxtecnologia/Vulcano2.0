with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'className={p-3 border-b border-r border-[#333] font-bold' in line:
        print(f"Found bad line at {i}")
        lines[i] = '                                  <th key={i} className={p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] }>\n'
    elif 'className="p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] {dossierExpanded' in line:
        print(f"Found bad line 2 at {i}")
        lines[i] = '                                  <th key={i} className={p-3 border-b border-r border-[#333] font-bold bg-[#1a1a1a] }>\n'

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("JSX Fixed line by line!")
