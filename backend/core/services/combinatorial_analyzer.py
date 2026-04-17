# -*- coding: utf-8 -*-
# Regra de negócio obrigatória:
# O cross-match combinatório SÓ soma valores de mesma direção (positiva).
# Não é permitido inverter o sinal de um lançamento para forçar um match D↔C.
# Para contas 5653/5665/5666, o indexador é APTO+número (já filtrado upstream).
import math
from itertools import combinations

class CombinatorialAnalyzer:
    @staticmethod
    def run_1_to_n(c_id, qs_livres, cv_v, _adicionar_match, _verificar_anomalia_cub):
        """
        Para cada Q órfão, tenta encontrar 1..N lançamentos V que somem o mesmo valor.
        Soma direta (sem inversão de sinal): só combina lançamentos com mesmo valor positivo.
        """
        qs_restantes = sorted(qs_livres, key=lambda x: x["valor"], reverse=True)
        for q in qs_restantes:
            if q.get("_usado", False): continue
            encontrou = False
            # Pool: apenas Vs ainda livres cujo valor individual não supera o Q com folga
            v_pool = [v for v in cv_v if not v.get("_usado", False)
                      and abs(v["valor"]) <= abs(q["valor"]) * 1.05 + 5.0]

            if len(v_pool) > 40: limit_r = 2
            elif len(v_pool) > 15: limit_r = 3
            else: limit_r = min(4, len(v_pool) + 1)

            for r in range(1, limit_r):
                for comb in combinations(v_pool, r):
                    # Soma direta — sem inversão de sinal
                    v_eval = sum(x["valor"] for x in comb)
                    diff = abs(v_eval - q["valor"])

                    cub_explicacao = _verificar_anomalia_cub(comb, diff)

                    if math.isclose(v_eval, q["valor"], rel_tol=0.05, abs_tol=5.0) or cub_explicacao:
                        c_nomes = " + ".join(f"c/{x['conta']}" for x in comb)

                        if cub_explicacao:
                            sug_str = (f"Tolerância Isolada ({c_id}): {cub_explicacao} "
                                       f"| Lançamentos Questor excluíam variação ({c_nomes})")
                        else:
                            sug_str = (f"Soma Direta ({c_id} | 1:N): "
                                       f"Lançamentos [{c_nomes}] somam e equivalem ao Questor")

                        _adicionar_match([q], list(comb), "SUBSET_SUM", sug_str)
                        encontrou = True
                        break
                if encontrou: break

    @staticmethod
    def run_n_to_1(c_id, vs_livres, cv_q, _adicionar_match, _verificar_anomalia_cub):
        """
        Para cada V órfão, tenta encontrar 1..N lançamentos Q que somem o mesmo valor.
        Soma direta (sem inversão de sinal).
        """
        vs_restantes = sorted(
            [v for v in vs_livres if not v.get("_usado", False)],
            key=lambda x: x["valor"], reverse=True
        )
        for v in vs_restantes:
            if v.get("_usado", False): continue
            encontrou = False
            q_pool = [q for q in cv_q if not q.get("_usado", False)
                      and abs(q["valor"]) <= abs(v["valor"]) * 1.05 + 5.0]

            if len(q_pool) > 40: limit_rq = 2
            elif len(q_pool) > 15: limit_rq = 3
            else: limit_rq = min(4, len(q_pool) + 1)

            for r in range(1, limit_rq):
                for comb in combinations(q_pool, r):
                    # Soma direta — sem inversão de sinal
                    v_eval = sum(x["valor"] for x in comb)
                    diff = abs(v_eval - v["valor"])

                    cub_explicacao = _verificar_anomalia_cub([v], diff)

                    if math.isclose(v_eval, v["valor"], rel_tol=0.05, abs_tol=5.0) or cub_explicacao:
                        if cub_explicacao:
                            sug_str = (f"Tolerância Isolada ({c_id}): {cub_explicacao} "
                                       f"| O Questor ignorava o repasse da variação real.")
                        else:
                            c_nomes = " + ".join(f"c/{x['conta']}" for x in comb)
                            sug_str = (f"Soma Direta ({c_id} | N:1): "
                                       f"Lançamentos Questor [{c_nomes}] somam e batem com o Vulcano")

                        _adicionar_match(list(comb), [v], "SUBSET_SUM_INV", sug_str)
                        encontrou = True
                        break
                if encontrou: break



