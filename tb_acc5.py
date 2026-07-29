with open(r'backend\core\services\graph_logic_builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''                            dossie = IFRS15Analyzer.gerar_dossie_temporal(
                                cur_v=cur_v,
                                cur_q=cur_q,
                                cc_empreendimento=emp["cc"],
                                empresa_id=empresa_id,
                                nome_emp=emp.get("nome", "Desconhecido"),'''

good = '''                            c_raw = emp.get("conta_estcon") if str(emp.get("obra_concluida", "N")).strip().upper() == 'S' else emp.get("conta_estand")
                            
                            dossie = IFRS15Analyzer.gerar_dossie_temporal(
                                cur_v=cur_v,
                                cur_q=cur_q,
                                cc_empreendimento=emp["cc"],
                                empresa_id=empresa_id,
                                nome_emp=emp.get("nome", "Desconhecido"),
                                conta_estoque=str(c_raw).strip() if c_raw else "5639",'''

text = text.replace(bad, good)

with open(r'backend\core\services\graph_logic_builder.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

# Add args
text2 = text2.replace('def gerar_dossie_temporal(cls, cur_v, cur_q, cc_empreendimento, empresa_id, nome_emp,', 'def gerar_dossie_temporal(cls, cur_v, cur_q, cc_empreendimento, empresa_id, nome_emp, conta_estoque,')

# Replace the credit query!
bad_query = '''          # Créditos do Questor LCTOGER (Apenas TRANSFERÊNCIA DE CUSTOS)
          cur_q.execute("""
              SELECT EXTRACT(YEAR FROM G.DATALCTOCTB), EXTRACT(MONTH FROM G.DATALCTOCTB), G.VALORLCTOGER, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
              FROM LCTOGER G
              JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
              LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
              WHERE G.CODIGOCENTROCUSTO = ? AND G.CODIGOEMPRESA = ? AND G.NATURLCTOCTB = -1
          """, (cc_empreendimento, empresa_id))'''

good_query = '''          # Créditos Diretamente do LCTOCTB na Conta de Estoque (LCTOGER não registra saída de estoque)
          cur_q.execute("""
              SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), C.VALORLCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
              FROM LCTOCTB C
              LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
              WHERE C.CONTACTBCRED = ? AND C.CODIGOEMPRESA = ? 
          """, (int(conta_estoque) if conta_estoque and str(conta_estoque).isdigit() else 5639, empresa_id))'''

text2 = text2.replace(bad_query, good_query)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text2)

print("Backend LCTOCTB Direct Credit Lookup Patched!")
