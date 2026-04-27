with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('from main import get_conn, _s_decode', 'from main import get_conn')

s_decode_code = """
def _s_decode(val):
    if not val:
        return ""
    if isinstance(val, (bytes, bytearray)):
        return val.decode("win1252", errors="replace")
    return str(val)

"""

if 'def _s_decode' not in text:
    text = text.replace('async def processar_lote', s_decode_code + '\nasync def processar_lote')

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("done")
