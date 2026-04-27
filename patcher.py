import re

with open('backend/vector_sync.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the Vulcano extractions
v_replace = """    # Fetch Questor standard texts for mapping
    try:
        cq = get_conn('questor')
        cur_q = cq.cursor()
        cur_q.execute("SELECT CODIGOHISTCTB, DESCRHISTCTB FROM HISTORICOCTB")
        hist_questor = {int(r[0]): str(r[1] or "").strip() for r in cur_q.fetchall() if r[0]}
        cq.close()
    except Exception:
        hist_questor = {}

    lote = []
    for r in cur.fetchall():
        r_id = r[0]
        dt = r[1].strftime('%Y-%m') if r[1] else "2025-00"
        valor = float(r[2] or 0.0)
        unid = str(r[3] or "").strip()
        hist_code = int(r[5] or 0) if len(r) > 5 else 0
        hist_str = hist_questor.get(hist_code, "RECEBIMENTO PARCELA")"""

if 'lote = []\n    for r in cur.fetchall():' in text:
    text = re.sub(r'lote = \[\]\s*for r in cur\.fetchall\(\):\s*r_id = r\[0\]\s*dt = .+?\s*valor = .+?\s*unid = .+?\.strip\(\)', v_replace, text, flags=re.DOTALL)

if 'texto_limpo = f"RECEBIMENTO PARCELA UNID {unid}".upper()' in text:
    text = text.replace('texto_limpo = f"RECEBIMENTO PARCELA UNID {unid}".upper()', 'texto_limpo = f"{hist_str} UNID {unid}".upper()')

# Questor replace
q_old = """desc = str(r[5] or "").strip()
        orig = str(r[6] or "").strip()
        
        texto_limpo = desc.upper()"""
q_new = """desc = str(r[5] or "").strip()
        orig = str(r[6] or "").strip()
        desc_padrao = str(r[7] or "").strip() if len(r) > 7 else ""
        texto_limpo = f"{desc_padrao} {desc}".upper().strip()"""
text = text.replace(q_old, q_new)

with open('backend/vector_sync.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fix executed!")
