with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

old_1 = '''        cur_q.execute("""
            SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOGER) 
            FROM LCTOGER 
            WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATURLCTOCTB = 1
            GROUP BY 1, 2 ORDER BY 1, 2
        """, (cc_empreendimento, empresa_id))
        custos_questor = [{"ano": int(r[0]), "mes": int(r[1]), "custo": float(r[2] or 0)} for r in cur_q.fetchall()]'''

new_1 = '''        cur_q.execute("""
            SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOGER) 
            FROM LCTOGER 
            WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATURLCTOCTB = 1
            GROUP BY 1, 2 ORDER BY 1, 2
        """, (cc_empreendimento, empresa_id))
        custos_questor = [{"ano": int(r[0]), "mes": int(r[1]), "custo": float(r[2] or 0)} for r in cur_q.fetchall()]
        
        # Créditos do Questor LCTOGER (NATURLCTOCTB = -1)
        cur_q.execute("""
            SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOGER) 
            FROM LCTOGER 
            WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATURLCTOCTB = -1
            GROUP BY 1, 2 ORDER BY 1, 2
        """, (cc_empreendimento, empresa_id))
        creditos_questor_global = [{"ano": int(r[0]), "mes": int(r[1]), "credito": float(r[2] or 0)} for r in cur_q.fetchall()]'''

text = text.replace(old_1, new_1)


old_2 = '''            # Busca Focada: Creditos do Apartamento NA CONTA ALVO sendo auditada
            if num_conta:
                cur_q.execute("""
                    SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOCTB)
                    FROM LCTOCTB
                    WHERE CODIGOEMPRESA = ? 
                      AND CONTACTBCRED = ?
                      AND CAST(COMPLHIST AS BLOB SUB_TYPE 0) LIKE ?
                    GROUP BY 1, 2 ORDER BY 1, 2
                """, (empresa_id, num_conta, f'%{apto_str}%'))
                mapa_creditos = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_q.fetchall()}
            else:
                mapa_creditos = {}'''

new_2 = '''            # Q. Crédito é a fração dos créditos globais do CC
            mapa_creditos = {f"{c['ano']}-{c['mes']}": c['credito'] * fracao for c in creditos_questor_global}'''

text = text.replace(old_2, new_2)


old_3 = '''for c in custos_questor: chaves_unicas.add(f"{c['ano']}-{c['mes']}")'''
new_3 = '''for c in custos_questor: chaves_unicas.add(f"{c['ano']}-{c['mes']}")
            for c in creditos_questor_global: chaves_unicas.add(f"{c['ano']}-{c['mes']}")'''

text = text.replace(old_3, new_3)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Combinatorial Analyzer to map LCTOGER Credits directly via Fraction!")
