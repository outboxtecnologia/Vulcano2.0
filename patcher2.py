with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

def_safe = '''def _s_decode(val):
    if isinstance(val, bytes):
        try: return val.decode('win1252', 'ignore').strip()
        except: return str(val)
    return str(val or "").strip()
'''

if 'def _s_decode' not in text:
    text = text.replace('import json\nimport uuid', 'import json\nimport uuid\n\n' + def_safe)

# Replace all the str(r[...]).strip() logic carefully
text = text.replace('str(r[5] or "").strip()', '_s_decode(r[5])')
text = text.replace('str(r[6] or "").strip()', '_s_decode(r[6])')
text = text.replace('str(r[7] or "").strip() if len(r) > 7 else ""', '_s_decode(r[7]) if len(r) > 7 else ""')
text = text.replace('str(r[3] or "").strip()', '_s_decode(r[3])')
text = text.replace('str(r[1] or "").strip()', '_s_decode(r[1])')
text = text.replace('str(r[1] or "").strip()', '_s_decode(r[1])')

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patch decoding applied.")
