"""
Testa exatamente a query da linha 407-427 do graph_logic_builder para Stuttgart
e verifica o que a conta 5639 recebe como saldo no LCTOGER global (contas_fisicas).
"""
import firebirdsql, os
from dotenv import load_dotenv
load_dotenv("backend/.env", override=True)

DB_Q = os.environ.get("DB_PATH_QUESTOR", r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB")
HOST = os.environ.get("FIREBIRD_HOST", "localhost")
PORT = int(os.environ.get("FIREBIRD_PORT", "3050"))
USR  = os.environ.get("FIREBIRD_USER", "SYSDBA")
PWD  = os.environ.get("FIREBIRD_PASSWORD", "masterkey")

conn = firebirdsql.connect(host=HOST, port=PORT, database=DB_Q,
                           user=USR, password=PWD, charset="WIN1252")
cur = conn.cursor()
EMPRESA = 959
CC_STU  = 35
ANO, MES = 2025, 3
data_ini = f"{ANO}-{str(MES).zfill(2)}-01"
data_fim = f"{ANO}-{str(MES+1).zfill(2)}-01"

print("=" * 65)
print(f"QUERY CUSTO LCTOGER/CC={CC_STU} para {ANO}-{str(MES).zfill(2)}")
print("(exatamente como graph_logic_builder.py faz)")
print("=" * 65)
cur.execute("""
    SELECT
        SUM(CASE WHEN C.DATALCTOCTB < CAST(? AS DATE)
                 THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_anterior,
        SUM(CASE WHEN C.DATALCTOCTB < CAST(? AS DATE)
                 THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_vigente
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
      AND C.DATALCTOCTB < CAST(? AS DATE)
      AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
      AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
""", (data_ini, data_fim, EMPRESA, CC_STU, data_fim))
r = cur.fetchone()
ant = float(r[0] or 0)
vig = float(r[1] or 0)
mov = vig - ant
print(f"  custo_anterior (antes de {data_ini}): R$ {ant:>18,.2f}")
print(f"  custo_vigente  (antes de {data_fim}): R$ {vig:>18,.2f}")
print(f"  mov_gasto (delta do mes):              R$ {mov:>18,.2f}")
print(f"  inject? abs(mov)>0.01={abs(mov)>0.01} OR abs(ant)>0.01={abs(ant)>0.01}")

print()
print("=" * 65)
print("NATURAL: VALORLCTOGER * NATURLCTOCTB no CC=35 (detalhe por natureza)")
print("=" * 65)
cur.execute("""
    SELECT G.NATURLCTOCTB, COUNT(*), SUM(G.VALORLCTOGER), SUM(G.VALORLCTOGER * G.NATURLCTOCTB)
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
      AND C.DATALCTOCTB < CAST(? AS DATE)
      AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
      AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
    GROUP BY G.NATURLCTOCTB
""", (EMPRESA, CC_STU, data_fim))
for r in cur.fetchall():
    print(f"  NATURLCTOCTB={r[0]:2d} | count={r[1]:5d} | bruto=R${float(r[2] or 0):>14,.2f} | liquido=R${float(r[3] or 0):>14,.2f}")

print()
print("=" * 65)
print("LCTOGER global (empresa-wide) - a conta 5639 aparece como contas_fisicas?")
print("(query da fase saldo_anterior_por_conta do pipeline)")
print("=" * 65)
cur.execute("""
    SELECT
        C.CONTACTBDEB, C.CONTACTBCRED, G.NATURLCTOCTB,
        SUM(G.VALORLCTOGER) as TOTAL
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = ? AND C.DATALCTOCTB < CAST(? AS DATE)
    AND (C.CODIGOORIGLCTOCTB IS NULL OR C.CODIGOORIGLCTOCTB <> 'ZZ')
    AND NOT (C.CODIGOHISTCTB = 370 AND G.NATURLCTOCTB = -1)
    AND (C.CONTACTBDEB = 5639 OR C.CONTACTBCRED = 5639)
    GROUP BY 1, 2, 3
""", (EMPRESA, data_ini))
rows = cur.fetchall()
print(f"  Lancamentos com conta 5639 no LCTOGER global: {len(rows)}")
saldo = 0.0
for r in rows:
    cdeb, ccred, nat, val = r
    v = float(val or 0)
    if nat == 1 and cdeb == 5639:
        saldo += v
        print(f"  D: {cdeb} / C: {ccred} | nat={nat} | val={v:,.2f} -> DEBITA 5639 +{v:,.2f}")
    elif nat == -1 and ccred == 5639:
        saldo -= v
        print(f"  D: {cdeb} / C: {ccred} | nat={nat} | val={v:,.2f} -> CREDITA 5639 -{v:,.2f}")
    else:
        print(f"  D: {cdeb} / C: {ccred} | nat={nat} | val={v:,.2f} -> NAO afeta saldo 5639 diretamente")
print(f"  SALDO ANTERIOR conta 5639 via LCTOGER global: R$ {saldo:,.2f}")

conn.close()
