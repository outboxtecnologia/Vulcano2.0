with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i in range(len(lines)):
    line = lines[i]
    if 'rowData.custo_questor_fracionado' in line and 'text-white' in line and not 'dossierExpanded &&' in ''.join(lines[max(0, i-6):i]):
        line = line.replace('rowData.custo_questor_fracionado', 'rowData.credito_questor')
    elif 'rowData.custo_questor_acumulado' in line and 'text-[#34c759]' in line and not 'dossierExpanded &&' in ''.join(lines[max(0, i-6):i]):
        line = line.replace('rowData.custo_questor_acumulado', 'rowData.credito_questor_acumulado')
    elif 'rowData.credito_questor' in line and 'text-blue-400' in line and 'dossierExpanded &&' in ''.join(lines[max(0, i-5):i]):
        # This is where we put the old fracionado value
        line = line.replace('rowData.credito_questor', 'rowData.custo_questor_fracionado')
    new_lines.append(line)

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Regex Fixed!")
