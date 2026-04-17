import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT SUM(VALORLCTOCTB)
      FROM LCTOCTB
      WHERE CONTACTBCRED = 5639 AND CODIGOEMPRESA = 1
  """)
print(cur_q.fetchall())
