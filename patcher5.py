with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('desc_padrao = _s_decode(r[7]) if len(r) > 7 else ""', 'desc_padrao = str(r[7] or "").strip() if len(r) > 7 else ""')
text = text.replace('_s_decode(r[1])', 'str(r[1] or "")')
text = text.replace('_s_decode(r[7])', 'str(r[7] or "")')

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Done!')
