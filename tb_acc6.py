with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''          cur_q.execute("""
              SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), C.VALORLCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
              FROM LCTOCTB C
              LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
              WHERE C.CONTACTBCRED = ? AND C.CODIGOEMPRESA = ? 
          """, (int(conta_estoque) if conta_estoque and str(conta_estoque).isdigit() else 5639, empresa_id))
          
          creditos_agrupados = {}
          for (v_ano, v_mes, v_val, h_compl, h_desc) in cur_q.fetchall():
              if isinstance(h_compl, (bytes, bytearray)):
                  t_compl = h_compl.decode("cp1252", "ignore")
              elif hasattr(h_compl, "read"):
                  t_compl = h_compl.read().decode("cp1252", "ignore")
              else:
                  t_compl = str(h_compl or "")
                  
              h_full = f"{str(h_desc or '')} {t_compl}".upper().replace('Ê', 'E').strip()
              
              if h_full.startswith('TRANSFERENCIA DE CUSTO'):
                  k = f"{int(v_ano)}-{int(v_mes)}"
                  creditos_agrupados[k] = creditos_agrupados.get(k, 0.0) + float(v_val or 0.0)
                  
          creditos_questor_global = [{"ano": int(k.split('-')[0]), "mes": int(k.split('-')[1]), "credito": float(v)} for k, v in creditos_agrupados.items()]'''

good = '''          # Créditos Diretamente do LCTOCTB na Conta de Estoque
          cur_q.execute("""
              SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), C.VALORLCTOCTB, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
              FROM LCTOCTB C
              LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
              WHERE C.CONTACTBCRED = ? AND C.CODIGOEMPRESA = ? 
          """, (int(conta_estoque) if conta_estoque and str(conta_estoque).isdigit() else 5639, empresa_id))
          
          creditos_questor_detalhes = []
          for (v_ano, v_mes, v_val, h_compl, h_desc) in cur_q.fetchall():
              if isinstance(h_compl, (bytes, bytearray)):
                  t_compl = h_compl.decode("cp1252", "ignore")
              elif hasattr(h_compl, "read"):
                  t_compl = h_compl.read().decode("cp1252", "ignore")
              else:
                  t_compl = str(h_compl or "")
                  
              h_full = f"{str(h_desc or '')} {t_compl}".upper().replace('Ê', 'E').strip()
              
              creditos_questor_detalhes.append({
                  "ano": int(v_ano), 
                  "mes": int(v_mes), 
                  "valor": float(v_val or 0.0), 
                  "str": h_full
              })
              
          creditos_questor_global = [] # Just to prevent undefined vars later if any'''

text = text.replace(bad, good)

# Now fix the mapper logic inside the loop!
bad2 = '''              num_apto_match = re.search(r'\d{1,5}', nome_apto)
              apto_str = num_apto_match.group(0) if num_apto_match else nome_apto
              # Q. Crédito é a fração dos créditos globais do CC
              mapa_creditos = {f"{c['ano']}-{c['mes']}": c['credito'] * fracao for c in creditos_questor_global}'''

good2 = '''              num_apto_match = re.search(r'\d{1,5}', nome_apto)
              apto_str = num_apto_match.group(0) if num_apto_match else nome_apto
              
              # Busca EXATAMENTE os creditos lançados contra a unidade na Contabilidade (Sem fracionar)
              mapa_creditos = {}
              for cr in creditos_questor_detalhes:
                  # Checa se ex: APTO 201 ta no historico ('TRANSFERENCIA DE CUSTO' pode ser parcial ou total, ou as vezes n tem a palavra exata)
                  # Usamos a string da unidade pra bindar os créditos reais da 5639 pra ela!
                  if str(apto_str) in cr["str"] or str(nome_apto).upper() in cr["str"]:
                      k = f"{cr['ano']}-{cr['mes']}"
                      mapa_creditos[k] = mapa_creditos.get(k, 0.0) + cr["valor"]'''

text = text.replace(bad2, good2)

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend LCTOCTB Exact Match By Unit Patched!")
