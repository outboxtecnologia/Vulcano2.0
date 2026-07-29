import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT EXTRACT(YEAR FROM DATALCTOCTB), COUNT(*)
      FROM LCTOCTB
      WHERE CONTACTBDEB = 5639 OR CONTACTBCRED = 5639
      GROUP BY 1 ORDER BY 1
  """)
print([r for r in cur_q.fetchall()])
