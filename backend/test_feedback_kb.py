import sqlite3, os, json

db = os.path.join(os.path.dirname(__file__), 'poc_database.sqlite')
conn = sqlite3.connect(db)

rows = conn.execute("""
    SELECT id, created_at, veredicto, obs, score_algoritmo,
           q_conta, q_historico, q_valor,
           v_conta, v_historico, v_valor,
           q_tokens, v_tokens
    FROM cross_match_feedback
    ORDER BY created_at DESC
""").fetchall()

print(f"Total de feedbacks salvos: {len(rows)}\n")
for r in rows:
    toks_q = json.loads(r[11] or '[]')
    toks_v = json.loads(r[12] or '[]')
    print(f"[{r[0]}] {r[1]} | {r[2]:10s} | score={r[4]:.2f}")
    print(f"  Q c/{r[5]}: {str(r[6])[:60]} -> R${r[7]:,.2f}")
    print(f"  V c/{r[8]}: {str(r[9])[:60]} -> R${r[10]:,.2f}")
    print(f"  OBS: {r[3] or '(sem obs)'}")
    print(f"  tokens Q: {toks_q[:8]}")
    print(f"  tokens V: {toks_v[:8]}")
    print()

# Stats
stats = conn.execute(
    "SELECT veredicto, COUNT(*), AVG(score_algoritmo) FROM cross_match_feedback GROUP BY veredicto"
).fetchall()
print("=== STATS ===")
for s in stats:
    print(f"  {s[0]}: {s[1]} registros | score médio original do algoritmo: {s[2]:.2f}")

conn.close()
