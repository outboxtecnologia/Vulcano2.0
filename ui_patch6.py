with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('{d.ano}-{str(d.mes).padStart(2, \\'0\\')}', '{d.ano}-{String(d.mes).padStart(2, \\'0\\')}')

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

