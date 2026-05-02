import sys
import os

with open("backend/main.py", "r", encoding="utf-8", errors="ignore") as f:
    code = f.read()

old_block = """            conn_sq.close()
            TOLE = 1.0

            for row in payload.rows:
                valor_pl    = _parse_valor(_get(row, "VALOR_PAGO")) or _parse_valor(_get(row, "VALOR_PARCELA"))
                valor_nominal_pl = _parse_valor(_get(row, "VALOR_PARCELA"))
                acrescimos_pl = _parse_valor(_get(row, "ACRESCIMOS"))
                descontos_pl = _parse_valor(_get(row, "DESCONTOS"))
                num_parcela_pl = _get(row, "NUMERO_PARCELA") or ""
                
                dt_venc_pl  = _parse_data(_get(row, "DATA_VENCIMENTO"))
                dt_pago_pl  = _parse_data(_get(row, "DATA_PAGAMENTO"))
                cliente_pl  = _get(row, "CLIENTE_NOME") or ""
                contrato_pl = _get(row, "CONTRATO") or ""
                unidade_pl  = _get(row, "UNIDADE") or ""

                status = "SEM_MATCH"
                valor_v = cliente_v = dt_venc_v = unidade_v = num_parcela = id_parcela = acrescimos = descontos = None

                candidatos = []
                for lista, st in [(abertas, "MATCH_PERFEITO"), (quitadas, "JA_QUITADO")]:
                    for p in lista:
                        pv    = float(p[4] if st == "JA_QUITADO" else p[3] or 0)
                        pvenc = p[2]
                        match_val  = valor_pl is not None and abs(pv - valor_pl) <= TOLE
                        match_venc = dt_venc_pl and pvenc and str(pvenc)[:10] == str(dt_venc_pl)
                        
                        nome_db = str(p[5] or "").upper().strip()
                        nome_pl = str(cliente_pl).upper().strip()
                        
                        match_nome = False
                        if not nome_pl or not nome_db:
                            match_nome = True
                        else:
                            if nome_db in nome_pl or nome_pl in nome_db:
                                match_nome = True
                            else:
                                tokens_db = set([t for t in nome_db.split() if len(t) > 2])
                                tokens_pl = set([t for t in nome_pl.split() if len(t) > 2])
                                if len(tokens_db.intersection(tokens_pl)) >= 1:
                                    match_nome = True

                        if match_nome and (match_val or match_venc):
                            score = 0
                            if match_val and match_venc: score += 100
                            elif match_val: score += 50
                            elif match_venc: score += 20
                            
                            if st == "MATCH_PERFEITO": score += 10 # Prioriza abertas
                            
                            candidatos.append({
                                'score': score,
                                'status': st,
                                'id_parcela': p[0],
                                'num_parcela': p[1],
                                'valor_v': pv,
                                'cliente_v': str(p[5] or ""),
                                'dt_venc_v': str(pvenc),
                                'unidade_v': str(p[6] or "") if p[6] else None
                            })"""

