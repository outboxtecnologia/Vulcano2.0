with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_loop = '''for (chave, dt, cdeb, ccred, hist_val, nat, val, chave_origem) in cur_q.fetchall():
            if isinstance(hist_val, (bytes, bytearray)):
                hist = hist_val.decode('cp1252', 'ignore')
            else:
                hist = str(hist_val) if hist_val else ""'''

new_loop = '''for (chave, dt, cdeb, ccred, hist_val, nat, val, chave_origem, descr_hist) in cur_q.fetchall():
            if isinstance(hist_val, (bytes, bytearray)):
                compl = hist_val.decode('cp1252', 'ignore')
            else:
                compl = str(hist_val) if hist_val else ""
                
            descr = str(descr_hist or "").strip()
            hist = f"{descr} {compl}".strip()'''

text = text.replace(old_loop, new_loop)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed main.py loop')
