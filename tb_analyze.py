import json
import sqlite3
import datetime

# This script will be appended to combinatorial_analyzer.py
patch = '''

class IFRS15Analyzer:
    @staticmethod
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
        
        # 1. Pegar Empreendimento
        cur_v.execute("SELECT ID, NOME, METRAGEMTOTAL FROM EMPREENDIMENTO WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ?", (cc_empreendimento, empresa_id))
        emp = cur_v.fetchone()
        if not emp:
            conn_v.close()
            return {"status": "error", "message": "Empreendimento nao encontrado para o CC informado"}
            
        emp_id, nome_emp = emp[0], str(emp[1] or '')
        metragem_total = float(emp[2] or 1.0)
        
        # 2. Pegar as N Unidades Vendidas
        cur_v.execute("""
            SELECT FIRST ? U.ID, U.DESCRICAO, U.METRAGEM, V.DATAVENDA
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
        custos_mensais = [{"ano": int(r[0]), "mes": int(r[1]), "custo": float(r[2] or 0)} for r in cur_q.fetchall()]
        conn_q.close()
        
        dossie = {
            "cc_empreendimento": cc_empreendimento,
            "empreendimento": nome_emp,
            "metragem_total": metragem_total,
            "custo_total_obra_mensal": custos_mensais,
            "amostra_unidades": []
        }
        
        for u in unidades:
            u_id, u_desc, u_metragem, u_data_venda = u[0], str(u[1] or ''), float(u[2] or 0.0), str(u[3])[:10]
            fracao = u_metragem / metragem_total if metragem_total > 0 else 0
            
            # Pegar Recebimentos do Apto (Fluxo)
            cur_v.execute("""
                SELECT EXTRACT(YEAR FROM DATAPAGTO), EXTRACT(MONTH FROM DATAPAGTO), SUM(VALORPAGO)
                FROM RECEBER
                WHERE IDUNIDADE = ? AND DATAPAGTO IS NOT NULL
                GROUP BY 1, 2 ORDER BY 1, 2
            """, (u_id,))
            recebimentos = [{"ano": int(r[0]), "mes": int(r[1]), "valor": float(r[2] or 0)} for r in cur_v.fetchall()]
            
            # Vulcano Rationale
            estimativa_custo_mensal = []
            for c in custos_mensais:
                estimativa_custo_mensal.append({
                    "ano": c["ano"], 
                    "mes": c["mes"], 
                    "custo_ifrs_esperado": round(c["custo"] * fracao, 2)
                })
                
            dossie["amostra_unidades"].append({
                "unidade": u_desc,
                "metragem": u_metragem,
                "data_venda": u_data_venda,
                "fracao_obra": round(fracao * 100, 4),
                "racional_custeio_ifrs_mensal": estimativa_custo_mensal,
                "fluxo_financeiro_recebimentos": recebimentos
            })
            
        conn_v.close()
        # POC mes a mes is complex, skipping for POC db lookup for now since it requires sqlite sync
        return {"status": "success", "dossie": dossie}

'''

with open(r'backend/core/services/combinatorial_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

if "IFRS15Analyzer" not in text:
    with open(r'backend/core/services/combinatorial_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(text + "\n" + patch)
    print("IFRS15Analyzer applied to combinatorial_analyzer.py")
else:
    print("IFRS15Analyzer already exists.")
