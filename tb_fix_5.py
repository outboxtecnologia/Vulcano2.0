with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''            # Busca Ampla de Creditos do Apartamento (Receitas/CPV Grupo 3 ou 5)
            cur_q.execute("""
                SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOCTB)
                FROM LCTOCTB
                WHERE CODIGOEMPRESA = ? 
                  AND CAST(COMPLHIST AS BLOB SUB_TYPE 0) LIKE ?
                  AND CONTACTBCRED IS NOT NULL 
                  AND (CAST(CONTACTBCRED AS VARCHAR(10)) LIKE '3%' OR CAST(CONTACTBCRED AS VARCHAR(10)) LIKE '5%')
                GROUP BY 1, 2 ORDER BY 1, 2
            """, (empresa_id, f'%{apto_str}%'))
            mapa_creditos = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_q.fetchall()}'''

new_logic = '''            # Busca Focada: Creditos do Apartamento NA CONTA ALVO sendo auditada
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

text = text.replace(old_logic, new_logic)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Reverted to Safe Account Focussed Credit Logic!")
