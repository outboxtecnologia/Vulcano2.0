with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("s1 = r[3].read().decode('cp1252', errors='replace') if r[3] else ''", "s1 = (r[3].read() if hasattr(r[3], 'read') else r[3]).decode('cp1252', errors='replace') if r[3] else ''")

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
