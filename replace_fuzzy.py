import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'# 4\. Fallback Clássico 1:1 Fuzzy.*?raw_fuzzy\.sort\(key=lambda x: x\["score"\], reverse=True\)'
match = re.search(pattern, text, re.DOTALL)

new_code = '''# 4. Fallback Clássico 1:1 Fuzzy
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
            
            # Pruning dinâmico pesado para evitar O(TxT) de SequenceMatcher super lento:
            # Se for contábil Cross-Account, o valor DEVE SER muito semelhante (sv > 0.85) para valer a pena testar.
            # Se for na mesma conta, toleramos diferença maior (sv > 0.60)
            limiar_corte = 0.60 if q["conta"] == v["conta"] else 0.85
            if sv < limiar_corte: 
                continue
                
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

    raw_fuzzy.sort(key=lambda x: x["score"], reverse=True)'''

if match:
    text = text[:match.start()] + new_code + text[match.end():]
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replace OK")
else:
    print("Failed match")
