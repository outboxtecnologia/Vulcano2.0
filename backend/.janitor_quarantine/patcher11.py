with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace SELECTs in LCTOGER section
text = text.replace(
    'CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.VALORLCTOGER, G.NATURLCTOCTB\n                        FROM LCTOGER G\n                        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB',
    'CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), G.VALORLCTOGER, G.NATURLCTOCTB, H.DESCRHISTCTB\n                        FROM LCTOGER G\n                        JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB\n                        LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB'
)

# Replace SELECTs in LCTOCTB section
text = text.replace(
    'CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), C.VALORLCTOCTB\n                        FROM LCTOCTB C',
    'CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), C.VALORLCTOCTB, H.DESCRHISTCTB\n                        FROM LCTOCTB C\n                        LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB'
)

old_loop = '''            for row_tuple in rows:
                chave, dt, cdeb, ccred, hist_raw, valor = row_tuple[:6]
                opt_nat = row_tuple[6] if len(row_tuple) > 6 else None
                
                if isinstance(hist_raw, (bytes, bytearray)):
                    hist = hist_raw.decode("cp1252", "ignore")
                elif hasattr(hist_raw, "read"):
                    hist = hist_raw.read().decode("cp1252", "ignore")
                else:
                    hist = str(hist_raw or "")'''

new_loop = '''            for row_tuple in rows:
                chave, dt, cdeb, ccred, hist_raw, valor = row_tuple[:6]
                
                if len(row_tuple) >= 8:
                    opt_nat = row_tuple[6]
                    descr_str = str(row_tuple[7] or "").strip()
                else:
                    opt_nat = None
                    descr_str = str(row_tuple[6] or "").strip()
                
                if isinstance(hist_raw, (bytes, bytearray)):
                    compl = hist_raw.decode("cp1252", "ignore")
                elif hasattr(hist_raw, "read"):
                    compl = hist_raw.read().decode("cp1252", "ignore")
                else:
                    compl = str(hist_raw or "")
                    
                hist = f"{descr_str} {compl}".strip()'''

text = text.replace(old_loop, new_loop)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched successfully!')
