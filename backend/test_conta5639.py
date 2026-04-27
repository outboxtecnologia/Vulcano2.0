import sys
sys.path.insert(0, '.')
from main import get_conn

conn_q = get_conn("questor")
cur = conn_q.cursor()

# 1. Nome e classificação da conta
cur.execute("SELECT CONTACTB, DESCRCONTA, CLASSIFCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = 959 AND CONTACTB = 5639")
row = cur.fetchone()
if row:
    print(f"Conta: {row[0]}, Nome: {row[1]}, Classif: {row[2]}")

# 2. Todos os lançamentos da conta em 2025 (sem filtro de ZZ)
cur.execute("""
    SELECT C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, C.VALORLCTOCTB,
           CAST(C.COMPLHIST AS BLOB SUB_TYPE 0), C.CODIGOORIGLCTOCTB, H.DESCRHISTCTB
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = 959
      AND (C.CONTACTBDEB = 5639 OR C.CONTACTBCRED = 5639)
      AND C.DATALCTOCTB >= CAST('2025-01-01' AS DATE)
      AND C.DATALCTOCTB < CAST('2025-05-01' AS DATE)
    ORDER BY C.DATALCTOCTB
""")
rows = cur.fetchall()
print(f"\nTotal lancamentos jan-abr 2025: {len(rows)}")
for r in rows[:20]:
    dt, cdeb, ccred, val, hist_raw, orig, descr = r
    nat = "D" if cdeb == 5639 else "C"
    hist = hist_raw.decode('cp1252', 'ignore') if isinstance(hist_raw, (bytes, bytearray)) else str(hist_raw or "")
    print(f"  {dt} [{nat}] R${float(val or 0):,.2f} | orig={orig} | hist={descr} {hist[:60]}")

# 3. Verifica se há lançamentos a CRÉDITO (que deveriam existir)
debitos = sum(1 for r in rows if r[1] == 5639)
creditos = sum(1 for r in rows if r[2] == 5639)
print(f"\nDebitos: {debitos}, Creditos: {creditos}")
conn_q.close()
