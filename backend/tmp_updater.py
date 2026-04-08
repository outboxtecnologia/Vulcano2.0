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
                
            # Ordena da maior pontuação para a menor
            candidatas.sort(key=lambda x: x['score'], reverse=True)
            
            melhor_match_final = None # Type: dict with keys
            
            def dec(vx):
                if vx is None: return ''
                if isinstance(vx, bytes): return vx.decode('win1252', 'ignore')
                return str(vx)
            
            # Loop de Busca Profunda (Firebird): procuraremos parcela aberta em todas candidatas, parando na primeira matemática perfeita
            for cand in candidatas:
                v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = cand['v_row']
                is_diamante = cand['is_diamante']
                
                is_ouro = False
                if comprador_nome and clean_str(comprador_nome) in clean_str(c_nome):
                    is_ouro = True
                elif unidade and v_desc_db and clean_str(unidade) in clean_str(v_desc_db):
                    is_ouro = True
                    
                match_reason = 'Match Prata (Matemática)'
                if is_diamante:
                    match_reason = 'Match Diamante (CPF/CNPJ)'
                elif is_ouro:
                    match_reason = 'Match Ouro (Nome/Unidade)'
                    
                cur.execute('SELECT ID, DATA, VALORPARCELA, TOTALPAGO, PARCELA FROM RECEBER WHERE IDVENDA = ? AND (TOTALPAGO IS NULL OR TOTALPAGO = 0)', (int(v_id),))
                abertas = cur.fetchall()
                
                match_perfeito = None
                for p in abertas:
                    p_id, p_venc, p_valor, p_pago, p_parcela = p
                    if (float(p_valor or 0) > 0 and (abs(float(p_valor) - total_pago) < 5.0 or abs(float(p_valor) - valor_raiz) < 5.0)):
                        match_perfeito = p
                        break
                    parcela_pdf = str(row.get('parcela', '')).strip()
                    if parcela_pdf and str(p_parcela).strip() == parcela_pdf:
                        match_perfeito = p
                        break
                        
                # Algoritmo Probabilístico
                if not match_perfeito and len(abertas) > 0:
                    abertas.sort(key=lambda x: str(x[1]) if x[1] else '9999')
                    
                    if match_reason != 'Match Prata (Matemática)':
                        for p in abertas:
                            p_id, p_venc, p_valor, p_pago, p_parcela = p
                            if float(p_valor or 0) > 0:
                                diff_ratio = abs(total_pago - float(p_valor)) / float(p_valor)
                                if diff_ratio < 1.0:
                                    match_perfeito = p
                                    match_reason = f'{match_reason} com CUB/Mora'
                                    break
                                    
                    if not match_perfeito and len(abertas) > 1:
                        sum_2 = float(abertas[0][2] or 0) + float(abertas[1][2] or 0)
                        if abs(sum_2 - total_pago) < 10.0:
                            match_perfeito = abertas[0]
                            match_reason = 'Match Probabilístico (Soma de 2 Parcelas)'
                            
                    if not match_perfeito and is_diamante:
                        pdf_venc = str(row.get('dt_vencimento', ''))
                        pdf_mes = pdf_venc[3:5] if len(pdf_venc) >= 5 else ''
                        if pdf_mes:
                            for p in abertas:
                                db_venc = str(p[1])
                                if f'-{pdf_mes}-' in db_venc:
                                    match_perfeito = p
                                    match_reason = 'Match Diamante (Forçado por Mês)'
                                    break
                                    
                if match_perfeito:
                    melhor_match_final = {
                        'type': 'PERFEITO',
                        'match_perfeito': match_perfeito,
                        'reason': match_reason,
                        'v_row': cand['v_row']
                    }
                    break # FIM! Achou na primeria venda que bate
                    
                # Se não achou em aberto, tenta PROJEÇÃO
                if not match_perfeito:
                    cur.execute("""
                        SELECT p.ID, p.DATA, p.VALORPARCELA, vfp.ID
                        FROM VENDAFORMAPAGTOPRAZO p
                        JOIN VENDAFORMAPAGTO vfp ON vfp.ID = p.IDVENDAFORMAPAGTO
                        WHERE vfp.IDVENDA = ?
                    """, (int(v_id),))
                    prazos = cur.fetchall()
                    proj_match = None
                    for pr in prazos:
                        pr_id, pr_data, pr_valor, f_id = pr
                        if float(pr_valor or 0) > 0 and (abs(float(pr_valor) - total_pago) < 5.0 or abs(float(pr_valor) - valor_raiz) < 5.0):
                            proj_match = pr
                            break
                            
                    if not proj_match and len(prazos) > 0 and match_reason != 'Match Prata (Matemática)':
                        for pr in prazos:
                            pr_id, pr_data, pr_valor, f_id = pr
                            if float(pr_valor or 0) > 0:
                                diff_ratio = abs(total_pago - float(pr_valor)) / float(pr_valor)
                                if diff_ratio < 1.0:
                                    proj_match = pr
                                    match_reason = f'{match_reason} com CUB/Mora na Projeção'
                                    break
                            
                    if proj_match:
                        melhor_match_final = {
                            'type': 'PROJETADA',
                            'proj_match': proj_match,
                            'reason': match_reason,
                            'v_row': cand['v_row']
                        }
                        break
                        
            # Cenas Pós-Loop:
            if melhor_match_final:
                v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = melhor_match_final['v_row']
                match_reason = melhor_match_final['reason']
                
                if melhor_match_final['type'] == 'PERFEITO':
                    p_id, p_venc, p_valor, p_pago, p_parcela = melhor_match_final['match_perfeito']
                    venc_str = p_venc.strftime('%d/%m/%Y') if hasattr(p_venc, 'strftime') else dec(p_venc)
                    results.append({
                        'row': row, 'has_date': has_date, 'matched': True, 'match_reason': match_reason, 'status': 'MATCH_PERFEITO', 'id_receber': p_id,
                        'erp_data': {'ID': p_id, 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                        'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': venc_str, 'valor_parcela': float(p_valor or 0), 'parcela': dec(p_parcela), 'pago_hoje': float(p_pago or 0)},
                        'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': False}
                    })
                elif melhor_match_final['type'] == 'PROJETADA':
                    pr_id, pr_data, pr_valor, f_id = melhor_match_final['proj_match']
                    proj_venc = pr_data.strftime('%d/%m/%Y') if hasattr(pr_data, 'strftime') else dec(pr_data)
                    results.append({
                        'row': row, 'has_date': has_date, 'matched': True, 'match_reason': match_reason, 'status': 'PROJETADA_NOVA_LINHA', 'id_receber': None,
                        'erp_data': {'ID': 'PROJ-' + str(pr_id), 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                        'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': float(pr_valor or 0), 'parcela': f'Nova Projeção {pr_id}', 'pago_hoje': 0},
                        'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': True,
                            'proj_payload': {'idvenda': v_id, 'idcliente': c_id, 'idformapagto': f_id, 'idprazopagto': pr_id, 'data_vencimento': pr_data.strftime('%Y-%m-%d') if hasattr(pr_data, 'strftime') else str(pr_data), 'valor_previsto': float(pr_valor or 0), 'referencia': f'Projecao {pr_id}'}
                        }
                    })
            else:
                best_cand = candidatas[0]
                v_id, c_nome, c_id, c_cnpj_db, v_desc_db, e_nome_db = best_cand['v_row']
                
                is_ouro = False
                if comprador_nome and clean_str(comprador_nome) in clean_str(c_nome): is_ouro = True
                elif unidade and v_desc_db and clean_str(unidade) in clean_str(v_desc_db): is_ouro = True
                    
                match_reason = 'Match Prata (Matemática)'
                if best_cand['is_diamante']: match_reason = 'Match Diamante (CPF/CNPJ)'
                elif is_ouro: match_reason = 'Match Ouro (Nome/Unidade)'
                
                if match_reason != 'Match Prata (Matemática)':
                    pr_id = -1 * (hash(str(v_id) + str(total_pago) + str(row.get('dt_vencimento', ''))) % 1000000)
                    proj_venc = str(row.get('dt_vencimento', ''))
                    results.append({
                        'row': row, 'has_date': has_date, 'matched': True, 'match_reason': f'{match_reason} (Nativo)', 'status': 'PROJETADA_NOVA_LINHA_NATIVA', 'id_receber': None,
                        'erp_data': {'ID': f'NTV-{abs(pr_id)}', 'CLIENTE_NOME': dec(c_nome), 'DESCUNIDIMOB': dec(v_desc_db), 'EMPREENDIMENTO': dec(e_nome_db)},
                        'db_estado_atual': {'venda': v_id, 'cliente': dec(c_nome), 'vencimento': proj_venc, 'valor_parcela': total_pago, 'parcela': 'Gerada Nativa', 'pago_hoje': 0},
                        'proposta_ia': {'novo_total_pago': total_pago, 'novo_desconto': float(row.get('descontos', 0) or 0), 'novo_acrescimo': float(row.get('acrescimos_variacoes', 0) or 0), 'projetada': True, 'nativa_sqlite': True,
                            'proj_payload': {'idvenda': v_id, 'idcliente': c_id, 'data_vencimento': proj_venc, 'valor_previsto': total_pago, 'referencia': 'Baixa Nativa', 'pseudo_id': pr_id}
                        }
                    })
                else:
                    results.append(base_fail_result)
'''

def main():
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_idx = -1
        end_idx = -1
        for i, line in enumerate(lines):
            if 'Pesquisa Rápida em RAM (In-Memory Filter)' in line:
                start_idx = i
            if 'else:' in line and 'Falha Matemática' in lines[i+1]:
                end_idx = i + 2
                
        if start_idx == -1 or end_idx == -1:
            print('Indexes not found', start_idx, end_idx)
            return
            
        new_lines = lines[:start_idx] + [new_logic + '\n'] + lines[end_idx:]
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        print('Logic rewritten successfully.')
    except Exception as e:
        print(e)
main()