new_block = """            conn_sq.close()
            TOLE = 1.0

            from collections import defaultdict
            idx_parcelas = defaultdict(list)
            for p in abertas:
                v = float(p[3] or 0)
                idx_parcelas[int(v)].append((p, "MATCH_PERFEITO"))
            for p in quitadas:
                v = float(p[4] or 0)
                idx_parcelas[int(v)].append((p, "JA_QUITADO"))

            todas_parcelas_fallback = [(p, "MATCH_PERFEITO") for p in abertas] + [(p, "JA_QUITADO") for p in quitadas]

            for row in payload.rows:
                valor_pl    = _parse_valor(_get(row, "VALOR_PAGO")) or _parse_valor(_get(row, "VALOR_PARCELA"))
                valor_nominal_pl = _parse_valor(_get(row, "VALOR_PARCELA"))
                acrescimos_pl = _parse_valor(_get(row, "ACRESCIMOS"))
                descontos_pl = _parse_valor(_get(row, "DESCONTOS"))
                num_parcela_pl = _get(row, "NUMERO_PARCELA") or ""
                
                dt_venc_pl  = _parse_data(_get(row, "DATA_VENCIMENTO"))
                dt_pago_pl  = _parse_data(_get(row, "DATA_PAGAMENTO"))
                cliente_pl  = _get(row, "CLIENTE_NOME") or ""
                contrato_pl = _get(row, "CONTRATO") or ""
                unidade_pl  = _get(row, "UNIDADE") or ""

                status = "SEM_MATCH"
                valor_v = cliente_v = dt_venc_v = unidade_v = num_parcela = id_parcela = acrescimos = descontos = None

                candidatos = []
                
                if valor_pl is not None:
                    v_int = int(valor_pl)
                    possiveis = idx_parcelas.get(v_int-1, []) + idx_parcelas.get(v_int, []) + idx_parcelas.get(v_int+1, [])
                else:
                    possiveis = todas_parcelas_fallback

                for p, st in possiveis:
                    pv    = float(p[4] if st == "JA_QUITADO" else p[3] or 0)
                    pvenc = p[2]
                    match_val  = valor_pl is not None and abs(pv - valor_pl) <= TOLE
                    match_venc = dt_venc_pl and pvenc and str(pvenc)[:10] == str(dt_venc_pl)
                    
                    nome_db = str(p[5] or "").upper().strip()
                    nome_pl = str(cliente_pl).upper().strip()
                    
                    match_nome = False
                    if not nome_pl or not nome_db:
                        match_nome = True
                    else:
                        if nome_db in nome_pl or nome_pl in nome_db:
                            match_nome = True
                        else:
                            tokens_db = set([t for t in nome_db.split() if len(t) > 2])
                            tokens_pl = set([t for t in nome_pl.split() if len(t) > 2])
                            if len(tokens_db.intersection(tokens_pl)) >= 1:
                                match_nome = True

                    if match_nome and (match_val or match_venc):
                        score = 0
                        if match_val and match_venc: score += 100
                        elif match_val: score += 50
                        elif match_venc: score += 20
                        
                        if st == "MATCH_PERFEITO": score += 10 # Prioriza abertas
                        
                        candidatos.append({
                            'score': score,
                            'status': st,
                            'id_parcela': p[0],
                            'num_parcela': p[1],
                            'valor_v': pv,
                            'cliente_v': str(p[5] or ""),
                            'dt_venc_v': str(pvenc)[:10] if pvenc else None,
                            'unidade_v': str(p[6] or "") if p[6] else None
                        })"""

old_append = """                resultados.append({
                    "status":           status,
                    "id_parcela":       id_parcela,
                    "cliente_planilha": cliente_pl or cliente_v or "",
                    "dt_vencimento":    str(dt_venc_pl) if dt_venc_pl else dt_venc_v,
                    "dt_pagamento":     str(dt_pago_pl) if dt_pago_pl else None,
                    "valor_planilha":   valor_pl,
                    "valor_vulcano":    valor_v,
                    "unidade":          unidade_pl or unidade_v or "",
                    "contrato":         contrato_pl,
                    "numero_parcela":   num_parcela,
                    "num_parcela_planilha": str(num_parcela_pl),
                    "acrescimos":       acrescimos,
                    "descontos":        descontos,
                    "obs":              _get(row, "OBSERVACOES") or "",
                })"""

new_append = """                resultados.append({
                    "status":           status,
                    "id_parcela":       id_parcela,
                    "cliente_planilha": cliente_pl or "",
                    "cliente_vulcano":  cliente_v or "",
                    "dt_vencimento":    str(dt_venc_pl) if dt_venc_pl else None,
                    "dt_venc_vulcano":  str(dt_venc_v) if dt_venc_v else None,
                    "dt_pagamento":     str(dt_pago_pl) if dt_pago_pl else None,
                    "valor_planilha":   valor_pl,
                    "valor_vulcano":    valor_v,
                    "unidade":          unidade_pl or "",
                    "unidade_vulcano":  unidade_v or "",
                    "contrato":         contrato_pl,
                    "numero_parcela":   num_parcela,
                    "num_parcela_planilha": str(num_parcela_pl),
                    "acrescimos":       acrescimos,
                    "descontos":        descontos,
                    "obs":              _get(row, "OBSERVACOES") or "",
                })"""

if old_block in code:
    code = code.replace(old_block, new_block)
    print("Block 1 replaced successfully.")
else:
    print("Block 1 not found!")

if old_append in code:
    code = code.replace(old_append, new_append)
    print("Block 2 replaced successfully.")
else:
    print("Block 2 not found!")

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(code)
