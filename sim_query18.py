import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), SUM(C.VALORLCTOCTB)
      FROM LCTOCTB C
      WHERE C.CONTACTBDEB = 5639 AND C.CODIGOEMPRESA = 1 AND C.DATALCTOCTB >= '2023-12-01'
      GROUP BY 1, 2 ORDER BY 1, 2
  """)
print("DEBITS TO 5639:")
print([r for r in cur_q.fetchall()])
