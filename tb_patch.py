with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''        creditos_questor_global = [{"ano": int(r[0]), "mes": int(r[1]), "credito": float(r[2] or 0)} for r in cur_q.fetchall()]
        
        # Aglutinar e cruzar arrays mensais em um Dossiê Massivo Temporal'''

good = '''        creditos_questor_global = [{"ano": int(r[0]), "mes": int(r[1]), "credito": float(r[2] or 0)} for r in cur_q.fetchall()]
        
        # EXTRACT DETAILED EXACT TRANSACTIONS FROM LCTOCTB RAZAO TO BUILD UNIT SPECIFIC POPUPS
        cur_q.execute("""
            SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), C.VALORLCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
            FROM LCTOCTB C
            LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
            WHERE C.CONTACTBCRED = ? AND C.CODIGOEMPRESA = ? 
        """, (int(num_conta) if num_conta else 5639, empresa_id))
        creditos_questor_detalhes = []
        for r in cur_q.fetchall():
            s1 = r[3].read().decode('cp1252', errors='replace') if r[3] else ""
            s2 = str(r[4] or "")
            c_str = f"{s2} {s1}".strip().upper()
            creditos_questor_detalhes.append({
                "ano": int(r[0]), "mes": int(r[1]), "valor": float(r[2] or 0), "str": c_str
            })

        # Aglutinar e cruzar arrays mensais em um Dossiê Massivo Temporal'''

text = text.replace(bad, good)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

