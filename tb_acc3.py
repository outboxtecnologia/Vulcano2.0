with open(r'backend\core\services\combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''          # Créditos do Questor LCTOGER (NATURLCTOCTB = -1)
          cur_q.execute("""
              SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOGER) 
              FROM LCTOGER 
              WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATURLCTOCTB = -1
              GROUP BY 1, 2 ORDER BY 1, 2
          """, (cc_empreendimento, empresa_id))
          creditos_questor_global = [{"ano": int(r[0]), "mes": int(r[1]), "credito": float(r[2] or 0)} for r in cur_q.fetchall()]'''

good = '''          # Créditos do Questor LCTOGER (Apenas TRANSFERÊNCIA DE CUSTOS)
          cur_q.execute("""
              SELECT EXTRACT(YEAR FROM G.DATALCTOCTB), EXTRACT(MONTH FROM G.DATALCTOCTB), G.VALORLCTOGER, CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), H.DESCRHISTCTB
              FROM LCTOGER G
              JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
              LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
              WHERE G.CODIGOCENTROCUSTO = ? AND G.CODIGOEMPRESA = ? AND G.NATURLCTOCTB = -1
          """, (cc_empreendimento, empresa_id))
          
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

text = text.replace(bad, good)

# Make sure to catch also the 'Ê' vs 'E' in the replace if needed

with open(r'backend\core\services\combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend Transferencia de Custos Patched!")
