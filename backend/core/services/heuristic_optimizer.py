from __future__ import annotations

from pydantic import BaseModel
from typing import List, Dict, Any
import re
import math
import time
from itertools import combinations
from collections import defaultdict

# ── Cache TTL do CUB Map (5 min por empresa) ──────────────────────────────────
_CUB_CACHE: dict = {}   # { empresa_id: (timestamp, cub_map_dict) }
_CUB_TTL = 300          # segundos

# Contas que pertencem ao mesmo grupo de reconciliação apartamento.
# Lançamentos destas contas SÓ fazem cross-match entre elas mesmas.
# O indexador primário é o número do APTO encontrado no histórico.
CONTAS_GRUPO_APTO: set = {5653, 5665, 5666}

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
        """Wrapper async: descarrega todo o processamento CPU-bound para um thread
        via asyncio.to_thread para não bloquear o event loop do FastAPI."""
        import asyncio
        return await asyncio.to_thread(
            OrphansReconciliationService._concilia_orfaos_sync, data
        )

    @staticmethod
    def _concilia_orfaos_sync(data: "OrphansReconciliationService.ConciliaOrfaosInput"):

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

        def _extrair_apto_num(texto: str) -> str | None:
            """Extrai número do APTO como indexador primário canônico.
            Quando há dois APTO no histórico (ex: 'APTO 277 ... - APTO 302'),
            o PRIMEIRO é o número do contrato e o SEGUNDO é o número real
            do apartamento. Sempre usa o Último match como indexador.
            Retorna 'APTO_<numero>' normalizado ou None se não encontrar."""
            t = (texto or "").upper()
            # findall retorna todas as ocorrências; pega a última (número real do apto)
            matches = re.findall(r'\bAPT[O]?[\s\-]*(\d+)', t)
            if matches:
                return f"APTO_{matches[-1].strip()}"
            return None

        def _extrair_clusters(texto: str) -> str:
            t = (texto or "").upper()

            # --- Indexador primário: APTO + número ---
            apto = _extrair_apto_num(t)
            if apto:
                return apto

            # --- Outras unidades (UNID, SALA, LOJA, etc.) ---
            m = re.search(r'(UNIDADE|UNID|SALA|LOJA|CASA|BOX|VG|VAGA|TORRE)\s*([A-Z0-9\-]+)', t)
            if m:
                return f"{m.group(1).strip()}_{m.group(2).strip()}"

            # Fallback para palavras fortes (ex: PIS, COFINS, RET, IRPJ)
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
            texto_completo = d.get("historico", "") + " " + (d.get("logica", "") or "")
            d["_cluster"] = _extrair_clusters(texto_completo)
            d["_apto"] = _extrair_apto_num(texto_completo)
            d["_no_grupo_apto"] = int(d.get("conta", 0)) in CONTAS_GRUPO_APTO
            d["_usado"] = False
            q_items.append(d)

        v_items = []
        for i, v in enumerate(data.orfaos_vulcano):
            if str(v.conta) == "5": continue
            d = v.dict()
            d["_id"] = f"V_{i}"
            texto_completo = d.get("historico", "") + " " + (d.get("logica", "") or "")
            d["_cluster"] = _extrair_clusters(texto_completo)
            d["_apto"] = _extrair_apto_num(texto_completo)
            d["_no_grupo_apto"] = int(d.get("conta", 0)) in CONTAS_GRUPO_APTO
            d["_usado"] = False
            v_items.append(d)

        clusters_map = defaultdict(lambda: {"q": [], "v": []})
        
        if data.use_pgvector is True:
            try:
                from vector_engine import SessionLocal, generate_embeddings_batch
                from sqlalchemy import text
                import json
                
                # 1. Gera embeddings dos Orfaos Virtuais na hora para caçar
                # NOTA: _concilia_orfaos_sync roda em thread (via asyncio.to_thread),
                # por isso não pode usar await diretamente. asyncio.run() cria um
                # event loop local só para essa coroutine.
                textos_v = [(str(v.get("historico", "")) + " " + str(v.get("logica", ""))).upper().strip() for v in v_items]
                import asyncio as _asyncio
                matrizes_v = _asyncio.run(generate_embeddings_batch(textos_v))
                
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
        
        # [CUB ANALYSIS] Cache TTL de 5 min por empresa — evita o JOIN pesado a cada chamada
        cub_map = {}
        try:
            _now = time.monotonic()
            _cached = _CUB_CACHE.get(data.empresa_id)
            if _cached and (_now - _cached[0]) < _CUB_TTL:
                cub_map = _cached[1]
            else:
                conn_v = get_conn("vulcano")
                cur_v = conn_v.cursor()
                cur_v.execute("""
                    SELECT FIRST 2000
                        V.DESCUNIDIMOB, EXTRACT(YEAR FROM R.DATA), EXTRACT(MONTH FROM R.DATA),
                        SUM(R.VALORVARIACAO)
                    FROM RECEBER R
                    JOIN VENDA V ON V.ID = R.IDVENDA
                    JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
                    JOIN UNIDADE U ON U.ID = VU.IDUNIDADE
                    JOIN BLOCO B ON B.ID = U.IDBLOCO
                    JOIN EMPREENDIMENTO E ON E.ID = B.IDEMPREENDIMENTO
                    WHERE E.CODIGOEMPRESA = ? AND R.TOTALPAGO > 0 AND R.VALORVARIACAO > 0
                    GROUP BY 1, 2, 3
                """, (data.empresa_id,))
                for cv_r in cur_v.fetchall():
                    uni = str(cv_r[0] or "").strip().upper()
                    if uni:
                        key = f"{uni}_{int(cv_r[1])}-{str(int(cv_r[2])).zfill(2)}"
                        cub_map[key] = float(cv_r[3] or 0.0)
                conn_v.close()
                _CUB_CACHE[data.empresa_id] = (_now, cub_map)
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

            # ── Regra de isolamento do grupo APTO (5653/5665/5666) ──────────────
            # Lançamentos do grupo só cruzam entre si. Se o cluster APTO misturar
            # contas fora do grupo com contas do grupo, separa os dois lados.
            eh_cluster_apto = c_id.startswith("APTO_")
            if eh_cluster_apto:
                # Lado Q: apenas contas do grupo podem cruzar com V do grupo (e vice-versa)
                qs_grupo = [q for q in qs_livres if q["_no_grupo_apto"]]
                vs_grupo = [v for v in vs_livres if v["_no_grupo_apto"]]
                qs_fora  = [q for q in qs_livres if not q["_no_grupo_apto"]]
                vs_fora  = [v for v in vs_livres if not v["_no_grupo_apto"]]
                # Redistribuir: dentro do grupo cruzam entre si; fora do grupo cruzam entre si
                cluster_batches = []
                if qs_grupo and vs_grupo:
                    cluster_batches.append((c_id + "_GRP", qs_grupo, vs_grupo))
                if qs_fora and vs_fora:
                    cluster_batches.append((c_id + "_EXT", qs_fora, vs_fora))
            else:
                # Para clusters não-APTO, contas do grupo APTO ficam de fora do cross-account
                # Elas só cruzam em clusters APTO.
                qs_ok = [q for q in qs_livres if not q["_no_grupo_apto"]]
                vs_ok = [v for v in vs_livres if not v["_no_grupo_apto"]]
                cluster_batches = [(c_id, qs_ok, vs_ok)] if (qs_ok and vs_ok) else []

            from core.services.combinatorial_analyzer import CombinatorialAnalyzer
            for batch_id, q_batch, v_batch in cluster_batches:
                if not q_batch or not v_batch:
                    continue
                sum_q = sum(q["valor"] for q in q_batch)
                sum_v = sum(v["valor"] for v in v_batch)

                if math.isclose(sum_q, sum_v, rel_tol=0.05, abs_tol=5.0):
                    _adicionar_match(q_batch, v_batch, "CLUSTER_TEXTO",
                        f"Cluster perfeito ({batch_id}): Todos os lançamentos somam {sum_q:,.2f}")
                    continue

                # 1.1 e 1.2 Combinatorias N:M isoladas em Motor dedicado
                CombinatorialAnalyzer.run_1_to_n(batch_id, q_batch, v_batch, _adicionar_match, _verificar_anomalia_cub)
                CombinatorialAnalyzer.run_n_to_1(batch_id, v_batch, q_batch, _adicionar_match, _verificar_anomalia_cub)

        # 2. Rescaldo Fuzzy Clássico 1:1 apenas para o que sobrou (inclui OUTROS)
        qs_finais = [q for q in q_items if not q["_usado"]]
        vs_finais = [v for v in v_items if not v["_usado"]]

        raw_fuzzy = []

        def sf_valor(a, b):
            if a < 0.01 or b < 0.01: return 0.0
            d = abs(a - b)
            if d < 10.0: return 1.0
            return max(0.0, 1.0 - d / max(a, b))

        # Otimização O(N): dicionário de Vs por conta
        # Contas do grupo APTO (5653/5665/5666) também cruzam entre si no fuzzy residual,
        # usando o número do APTO como chave secundária de restrição.
        vs_por_conta = defaultdict(list)
        vs_por_apto_grupo = defaultdict(list)  # chave: apto_num para o grupo APTO
        for v in vs_finais:
            vs_por_conta[v["conta"]].append(v)
            if v["_no_grupo_apto"] and v["_apto"]:
                vs_por_apto_grupo[v["_apto"]].append(v)

        for q in qs_finais:
            if q["_usado"]: continue
            qh = (q.get("historico", "") or "").upper()

            # Contas do grupo APTO: fuzzy residual restrito ao grupo + mesmo APTO
            if q["_no_grupo_apto"]:
                apto_q = q["_apto"]
                if apto_q:
                    vs_avaliar = [v for v in vs_por_apto_grupo.get(apto_q, []) if not v["_usado"]]
                else:
                    # sem número APTO identificado → sem cross residual
                    continue
            else:
                # Filtra apenas a mesma conta (para não travar CPU em busca Cross-Account cega)
                # Qualquer Cross-Account válida já foi resolvida pelos Repositórios no Passo 1!
                vs_avaliar = [v for v in vs_por_conta[q["conta"]] if not v["_usado"]]
            
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
