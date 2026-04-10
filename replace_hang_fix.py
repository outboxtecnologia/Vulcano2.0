import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to replace the section from "# 2. Matching Combinatório 1:N (dentro do Cluster OUTROS ou sobras de Clusters)"
# up to "# 4. Fallback Clássico 1:1 Fuzzy"

pattern = r'# 2\. Matching Combinatório 1:N.*?# 4\. Fallback Clássico 1:1 Fuzzy'
match = re.search(pattern, text, re.DOTALL)

new_code = '''# 2. Matching Combinatório 1:N (dentro da mesma conta e natureza)
    qs_restantes = sorted([q for q in q_items if not q["_usado"]], key=lambda x: x["valor"], reverse=True)
    vs_restantes = [v for v in v_items if not v["_usado"]]
    
    for q in qs_restantes:
        if q["_usado"]: continue
        encontrou = False
        # Para evitar explosão O(N^5) e falsos positivos, restringe V livres a mesma conta
        v_livres = [v for v in vs_restantes if not v["_usado"] and v["conta"] == q["conta"] and v["natureza"] == q["natureza"]]
        # Filtra valores impossíveis (maiores que o Q target)
        v_livres = [v for v in v_livres if abs(v["valor"]) <= abs(q["valor"]) + 0.05]
        
        limit_r = min(6, len(v_livres) + 1)
        if len(v_livres) > 30: limit_r = min(limit_r, 4)
        if len(v_livres) > 50: limit_r = min(limit_r, 3)
        
        for r in range(1, limit_r):
            for comb in combinations(v_livres, r):
                if math.isclose(sum(v["valor"] for v in comb), q["valor"], abs_tol=0.02):
                    c_nomes = " + ".join(str(v["conta"]) for v in comb)
                    _adicionar_match([q], list(comb), "SUBSET_SUM", 
                        f"Soma exata intra-conta (1:N): Lançamento Questor eq. à soma de Vulcano [{c_nomes}]")
                    encontrou = True
                    break
            if encontrou: break

    # 3. Matching Combinatório N:1 (Inverso)
    vs_restantes2 = sorted([v for v in v_items if not v["_usado"]], key=lambda x: x["valor"], reverse=True)
    for v in vs_restantes2:
        if v["_usado"]: continue
        encontrou = False
        q_livres = [q for q in q_items if not q["_usado"] and q["conta"] == v["conta"] and q["natureza"] == v["natureza"]]
        q_livres = [q for q in q_livres if abs(q["valor"]) <= abs(v["valor"]) + 0.05]
        
        limit_rq = min(6, len(q_livres) + 1)
        if len(q_livres) > 30: limit_rq = min(limit_rq, 4)
        if len(q_livres) > 50: limit_rq = min(limit_rq, 3)

        for r in range(1, limit_rq):
            for comb in combinations(q_livres, r):
                if math.isclose(sum(q["valor"] for q in comb), v["valor"], abs_tol=0.02):
                    _adicionar_match(list(comb), [v], "SUBSET_SUM_INV", 
                        f"Soma exata intra-conta (N:1): Múltiplos lançamentos Questor equivalem a este do Vulcano")
                    encontrou = True
                    break
            if encontrou: break

    # 4. Fallback Clássico 1:1 Fuzzy'''
    
if match:
    text = text[:match.start()] + new_code + text[match.end():]
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replace OK")
else:
    print("Match failed")

