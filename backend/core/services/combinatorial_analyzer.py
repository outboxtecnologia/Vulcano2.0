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
