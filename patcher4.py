with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

def_safe = '''def _s_decode(val):
    if isinstance(val, bytes):
        try: return val.decode('win1252', 'ignore').strip()
        except: return str(val)
    return str(val or "").strip()
'''

if 'def _s_decode' not in text:
    text = text.replace('import json', 'import json\n' + def_safe)

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Function injected.")
