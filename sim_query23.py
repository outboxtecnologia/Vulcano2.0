import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT FIRST 10 CAST(COMPLHIST AS BLOB SUB_TYPE 0) FROM LCTOCTB WHERE CONTACTBCRED = 5639 AND CODIGOEMPRESA = 959
  """)
for r in cur_q.fetchall():
    h = r[0]
    t = ""
    if isinstance(h, (bytes, bytearray)): t = h.decode("cp1252", "ignore")
    elif hasattr(h, "read"): t = h.read().decode("cp1252", "ignore")
    print(t)
