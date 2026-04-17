with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Insert the code to fetch Credit from LCTOGER using COMPLHIST matching right after finding RECEIVER map
q_mapa_receb = '''mapa_receb = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_v.fetchall()}'''

q_credito_questor = '''mapa_receb = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_v.fetchall()}
            
            # Pegar Creditos Questor pro Apartamento
            nome_apto = u[1]
            import re
            num_apto_match = re.search(r'\d{1,5}', nome_apto)
            apto_str = num_apto_match.group(0) if num_apto_match else nome_apto
            cur_q.execute("""
                SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), SUM(G.VALORLCTOGER)
                FROM LCTOGER G
                JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
                WHERE G.CODIGOCENTROCUSTO = ? 
                  AND G.CODIGOEMPRESA = ? 
                  AND G.NATURLCTOCTB = 2
                  AND CAST(C.COMPLHIST AS BLOB SUB_TYPE 0) LIKE ?
                GROUP BY 1, 2 ORDER BY 1, 2
            """, (cc_empreendimento, empresa_id, f'%{apto_str}%'))
            mapa_creditos = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_q.fetchall()}'''

text = text.replace(q_mapa_receb, q_credito_questor)

# Append credito_questor to temporal row dictionary
q_linhas = '''"fluxo_recebido": mapa_receb.get(k, 0),'''
new_q_linhas = '''"fluxo_recebido": mapa_receb.get(k, 0),
                        "credito_questor": mapa_creditos.get(k, 0),'''

text = text.replace(q_linhas, new_q_linhas)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Backend API to extract Credit")
