import sys
sys.path.insert(0, '.')
from main import get_conn

conn_q = get_conn("questor")
cur = conn_q.cursor()

# Verifica CODIGOHISTCTB dos lançamentos de crédito (orig=VU) para conta 5639
cur.execute("""
    SELECT C.DATALCTOCTB, C.CONTACTBDEB, C.CONTACTBCRED, C.VALORLCTOCTB,
           C.CODIGOORIGLCTOCTB, C.CODIGOHISTCTB, H.DESCRHISTCTB
    FROM LCTOCTB C
    LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
    WHERE C.CODIGOEMPRESA = 959
      AND C.CONTACTBCRED = 5639
      AND C.DATALCTOCTB >= CAST('2025-01-01' AS DATE)
      AND C.DATALCTOCTB < CAST('2025-02-01' AS DATE)
    ORDER BY C.DATALCTOCTB
""")
rows = cur.fetchall()
print(f"Creditos de 5639 em Jan/2025: {len(rows)}")

# Conta os CODIGOHISTCTB distintos
from collections import Counter
hist_counter = Counter()
for r in rows:
    hist_counter[r[5]] += 1  # CODIGOHISTCTB

print("\nCODIGOHISTCTB mais frequentes:")
for hist_cod, cnt in hist_counter.most_common(10):
    # Pega a descrição
    cur.execute("SELECT DESCRHISTCTB FROM HISTORICOCTB WHERE CODIGOHISTCTB = ?", (hist_cod,))
    hr = cur.fetchone()
    descr = hr[0] if hr else "?"
    print(f"  HIST {hist_cod}: {cnt} lançamentos - '{descr}'")

# Exemplos com HIST=370 se existir
print("\n--- Amostras dos últimos 5 créditos ---")
for r in rows[-5:]:
    dt, cdeb, ccred, val, orig, hist_cod, descr_hist = r
    print(f"  {dt} D:{cdeb} C:{ccred} R${float(val or 0):,.2f} orig={orig} HIST={hist_cod} ({descr_hist})")

conn_q.close()