class IFRS15Analyzer:
    @staticmethod
    def gerar_dossie_temporal(cc_empreendimento: int, empresa_id: int=959, conta_alvo: str=None, limite_amostra: int=5):
        num_conta = None
        if conta_alvo:
            import re
            m = re.search(r'\b(\d{3,6})\b', conta_alvo)
            if m:
                num_conta = int(m.group(1))

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
        
        # Créditos do Questor LCTOGER (NATURLCTOCTB = -1)
        cur_q.execute("""
            SELECT EXTRACT(YEAR FROM DATALCTOCTB), EXTRACT(MONTH FROM DATALCTOCTB), SUM(VALORLCTOGER) 
            FROM LCTOGER 
            WHERE CODIGOCENTROCUSTO = ? AND CODIGOEMPRESA = ? AND NATURLCTOCTB = -1
            GROUP BY 1, 2 ORDER BY 1, 2
        """, (cc_empreendimento, empresa_id))
        creditos_questor_global = [{"ano": int(r[0]), "mes": int(r[1]), "credito": float(r[2] or 0)} for r in cur_q.fetchall()]
        
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
            
            # Pegar Creditos Questor pro Apartamento
            nome_apto = u[1]
            import re
            num_apto_match = re.search(r'\d{1,5}', nome_apto)
            apto_str = num_apto_match.group(0) if num_apto_match else nome_apto
            mapa_creditos = {}
            mapa_creditos_detalhes = {}
            for cr in creditos_questor_detalhes:
                if str(apto_str) in cr["str"] or str(nome_apto).upper() in cr["str"]:
                    k = f"{cr['ano']}-{cr['mes']}"
                    mapa_creditos[k] = mapa_creditos.get(k, 0.0) + cr["valor"]
                    mapa_creditos_detalhes.setdefault(k, []).append(cr)
            
            # Racional Híbrido Temporal
            linhas_temporal = []
            u_dt_v_str = str(u_dt_venda).strip()
            u_ano_venda = int(u_dt_v_str[:4]) if len(u_dt_v_str) >= 4 and u_dt_v_str[:4].isdigit() else 9999
            u_mes_venda = int(u_dt_v_str[5:7]) if len(u_dt_v_str) >= 7 and u_dt_v_str[5:7].isdigit() else 12

            acumulado_v2 = 0
            acumulado_v1 = 0

            chaves_unicas = set()
            for c in custos_questor: chaves_unicas.add(f"{c['ano']}-{c['mes']}")
            for c in creditos_questor_global: chaves_unicas.add(f"{c['ano']}-{c['mes']}")
            for k in mapa_receb.keys(): chaves_unicas.add(k)
            for k in mapa_creditos.keys(): chaves_unicas.add(k)
            
            meses_ordenados = sorted([ {"ano": int(k.split('-')[0]), "mes": int(k.split('-')[1])} for k in chaves_unicas ], key=lambda x: (x["ano"], x["mes"]))

            acumulado_linha_questor = 0
            acumulado_linha_questor_credito = 0
            acumulado_linha_v2 = 0
            for c in meses_ordenados:
                k = f"{c['ano']}-{c['mes']}"
                custo_orig = next((cq["custo"] for cq in custos_questor if cq["ano"] == c["ano"] and cq["mes"] == c["mes"]), 0)
                custo_fis = custo_orig * fracao
                custo_fis_v1 = custo_fis * (mapa_poc.get(k, 0) / 100) if mapa_poc.get(k, 0) > 0 else 0
                
                is_before_sale = (c['ano'] < u_ano_venda) or (c['ano'] == u_ano_venda and c['mes'] < u_mes_venda)
                is_sale_month = (c['ano'] == u_ano_venda and c['mes'] == u_mes_venda)

                if is_before_sale:
                    acumulado_v2 += custo_fis
                    acumulado_v1 += custo_fis_v1
                    custo_v2 = 0
                    custo_v1 = 0
                elif is_sale_month:
                    custo_v2 = custo_fis + acumulado_v2
                    custo_v1 = custo_fis_v1 + acumulado_v1
                    acumulado_v2 = 0
                    acumulado_v1 = 0
                else:
                    custo_v2 = custo_fis
                    custo_v1 = custo_fis_v1

                custo_questor_fracionado = custo_orig * (fracao * 100) / 100
                acumulado_linha_questor += custo_questor_fracionado
                acumulado_linha_questor_credito += mapa_creditos.get(k, 0.0)
                acumulado_linha_v2 += custo_v2

                linhas_temporal.append({
                    "ano": c["ano"], 
                    "mes": c["mes"], 
                    "custo_questor": custo_orig,
                    "custo_questor_fracionado": custo_questor_fracionado,
                    "custo_questor_acumulado": acumulado_linha_questor,
                    "custo_v2_ifrs": round(custo_v2, 2),
                    "custo_v2_ifrs_acumulado": round(acumulado_linha_v2, 2),
                    "custo_v1_legacy": round(custo_v1, 2),
                    "poc_mes": mapa_poc.get(k, 0.0),
                    "cub_mes": mapa_cub.get(k, 0.0),
                    "fluxo_recebido": mapa_receb.get(k, 0.0),
                    "credito_questor": mapa_creditos.get(k, 0.0),
                    "credito_questor_acumulado": acumulado_linha_questor_credito,
                    "questor_creditos_raw": mapa_creditos_detalhes.get(k, [])
                })
                
            dossie["amostra_unidades"].append({
                "unidade": u_desc,
                "metragem": u_metragem,
                "data_venda": u_dt_venda,
                "valor_unidade": u_tvenda,
                "fracao_obra": round(fracao * 100, 4),
                "grid_temporal": linhas_temporal
            })
            
        conn_q.close()
        conn_v.close()
        return {"status": "success", "dossie": dossie}


