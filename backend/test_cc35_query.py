"""
Testa a query LCTOGER para CC=35 (Stuttgart) - conta 5639
Verifica o total mensal de custos que deveria aparecer na auditoria
"""
import firebirdsql, os
from dotenv import load_dotenv
load_dotenv("backend/.env", override=True)

empresa_id = 959
cc_emp = 35  # Stuttgart
conta_5639 = 5639

conn = firebirdsql.connect(
    host=os.environ.get("FIREBIRD_HOST", "localhost"),
    port=int(os.environ.get("FIREBIRD_PORT", "3050")),
    database=os.environ.get("DB_PATH_QUESTOR", r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB"),
    user=os.environ.get("FIREBIRD_USER", "SYSDBA"),
    password=os.environ.get("FIREBIRD_PASSWORD", "masterkey"),
    charset="WIN1252"
)
cur = conn.cursor()

print("=== QUERY 1: Total mensal pelo CC=35 (como sincronizar_totalizadores faz) ===")
cur.execute("""
    SELECT extract(year from lctoger.datalctoctb),
           extract(month from lctoger.datalctoctb),
           coalesce(sum(coalesce(lctoger.valorlctoger*lctoger.naturlctoctb, 0)), 0)
    FROM lctoger
    INNER JOIN lctoctb ON lctoctb.codigoempresa = lctoger.codigoempresa 
        AND lctoctb.chavelctoctb = lctoger.chavelctoctb
    WHERE lctoger.codigoempresa = ? AND lctoger.codigocentrocusto = ?
    AND not (lctoctb.codigohistctb = 370 and lctoger.naturlctoctb = -1)
    GROUP BY 1, 2
    ORDER BY 1, 2
""", (empresa_id, cc_emp))
rows = cur.fetchall()
print(f"Total de periodos: {len(rows)}")
total_geral = 0.0
for r in rows:
    total_geral += float(r[2])
    print(f"  {int(r[0])}-{str(int(r[1])).zfill(2)}: R$ {float(r[2]):,.2f}")
print(f"TOTAL GERAL: R$ {total_geral:,.2f}")

print()
print("=== QUERY 2: A conta 5639 aparece no CC=35? (CONTACTBDEB/CRED=5639 no CC=35) ===")
cur.execute("""
    SELECT COUNT(*), SUM(G.VALORLCTOGER * G.NATURLCTOCTB)
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
      AND (C.CONTACTBDEB = ? OR C.CONTACTBCRED = ?)
""", (empresa_id, cc_emp, conta_5639, conta_5639))
r = cur.fetchone()
print(f"  Lancamentos com conta 5639 no CC=35: {r[0]} | Saldo: R$ {float(r[1] or 0):,.2f}")

print()
print("=== QUERY 3: A conta 5639 aparece no LCTOCTB SEM filtro de CC? ===")
cur.execute("""
    SELECT COUNT(*), SUM(CASE WHEN CONTACTBDEB=? THEN VALORLCTOCTB ELSE -VALORLCTOCTB END)
    FROM LCTOCTB
    WHERE CODIGOEMPRESA = ? AND (CONTACTBDEB = ? OR CONTACTBCRED = ?)
      AND (CODIGOORIGLCTOCTB IS NULL OR CODIGOORIGLCTOCTB <> 'ZZ')
""", (conta_5639, empresa_id, conta_5639, conta_5639))
r = cur.fetchone()
print(f"  Lancamentos conta 5639 no LCTOCTB total: {r[0]} | Saldo: R$ {float(r[1] or 0):,.2f}")

print()
print("=== QUERY 4: Top contas mais debitadas no CC=35 ===")
cur.execute("""
    SELECT C.CONTACTBDEB, SUM(G.VALORLCTOGER) as TOTAL
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ? AND G.NATURLCTOCTB = 1
    GROUP BY C.CONTACTBDEB
    ORDER BY TOTAL DESC
    ROWS 15
""", (empresa_id, cc_emp))
rows = cur.fetchall()
for r in rows:
    print(f"  Conta {r[0]}: R$ {float(r[1] or 0):,.2f}")

conn.close()
