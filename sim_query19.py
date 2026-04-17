import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT COUNT(*)
      FROM LCTOCTB
      WHERE CONTACTBDEB = 5639 OR CONTACTBCRED = 5639
  """)
print("TOTAL RECORDS FOR 5639:", cur_q.fetchone()[0])
