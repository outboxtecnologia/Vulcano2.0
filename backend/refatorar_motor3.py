import sys

new_logic = r'''            # Pesquisa Rápida em RAM (In-Memory Filter) com Score de Vendas
            def clean_str(s): return str(s).lower().strip()
            
            candidatas = []
            for v_data in todas_vendas:
                v_id, c_nome, c_id, c_cnpj, v_desc, e_nome = v_data
                
                db_cpf = ''.join(c for c in str(c_cnpj or '') if c.isdigit())
                score = 0
                is_diamante_c = False
                
                if cpf_clean and len(cpf_clean) > 5 and cpf_clean == db_cpf:
                    score += 20
                    is_diamante_c = True
                    
                if comprador_nome and clean_str(comprador_nome) in clean_str(c_nome):
                    score += 10
                    
                if unidade and v_desc and clean_str(unidade) in clean_str(v_desc):
                    score += 15
                    
                if score > 0:
                    candidatas.append({
                        'v_row': v_data,
                        'score': score,
                        'is_diamante': is_diamante_c
                    })
                    
            if not candidatas:
                results.append(base_fail_result)
                continue
                
            candidatas.sort(key=lambda x: x['score'], reverse=True)
            
            def dec(vx):
                if vx is None: return ''
                if isinstance(vx, bytes): return vx.decode('win1252', 'ignore')
                return str(vx)
                
            grupos_unidades = {}
            for cand in candidatas:
                desc_unid = dec(cand["v_row"][4]).upper().strip()
                if not desc_unid: desc_unid = f'V_{cand["v_row"][0]}'
                if desc_unid not in grupos_unidades:
                    grupos_unidades[desc_unid] = []
                grupos_unidades[desc_unid].append(cand)
                
            melhor_match_final = None 
            from itertools import combinations
            
            pdf_venc = str(row.get('dt_vencimento', ''))
            pdf_mes = pdf_venc[3:5] if len(pdf_venc) >= 5 else ''
            pdf_ano = pdf_venc[6:10] if len(pdf_venc) >= 10 else ''
            
            for grupo_key, grupo_vendas in grupos_unidades.items():
                pool_abertas = []
                pool_prazos = []
                
                for cand in grupo_vendas:
                    v_id = int(cand['v_row'][0])
                    cur.execute("SELECT ID, DATA, VALORPARCELA, TOTALPAGO, PARCELA FROM RECEBER WHERE IDVENDA = ? AND (TOTALPAGO IS NULL OR TOTALPAGO = 0)", (v_id,))
                    for ra in cur.fetchall(): pool_abertas.append((ra, cand))
                        
                    cur.execute("""
                        SELECT p.ID, p.DATA, p.VALORPARCELA, vfp.ID
                        FROM VENDAFORMAPAGTOPRAZO p
                        JOIN VENDAFORMAPAGTO vfp ON vfp.ID = p.IDVENDAFORMAPAGTO
                        WHERE vfp.IDVENDA = ?
                    """, (v_id,))
                    for pr in cur.fetchall(): pool_prazos.append((pr, cand))
                        
                pool_abertas.sort(key=lambda x: str(x[0][1]) if x[0][1] else '9999')
                pool_prazos.sort(key=lambda x: str(x[0][1]) if x[0][1] else '9999')
                
                match_perfeito = None
                lista_multipla = []
                mat_type = ""
                
                # PRIORIDADE MÁXIMA 0: DATA BATE ESTREITAMENTE COM A DATA DO PDF e o VALOR BATE.
                for p_tuple in pool_abertas:
                    p, cand = p_tuple
                    p_id, p_venc, p_valor, p_pago, p_parcela = p
                    if float(p_valor or 0) > 0 and (abs(float(p_valor) - total_pago) < 5.0 or abs(float(p_valor) - valor_raiz) < 5.0):
                        db_venc = str(p_venc)
                        if pdf_mes and f'-{pdf_mes}-' in db_venc and pdf_ano in db_venc:
                            match_perfeito = p_tuple
                            mat_type = "PERFEITO_RECEBER_DATA_EXATA"
                            break
                            
                # 1. Match Singular Rápido (Qualquer data)
                if not match_perfeito:
                    for p_tuple in pool_abertas:
                        p, cand = p_tuple
                        if float(p[2] or 0) > 0 and (abs(float(p[2]) - total_pago) < 5.0 or abs(float(p[2]) - valor_raiz) < 5.0):
                            match_perfeito = p_tuple
                            mat_type = "PERFEITO_RECEBER"
                            break
                if not match_perfeito:
                    for pr_tuple in pool_prazos:
                        pr, cand = pr_tuple
                        if float(pr[2] or 0) > 0 and (abs(float(pr[2]) - total_pago) < 5.0 or abs(float(pr[2]) - valor_raiz) < 5.0):
                            match_perfeito = pr_tuple
                            mat_type = "PERFEITO_PROJETADA"
                            break
                            
                # 2. Combinação Múltipla COM JUROS (Aceita variação de Cub/Mora até 30%)
                if not match_perfeito and len(pool_abertas) >= 2:
                    achou_combo = False
                    for combo_tamanho in [2, 3, 4]:
                        if achou_combo or len(pool_abertas) < combo_tamanho: break
                        for combo in combinations(pool_abertas, combo_tamanho):
                            soma_combo = sum(float(it[0][2] or 0) for it in combo)
                            if soma_combo > 0 and soma_combo <= total_pago:
                                diff_rate = abs(total_pago - soma_combo)/soma_combo
                                # Até 100% de margem de juros/cub para soma multipla caso feche as contas antigas
                                if diff_rate < 1.0:
                                    lista_multipla = list(combo)
                                    mat_type = "MULTIPLO_RECEBER"
                                    achou_combo = True
                                    break
                
                # 3. Margem CUB Singular SE DIAMANTE
                if not match_perfeito and not lista_multipla:
                    diamante_no_grupo = any(c['is_diamante'] for c in grupo_vendas)
                    if diamante_no_grupo:
                        for p_tuple in pool_abertas:
                            p, cand = p_tuple
                            p_valor = float(p[2] or 0)
                            if p_valor > 0 and total_pago > p_valor and (abs(total_pago - p_valor) / p_valor) < 5.0:
                                db_venc = str(p[1])
                                if pdf_mes and f'-{pdf_mes}-' in db_venc and pdf_ano in db_venc:
                                    match_perfeito = p_tuple
                                    mat_type = "CUB_RECEBER_DATA_EXATA"
                                    break
                        if not match_perfeito:
                            for p_tuple in pool_abertas:
                                p, cand = p_tuple
                                p_valor = float(p[2] or 0)
                                if p_valor > 0 and total_pago > p_valor and (abs(total_pago - p_valor) / p_valor) < 2.0:
                                    match_perfeito = p_tuple
                                    mat_type = "CUB_RECEBER"
                                    break
                        if not match_perfeito:
                            for pr_tuple in pool_prazos:
                                pr, cand = pr_tuple
                                pr_valor = float(pr[2] or 0)
                                if pr_valor > 0 and total_pago > pr_valor and (abs(total_pago - pr_valor) / pr_valor) < 5.0:
                                    db_venc = str(pr[1])
                                    if pdf_mes and f'-{pdf_mes}-' in db_venc and pdf_ano in db_venc:
                                        match_perfeito = pr_tuple
                                        mat_type = "CUB_PROJETADA_DATA_EXATA"
                                        break
                        if not match_perfeito:
                            for pr_tuple in pool_prazos:
                                pr, cand = pr_tuple
                                pr_valor = float(pr[2] or 0)
                                if pr_valor > 0 and total_pago > pr_valor and (abs(total_pago - pr_valor) / pr_valor) < 2.0:
                                    match_perfeito = pr_tuple
                                    mat_type = "CUB_PROJETADA"
                                    break
                                        
                if match_perfeito:
                    cand = match_perfeito[1]
                    is_ouro = True if unidade and dec(cand['v_row'][4]) and clean_str(unidade) in clean_str(dec(cand['v_row'][4])) else False
                    m_reason = f"Match Diamante Global ({mat_type})" if cand['is_diamante'] else f"Match Ouro Global ({mat_type})"
                    melhor_match_final = { 'type': mat_type, 'db_raw': match_perfeito[0], 'reason': m_reason, 'v_row': cand['v_row'] }
                    break
                elif lista_multipla:
                    mat_type = "MULTIPLO_RECEBER"
                    melhor_match_final = { 'type': mat_type, 'lista': lista_multipla }
                    break
                    
            if melhor_match_final:
                if 'MULTIPLO' in melhor_match_final['type']:
                    lista = melhor_match_final['lista']
                    total_div = total_pago / len(lista)
                    for idx, item in enumerate(lista):
                        p, cand = item
                        p_id, p_venc, p_valor, p_pago, p_parcela = p
                        v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = cand['v_row']
                        
                        venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                        nova_row = dict(row)
                        nova_row['total_pago'] = total_div
                        if idx > 0: nova_row['cpf_cnpj'] = str(nova_row.get('cpf_cnpj','')) + f" [Rateio {idx+1}/{len(lista)}]"
                            
                        results.append({
                            'row': nova_row, 'has_date': has_date, 'matched': True, 'match_reason': f"Cross-Match (Combo {len(lista)} Titulos)", 'status': 'MATCH_PERFEITO', 'id_receber': p_id,
                            'erp_data': {'ID': p_id, 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': venc_str, 'valor_parcela': float(p_valor or 0), 'parcela': dec(p_parcela), 'pago_hoje': float(p_pago or 0)},
                            'proposta_ia': {'novo_total_pago': total_div, 'novo_desconto': float(row.get('descontos', 0) or 0) / len(lista), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0) / len(lista), 'projetada': False}
                        })
                else:    
                    v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = melhor_match_final['v_row']
                    match_reason = melhor_match_final['reason']
                    mat_type = melhor_match_final['type']
                    
                    if 'RECEBER' in mat_type:
                        p_id, p_venc, p_valor, p_pago, p_parcela = melhor_match_final['db_raw']
                        venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                        results.append({
                            'row': row, 'has_date': has_date, 'matched': True, 'match_reason': match_reason, 'status': 'MATCH_PERFEITO', 'id_receber': p_id,
                            'erp_data': {'ID': p_id, 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': venc_str, 'valor_parcela': float(p_valor or 0), 'parcela': dec(p_parcela), 'pago_hoje': float(p_pago or 0)},
                            'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': False}
                        })
                    elif 'PROJETADA' in mat_type:
                        pr_id, pr_data, pr_valor, f_id = melhor_match_final['db_raw']
                        proj_venc = pr_data.strftime('%d/%m/%Y') if hasattr(pr_data, 'strftime') else dec(pr_data)
                        results.append({
                            'row': row, 'has_date': has_date, 'matched': True, 'match_reason': match_reason, 'status': 'PROJETADA_NOVA_LINHA', 'id_receber': None,
                            'erp_data': {'ID': 'PROJ-' + str(pr_id), 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                            'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': float(pr_valor or 0), 'parcela': f'Projeção ERP {pr_id}', 'pago_hoje': 0},
                            'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': True,
                                'proj_payload': {'idvenda': v_id, 'idcliente': c_id, 'idformapagto': f_id, 'idprazopagto': pr_id, 'data_vencimento': pr_data.strftime('%Y-%m-%d') if hasattr(pr_data, 'strftime') else str(pr_data), 'valor_previsto': float(pr_valor or 0), 'referencia': f'Projeção {pr_id}'}
                            }
                        })
            else:
                best_cand = candidatas[0]
                v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = best_cand['v_row']
                
                is_ouro = False
                if comprador_nome and clean_str(comprador_nome) in clean_str(c_nome): is_ouro = True
                elif unidade and v_desc_db and clean_str(unidade) in clean_str(v_desc_db): is_ouro = True
                    
                match_reason = 'Match Ouro (Nome/Unidade) Nativo'
                if best_cand['is_diamante']: match_reason = 'Match Diamante (CPF/CNPJ) Nativo'
                
                pr_id = -1 * (hash(str(v_id) + str(total_pago) + str(row.get('dt_vencimento', ''))) % 1000000)
                proj_venc = str(row.get('dt_vencimento', ''))
                results.append({
                    'row': row, 'has_date': has_date, 'matched': True, 'match_reason': f'{match_reason}', 'status': 'PROJETADA_NOVA_LINHA_NATIVA', 'id_receber': None,
                    'erp_data': {'ID': f'NTV-{abs(pr_id)}', 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                    'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': total_pago, 'parcela': 'Gerada Nativa Extra-Caixa', 'pago_hoje': 0},
                    'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': True, 'nativa_sqlite': True,
                        'proj_payload': {'idvenda': v_id, 'idcliente': c_id, 'data_vencimento': proj_venc, 'valor_previsto': total_pago, 'referencia': 'Baixa Nativa Multi', 'pseudo_id': pr_id}
                    }
                })
'''

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if 'Pesquisa Rápida em RAM (In-Memory Filter)' in line:
            start_idx = i
            
    for i in range(start_idx, len(lines)):
        if 'results.append(base_fail_result)' in lines[i] and 'else:' in lines[i-1]:
            end_idx = i + 1
            break
            
    new_lines = lines[:start_idx] + [new_logic + '\n'] + lines[end_idx:]
    with open('main.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('OK REWRITTEN')
except Exception as e:
    print('ERR', e)
