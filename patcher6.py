with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_query = """SELECT 
                C.CHAVELCTOCTB, C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.NATURLCTOCTB, G.VALORLCTOGER, C.CHAVEORIGEM
            FROM LCTOGER G
            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB"""

new_query = """SELECT 
                C.CHAVELCTOCTB, C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.NATURLCTOCTB, G.VALORLCTOGER, C.CHAVEORIGEM, H.DESCRHISTCTB
            FROM LCTOGER G
            JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
            LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB"""

old_loop = """for (chave, dt, c_deb, c_cred, hist_val, nat, val, orig) in cur_q.fetchall():
            orig_str = str(orig) if orig else ""
            if orig_str == "ZZ": continue # Ignora encerramentos

            hist = _s_decode(hist_val)"""

new_loop = """for (chave, dt, c_deb, c_cred, hist_val, nat, val, orig, descr_hist) in cur_q.fetchall():
            orig_str = str(orig) if orig else ""
            if orig_str == "ZZ": continue # Ignora encerramentos

            compl = _s_decode(hist_val)
            descr = str(descr_hist or "").strip()
            hist = f"{descr} {compl}".strip()"""

text = text.replace(old_query, new_query)
text = text.replace(old_loop, new_loop)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("main.py patched successfully")
