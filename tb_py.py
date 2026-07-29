with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# REWRITE gerar_dossie_temporal
new_func = '''    @staticmethod
    def gerar_dossie_temporal(cc_empreendimento: int, empresa_id: int=959, limite_amostra: int=5):
        try:
            from main import get_conn
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from main import get_conn

        conn_v = get_conn("vulcano")
        cur_v = conn_v.cursor()
        
        # 1. Pegar Empreendimento + Orcamento
        cur_v.execute("SELECT ID, NOME, METRAGEMTOTAL, CUSTOORCADO FROM EMPREENDIMENTO WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ?", (cc_empreendimento, empresa_id))
        emp = cur_v.fetchone()
        if not emp:
            conn_v.close()
            return {"status": "error", "message": "Empreendimento nao encontrado para o CC informado"}
            
        emp_id, nome_emp = emp[0], str(emp[1] or '')
        metragem_total, orcado = float(emp[2] or 1.0), float(emp[3] or 0.0)
        
        # 1.1 Pegar POC do Projeto
        cur_v.execute("SELECT EXTRACT(YEAR FROM PERIODO), EXTRACT(MONTH FROM PERIODO), PERCENTUAL FROM POC WHERE ID_EMPREENDIMENTO = ?", (emp_id,))
        mapa_poc = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0.0) for r in cur_v.fetchall()}
        
        # 1.2 Pegar CUB
        cur_v.execute("SELECT EXTRACT(YEAR FROM MES), EXTRACT(MONTH FROM MES), PERCENTUAL_VARIACAO FROM INDICE_REAJUSTE_TABELA WHERE ID_INDICE_REAJUSTE = 1")
        mapa_cub = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0.0) for r in cur_v.fetchall()}
        
        # 2. Pegar Unidades (Adicionado TOTALVENDA vs POC Informado)
        cur_v.execute("""
            SELECT FIRST ? U.ID, U.DESCRICAO, U.METRAGEM, V.DTOPER, V.TOTALVENDA
            FROM UNIDADE U
            JOIN BLOCO B ON B.ID = U.IDBLOCO
            JOIN VENDAUNIDADE VU ON VU.IDUNIDADE = U.ID
            JOIN VENDA V ON V.ID = VU.IDVENDA
            WHERE B.IDEMPREENDIMENTO = ? AND COALESCE(V.DISTRATO, 'N') <> 'S'
            ORDER BY U.ID
        """, (limite_amostra, emp_id))
        unidades = cur_v.fetchall()
        
        # Custo por Mes (Questor)
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute("""
            SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOGER) 
            FROM LCTOGER 
            WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATURLCTOCTB = 1
            GROUP BY 1, 2 ORDER BY 1, 2
        """, (cc_empreendimento, empresa_id))
        custos_questor = [{"ano": int(r[0]), "mes": int(r[1]), "custo": float(r[2] or 0)} for r in cur_q.fetchall()]
        conn_q.close()
        
        # Aglutinar e cruzar arrays mensais em um Dossiê Massivo Temporal
        dossie = {
            "cc_empreendimento": cc_empreendimento,
            "empreendimento": nome_emp,
            "metragem_total": metragem_total,
            "custo_orcado": orcado,
            "custo_total_obra_mensal": custos_questor,
            "amostra_unidades": []
        }
        
        for u in unidades:
            u_id, u_desc, u_metragem, u_dt_venda, u_tvenda = u[0], str(u[1] or ''), float(u[2] or 0.0), str(u[3] or '')[:10], float(u[4] or 0.0)
            fracao = u_metragem / metragem_total if metragem_total > 0 else 0
            
            # Pegar Recebimentos do Apto (Fluxo)
            cur_v.execute("""
                SELECT EXTRACT(YEAR FROM DATA), EXTRACT(MONTH FROM DATA), SUM(VALORPARCELA)
                FROM RECEBER R
                JOIN VENDA V ON V.ID = R.IDVENDA
                JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
                WHERE VU.IDUNIDADE = ? AND DATA IS NOT NULL
                GROUP BY 1, 2 ORDER BY 1, 2
            """, (u_id,))
            mapa_receb = {f"{int(r[0])}-{int(r[1])}": float(r[2] or 0) for r in cur_v.fetchall()}
            
            # Racional Híbrido Temporal
            linhas_temporal = []
            for c in custos_questor:
                k = f"{c['ano']}-{c['mes']}"
                custo_v2 = c["custo"] * fracao
                custo_v1 = custo_v2 * (mapa_poc.get(k, 0) / 100) if mapa_poc.get(k, 0) > 0 else 0
                
                linhas_temporal.append({
                    "ano": c["ano"], 
                    "mes": c["mes"], 
                    "custo_questor": c["custo"],
                    "custo_v2_ifrs": round(custo_v2, 2),
                    "custo_v1_legacy": round(custo_v1, 2),
                    "poc_mes": mapa_poc.get(k, 0.0),
                    "cub_mes": mapa_cub.get(k, 0.0),
                    "fluxo_recebido": mapa_receb.get(k, 0.0)
                })
                
            dossie["amostra_unidades"].append({
                "unidade": u_desc,
                "metragem": u_metragem,
                "data_venda": u_dt_venda,
                "valor_unidade": u_tvenda,
                "fracao_obra": round(fracao * 100, 4),
                "grid_temporal": linhas_temporal
            })
            
        conn_v.close()
        return {"status": "success", "dossie": dossie}
'''

text = re.sub(r'    @staticmethod\s*def gerar_dossie_temporal\b.*?return \{"status": "success", "dossie": dossie\}', new_func, text, flags=re.DOTALL)

with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Combinatorial Analyzer massive extractor")
