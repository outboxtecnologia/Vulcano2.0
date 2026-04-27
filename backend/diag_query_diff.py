"""
Valida a nova query (filtro alinhado ao SELECT de referencia da tela de Custos)
e compara com a query antiga para confirmar a diferença de valores.
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
cur  = conn.cursor()
EMPRESA = 959
CC      = 35
ANO, MES = 2025, 3
data_ini = f"{ANO}-{str(MES).zfill(2)}-01"
data_fim = f"{ANO}-{str(MES+1).zfill(2)}-01"

print("=" * 65)
print("QUERY ANTIGA  (C.DATALCTOCTB + filtro ZZ + histctb=370&nat=-1)")
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
""", (data_ini, data_fim, EMPRESA, CC, data_fim))
r = cur.fetchone()
old_ant = float(r[0] or 0)
old_vig = float(r[1] or 0)
print(f"  custo_anterior : R$ {old_ant:>18,.2f}")
print(f"  custo_vigente  : R$ {old_vig:>18,.2f}")
print(f"  mov_mes        : R$ {old_vig - old_ant:>18,.2f}")

print()
print("=" * 65)
print("QUERY NOVA   (G.DATALCTOCTB + filtro 31/12 alinhado ao SELECT ref.)")
print("=" * 65)
cur.execute("""
    SELECT
        SUM(CASE WHEN G.DATALCTOCTB < CAST(? AS DATE)
                 THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_anterior,
        SUM(CASE WHEN G.DATALCTOCTB < CAST(? AS DATE)
                 THEN G.VALORLCTOGER * G.NATURLCTOCTB ELSE 0 END) AS custo_vigente
    FROM LCTOGER G
    JOIN LCTOCTB C ON C.CODIGOEMPRESA = G.CODIGOEMPRESA AND C.CHAVELCTOCTB = G.CHAVELCTOCTB
    WHERE G.CODIGOEMPRESA = ? AND G.CODIGOCENTROCUSTO = ?
      AND G.DATALCTOCTB < CAST(? AS DATE)
      AND NOT (C.CODIGOHISTCTB = 370
           AND (G.DATALCTOCTB = CAST(EXTRACT(YEAR FROM G.DATALCTOCTB)||'-12-31' AS DATE)
                OR G.NATURLCTOCTB = -1))
""", (data_ini, data_fim, EMPRESA, CC, data_fim))
r = cur.fetchone()
new_ant = float(r[0] or 0)
new_vig = float(r[1] or 0)
print(f"  custo_anterior : R$ {new_ant:>18,.2f}")
print(f"  custo_vigente  : R$ {new_vig:>18,.2f}")
print(f"  mov_mes        : R$ {new_vig - new_ant:>18,.2f}")

print()
print("=" * 65)
print("DIFERENCA (nova - antiga)")
print("=" * 65)
print(f"  custo_anterior delta: R$ {new_ant - old_ant:>+18,.2f}")
print(f"  custo_vigente  delta: R$ {new_vig - old_vig:>+18,.2f}")

if abs(new_ant - old_ant) > 0.01 or abs(new_vig - old_vig) > 0.01:
    print("  >> VALORES DIFERENTES — filtro estava excluindo lancamentos de obra!")
else:
    print("  >> Valores identicos — problema pode ser em outro lugar")

conn.close()
