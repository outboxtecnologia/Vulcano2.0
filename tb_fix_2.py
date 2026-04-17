with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"custo_questor": c["custo"],', '"custo_questor": custo_orig,')

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed KeyError!")
