import re

with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add import for _s_decode if not present
if 'from main import _s_decode' not in text:
    text = text.replace('from main import get_conn', 'from main import get_conn, _s_decode')

old_query = """SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.VALORLCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, 
           '' as desc,
           C.CODIGOORIGLCTOCTB,
           H.DESCRHISTCTB"""

new_query = """SELECT C.CHAVELCTOCTB, C.DATALCTOCTB, C.VALORLCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, 
           CAST(C.COMPLHIST AS BLOB SUB_TYPE 0),
           C.CODIGOORIGLCTOCTB,
           H.DESCRHISTCTB"""

old_loop = """deb = int(r[3] or 0)
        cred = int(r[4] or 0)
        desc_padrao = str(r[7] or "").strip() if len(r) > 7 else ""
        texto_limpo = f"{desc_padrao}".strip().upper()"""

new_loop = """deb = int(r[3] or 0)
        cred = int(r[4] or 0)
        compl = _s_decode(r[5])
        desc_padrao = str(r[7] or "").strip() if len(r) > 7 else ""
        texto_limpo = f"{desc_padrao} {compl}".strip().upper()"""

text = text.replace(old_query, new_query)
text = text.replace(old_loop, new_loop)

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch applied to vector_sync.py")
