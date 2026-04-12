from pydantic import BaseModel
from typing import List, Dict, Any
import re
import math
from itertools import combinations
from collections import defaultdict

class OrphansReconciliationService:
    class OrfaoItem(BaseModel):
        conta: int = 0
        data: str = ""
        historico: str = ""
        natureza: str = ""   # 'D' | 'C'
        valor: float = 0.0
        chave: str = ""
        logica: str = ""

    class ConciliaOrfaosInput(BaseModel):
        empresa_id: int
        orfaos_questor: list[OrfaoItem]
        orfaos_vulcano: list[OrfaoItem]
        threshold: float = 0.38
        use_pgvector: bool = False

    @staticmethod
    async def api_concilia_orfaos(data: "OrphansReconciliationService.ConciliaOrfaosInput"):
        from main import get_conn

        """
        Conciliação Híbrida:
        1. Clustering baseado em texto (Unidades, Vagas, Docs).
        2. Combinações Numéricas (Subset Sum) isoladas por cluster (N:M e 1:N).
        3. Fallback para similaridade Fuzzy 1:1.
        """
        import re
        import math
        from itertools import combinations, product
        from difflib import SequenceMatcher
        from collections import defaultdict

        def _extrair_clusters(texto: str) -> str:
            t = (texto or "").upper()
            # Busca menção explícita a unidade, bloco, apto, vaga
            m = re.search(r'(UNIDADE|UNID|APTO|APT|SALA|LOJA|CASA|BOX|VG|VAGA|TORRE)\s*([A-Z0-9\-]+)', t)
            if m:
                return f"{m.group(1).strip()}_{m.group(2).strip()}"
            
            # Fallback para palavras fortes (ex: PIS, COFINS, RET, IRPJ) - agrupa guias da mesma competência
            impostos = []
            for imp in ["IRPJ", "CSLL", "PIS", "COFINS", "RET"]:
                if imp in t: impostos.append(imp)
            if impostos:
                return "_".join(sorted(impostos))
                
            return "OUTROS"

        # Preparar itens com IDs únicos
        q_items = []
        for i, q in enumerate(data.orfaos_questor):
            if str(q.conta) == "5": continue
            d = q.dict()
            d["_id"] = f"Q_{i}"
            d["_cluster"] = _extrair_clusters(d.get("historico", "") + " " + (d.get("logica", "") or ""))
            d["_usado"] = False
            q_items.append(d)

        v_items = []
        for i, v in enumerate(data.orfaos_vulcano):
            if str(v.conta) == "5": continue
            d = v.dict()
            d["_id"] = f"V_{i}"
            d["_cluster"] = _extrair_clusters(d.get("historico", "") + " " + (d.get("logica", "") or ""))
            d["_usado"] = False
            v_items.append(d)

        clusters_map = defaultdict(lambda: {"q": [], "v": []})
        
        if data.use_pgvector is True:
            try:
                from vector_engine import SessionLocal, generate_embeddings_batch
                from sqlalchemy import text
                import json
                
                # 1. Gera embeddings dos Orfaos Virtuais na hora para caçar
                textos_v = [(str(v.get("historico", "")) + " " + str(v.get("logica", ""))).upper().strip() for v in v_items]
                matrizes_v = await generate_embeddings_batch(textos_v)
                
                db = SessionLocal()
                q_by_key = {str(q.get("chave", "")): q for q in q_items if str(q.get("chave", ""))}
                
                # Adiciona todos os Questor órfãos em clusters únicos pela chave
                for q in q_items:
                    chave = str(q.get("chave", ""))
                    cid = f"vec_Q_{chave}" if chave else f"vec_FAIL_Q_{q['_id']}"
                    clusters_map[cid]["q"].append(q)
                    
                # 2. Cruza com PGVector
                for k_v, v in enumerate(v_items):
                    if k_v >= len(matrizes_v): 
                        clusters_map[f"vec_fail_{v['_id']}"]["v"].append(v)
                        continue
                        
                    vec_str = json.dumps(matrizes_v[k_v])
                    rs = db.execute(text(f"""
                       SELECT id, embedding <-> '{vec_str}' as dist 
                       FROM erp_embeddings 
                       WHERE fonte='QUESTOR' AND empresa_id=:emp
                       ORDER BY dist ASC LIMIT 10
                    """), {"emp": data.empresa_id}).fetchall()
                    
                    best_q_chave = None
                    for row in rs:
                        chv = str(row[0]).replace("Q_", "")
                        if chv in q_by_key: # O mais próximo que é ÓRFÃO na tela
                            best_q_chave = chv
                            break
                            
                    if best_q_chave:
                        clusters_map[f"vec_Q_{best_q_chave}"]["v"].append(v)
                    else:
                        clusters_map[f"vec_fail_{v['_id']}"]["v"].append(v)
                        
                db.close()
            except Exception as e:
                print(f"Erro no módulo PGVector: {e}")
                # Fallback seguro
                clusters_map = defaultdict(lambda: {"q": [], "v": []})
                for q in q_items: clusters_map[q["_cluster"]]["q"].append(q)
                for v in v_items: clusters_map[v["_cluster"]]["v"].append(v)
        else:
            for q in q_items: clusters_map[q["_cluster"]]["q"].append(q)
            for v in v_items: clusters_map[v["_cluster"]]["v"].append(v)
        
        # [CUB ANALYSIS] Mapa analítico para auditar se pequenas diferenças são CUB
        cub_map = {}
        try:
            conn_v = get_conn("vulcano")
            cur_v = conn_v.cursor()
            cur_v.execute("""
                SELECT V.DESCUNIDIMOB, EXTRACT(YEAR FROM R.DATA), EXTRACT(MONTH FROM R.DATA), SUM(R.VALORVARIACAO)
                FROM RECEBER R
                JOIN VENDA V ON V.ID = R.IDVENDA
                JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
                JOIN UNIDADE U ON U.ID = VU.IDUNIDADE
                JOIN BLOCO B ON B.ID = U.IDBLOCO
                JOIN EMPREENDIMENTO E ON E.ID = B.IDEMPREENDIMENTO
                WHERE E.CODIGOEMPRESA = ? AND R.TOTALPAGO > 0
                GROUP BY 1, 2, 3
            """, (data.empresa_id,))
            for cv_r in cur_v.fetchall():
                uni = str(cv_r[0] or "").strip().upper()
                if uni:
                    key = f"{uni}_{int(cv_r[1])}-{str(int(cv_r[2])).zfill(2)}"
                    cub_map[key] = float(cv_r[3] or 0.0)
        except Exception as e:
            print(f"Erro CUB Mapping Caching: {e}")

        def _verificar_anomalia_cub(v_list, diff_eval):
            if diff_eval < 0.03: return None
            for v in v_list:
                hist = (str(v.get("historico", "")) + " " + str(v.get("logica", ""))).upper()
                if "UNID " in hist:
                    uni_nome = hist.split("UNID ")[-1].strip()
                    comp = str(v.get("competencia", "")) if v.get("competencia") else str(v.get("data", ""))[:7]
                    key = f"{uni_nome}_{comp}"
                    cub_esperado = cub_map.get(key, 0.0)
                    if cub_esperado > 0 and math.isclose(diff_eval, cub_esperado, rel_tol=0.03, abs_tol=1.0):
                        return f"Aprovado por CUB: Diferença exata de CUB mapeado R$ {diff_eval:,.2f}"
            return None

        matches_finais = []
        
        def _adicionar_match(q_list, v_list, tipo_str, sugestao_str):
            nonlocal matches_finais
            s_vq = sum(q["valor"] for q in q_list)
            s_vv = sum(v["valor"] for v in v_list)
            
            q_contas = list(set([int(q["conta"]) for q in q_list]))
            v_contas = list(set([int(v["conta"]) for v in v_list]))
            conta_q = q_contas[0] if len(q_contas)==1 else 9999
            conta_v = v_contas[0] if len(v_contas)==1 else 9999
            
            nat_ok = all(q["natureza"] == v["natureza"] for q in q_list for v in v_list)

            matches_finais.append({
                "questor": q_list[0] if len(q_list)==1 else {"conta": conta_q, "historico": f"{len(q_list)} Lanç. Aglutinados", "valor": s_vq, "natureza": q_list[0]["natureza"], "data": q_list[0]["data"]},
                "vulcano": v_list[0] if len(v_list)==1 else {"conta": conta_v, "historico": f"{len(v_list)} Lanç. Aglutinados", "valor": s_vv, "natureza": v_list[0]["natureza"], "data": v_list[0]["data"]},
                "questor_detalhe": q_list,
                "vulcano_detalhe": v_list,
                "score": 1.0,
                "score_valor": 1.0,
                "score_hist": 1.0 if tipo_str == "CLUSTER_TEXTO" else 0.5,
                "score_data": 0.5,
                "score_conta": 1.0 if conta_q == conta_v else 0.6,
                "nat_match": nat_ok,
                "tipo": "CROSS_ACCOUNT" if conta_q != conta_v else "MESMA_CONTA",
                "sugestao": sugestao_str
            })
            for q in q_list: q["_usado"] = True
            for v in v_list: v["_usado"] = True

        # 1. Matching por Repositório/Cluster (Splink Equivalente)
        for c_id, cv in clusters_map.items():
            if c_id == "OUTROS": continue
            qs_livres = [q for q in cv["q"] if not q["_usado"]]
            vs_livres = [v for v in cv["v"] if not v["_usado"]]
            if not qs_livres or not vs_livres: continue

            sum_q = sum(q["valor"] for q in qs_livres)
            sum_v = sum(v["valor"] for v in vs_livres)

            if math.isclose(sum_q, sum_v, rel_tol=0.05, abs_tol=5.0):
                _adicionar_match(qs_livres, vs_livres, "CLUSTER_TEXTO", 
                    f"Cluster perfeito ({c_id}): Todos os lançamentos engajados somam {sum_q:,.2f}")
                continue

            from core.services.combinatorial_analyzer import CombinatorialAnalyzer
            # 1.1 e 1.2 Combinatorias N:M isoladas em Motor dedicado
            CombinatorialAnalyzer.run_1_to_n(c_id, qs_livres, cv['v'], _adicionar_match, _verificar_anomalia_cub)
            CombinatorialAnalyzer.run_n_to_1(c_id, vs_livres, cv['q'], _adicionar_match, _verificar_anomalia_cub)

        # 2. Rescaldo Fuzzy Clássico 1:1 apenas para o que sobrou (inclui OUTROS)
        qs_finais = [q for q in q_items if not q["_usado"]]
        vs_finais = [v for v in v_items if not v["_usado"]]
        
        raw_fuzzy = []
        
        def sf_valor(a, b):
            if a < 0.01 or b < 0.01: return 0.0
            d = abs(a - b)
            if d < 10.0: return 1.0
            return max(0.0, 1.0 - d / max(a, b))

        # Otimização O(N) agilizando a restrição primária de conta: 
        # Dicionário de Vs por conta
        vs_por_conta = defaultdict(list)
        for v in vs_finais: vs_por_conta[v["conta"]].append(v)
        
        for q in qs_finais:
            if q["_usado"]: continue
            qh = (q.get("historico", "") or "").upper()
            
            # Filtra apenas a mesma conta (para não travar CPU em busca Cross-Account cega)
            # Qualquer Cross-Account válida já foi resolvida pelos Repositórios no Passo 1!
            vs_avaliar = vs_por_conta[q["conta"]]
            
            for v in vs_avaliar:
                if v["_usado"]: continue
                sv = sf_valor(q["valor"], v["valor"])
                
                # Como só avalia Mesma_Conta, limiar é 0.60
                if sv < 0.60: 
                    continue
                    
                vh = (v.get("historico", "") or "").upper()
                sh = SequenceMatcher(None, qh, vh).ratio() if qh and vh else 0.5
                sc = 1.0
                
                score = (sv * 0.50) + (sh * 0.25) + (sc * 0.25)
                if q["natureza"] != v["natureza"]: score *= 0.75
                
                if score >= data.threshold:
                    raw_fuzzy.append({
                        "questor": q, "vulcano": v, "score": score,
                        "questor_detalhe": [q], "vulcano_detalhe": [v],
                        "score_valor": sv, "score_hist": sh, "score_data": 0.5, "score_conta": sc,
                        "nat_match": q["natureza"] == v["natureza"],
                        "tipo": "MESMA_CONTA",
                        "sugestao": f"Fuzzy Residual 1:1: similaridade {score*100:.0f}% detectada."
                    })

        raw_fuzzy.sort(key=lambda x: x["score"], reverse=True)
        for m in raw_fuzzy:
            if not m["questor"]["_usado"] and not m["vulcano"]["_usado"]:
                m["questor"]["_usado"] = True
                m["vulcano"]["_usado"] = True
                matches_finais.append(m)

        # Limpar tags internas
        for m in matches_finais:
            if "questor_detalhe" in m:
                for q in m["questor_detalhe"]: q.pop("_id", None); q.pop("_cluster", None); q.pop("_usado", None)
                for v in m["vulcano_detalhe"]: v.pop("_id", None); v.pop("_cluster", None); v.pop("_usado", None)
            else:
                m["questor"].pop("_id", None); m["questor"].pop("_cluster", None); m["questor"].pop("_usado", None)
                m["vulcano"].pop("_id", None); m["vulcano"].pop("_cluster", None); m["vulcano"].pop("_usado", None)

        return {
            "total_orfaos_questor": len(data.orfaos_questor),
            "total_orfaos_vulcano": len(data.orfaos_vulcano),
            "total_matches": len(matches_finais),
            "matches": matches_finais,
        }
