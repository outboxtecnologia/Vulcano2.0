import re
with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

target_block = '''    clusters_map = defaultdict(lambda: {"q": [], "v": []})
    for q in q_items: clusters_map[q["_cluster"]]["q"].append(q)
    for v in v_items: clusters_map[v["_cluster"]]["v"].append(v)'''

new_block = '''
    clusters_map = defaultdict(lambda: {"q": [], "v": []})
    
    if getattr(data, 'use_pgvector', False):
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
'''

if target_block in text:
    text = text.replace(target_block, new_block.strip("\n"), 1)
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("PATCH SUCESSO: main.py alterado!")
else:
    print("FALHA: Bloco target não encontrado!")
