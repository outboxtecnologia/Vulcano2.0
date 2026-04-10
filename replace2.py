import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('@app.post("/api/auditoria/concilia-orfaos")')
end_idx = text.find('@app.get("/api/questor/saldo-contas")')

new_code = '''@app.post("/api/auditoria/concilia-orfaos")
async def api_concilia_orfaos(data: ConciliaOrfaosInput):
    """
    Conciliação Híbrida:
    1. Clustering baseado em texto (Unidades, Vagas, Docs).
    2. Combinações Numéricas (Subset Sum) isoladas por cluster (N:M e 1:N).
    3. Fallback para similaridade Fuzzy 1:1.
    """
    import re
    import math
    from itertools import combinations
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
        d = q.dict()
        d["_id"] = f"Q_{i}"
        d["_cluster"] = _extrair_clusters(d.get("historico", "") + " " + (d.get("logica", "") or ""))
        d["_usado"] = False
        q_items.append(d)

    v_items = []
    for i, v in enumerate(data.orfaos_vulcano):
        d = v.dict()
        d["_id"] = f"V_{i}"
        d["_cluster"] = _extrair_clusters(d.get("historico", "") + " " + (d.get("logica", "") or ""))
        d["_usado"] = False
        v_items.append(d)

    clusters_map = defaultdict(lambda: {"q": [], "v": []})
    for q in q_items: clusters_map[q["_cluster"]]["q"].append(q)
    for v in v_items: clusters_map[v["_cluster"]]["v"].append(v)

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

    # 1. Matching por Cluster Fechado (Soma Global do Cluster N:M)
    for c_id, cv in clusters_map.items():
        if c_id == "OUTROS": continue
        qs_livres = [q for q in cv["q"] if not q["_usado"]]
        vs_livres = [v for v in cv["v"] if not v["_usado"]]
        if not qs_livres or not vs_livres: continue

        sum_q = sum(q["valor"] for q in qs_livres)
        sum_v = sum(v["valor"] for v in vs_livres)

        if math.isclose(sum_q, sum_v, abs_tol=0.03):
            _adicionar_match(qs_livres, vs_livres, "CLUSTER_TEXTO", 
                f"Cluster perfeito ({c_id}): Todos os lançamentos do grupo somam {sum_q:,.2f}")

    # 2. Matching Combinatório 1:N (dentro do Cluster OUTROS ou sobras de Clusters)
    # Testa subconjuntos de V que somam 1 Q
    qs_restantes = sorted([q for q in q_items if not q["_usado"]], key=lambda x: x["valor"], reverse=True)
    vs_restantes = [v for v in v_items if not v["_usado"]]
    
    for q in qs_restantes:
        if q["_usado"]: continue
        encontrou = False
        v_livres = [v for v in vs_restantes if not v["_usado"]]
        limit_r = min(6, len(v_livres) + 1)
        for r in range(1, limit_r):
            for comb in combinations(v_livres, r):
                if math.isclose(sum(v["valor"] for v in comb), q["valor"], abs_tol=0.02):
                    c_nomes = " + ".join(str(v["conta"]) for v in comb)
                    _adicionar_match([q], list(comb), "SUBSET_SUM", 
                        f"Soma exata (1:N): Lançamento Questor eq. à soma de Vulcano contas [{c_nomes}]")
                    encontrou = True
                    break
            if encontrou: break

    # 3. Matching Combinatório N:1 (Inverso)
    vs_restantes2 = sorted([v for v in v_items if not v["_usado"]], key=lambda x: x["valor"], reverse=True)
    for v in vs_restantes2:
        if v["_usado"]: continue
        encontrou = False
        q_livres = [q for q in q_items if not q["_usado"]]
        limit_rq = min(6, len(q_livres) + 1)
        for r in range(1, limit_rq):
            for comb in combinations(q_livres, r):
                if math.isclose(sum(q["valor"] for q in comb), v["valor"], abs_tol=0.02):
                    _adicionar_match(list(comb), [v], "SUBSET_SUM_INV", 
                        f"Soma exata (N:1): Múltiplos lançamentos Questor equivalem a este do Vulcano")
                    encontrou = True
                    break
            if encontrou: break

    # 4. Fallback Clássico 1:1 Fuzzy (para os que sobraram isolados)
    qs_finais = [q for q in q_items if not q["_usado"]]
    vs_finais = [v for v in v_items if not v["_usado"]]
    
    raw_fuzzy = []
    
    def sf_valor(a, b):
        if a < 0.01 or b < 0.01: return 0.0
        d = abs(a - b)
        if d < 0.02: return 1.0
        return max(0.0, 1.0 - d / max(a, b))

    for q in qs_finais:
        qh = (q.get("historico", "") or "").upper()
        for v in vs_finais:
            sv = sf_valor(q["valor"], v["valor"])
            if sv < 0.25: continue
            vh = (v.get("historico", "") or "").upper()
            sh = SequenceMatcher(None, qh, vh).ratio() if qh and vh else 0.5
            sc = 1.0 if q["conta"] == v["conta"] else 0.6
            
            score = (sv * 0.50) + (sh * 0.25) + (sc * 0.25)
            if q["natureza"] != v["natureza"]: score *= 0.75
            
            if score >= data.threshold:
                tipo = "CROSS_ACCOUNT" if q["conta"] != v["conta"] else "MESMA_CONTA"
                raw_fuzzy.append({
                    "questor": q, "vulcano": v, "score": score,
                    "questor_detalhe": [q], "vulcano_detalhe": [v],
                    "score_valor": sv, "score_hist": sh, "score_data": 0.5, "score_conta": sc,
                    "nat_match": q["natureza"] == v["natureza"],
                    "tipo": tipo,
                    "sugestao": f"Fuzzy Residual: similaridade {score*100:.0f}% detectada."
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

'''

text = text[:start_idx] + new_code + text[end_idx:]
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)

