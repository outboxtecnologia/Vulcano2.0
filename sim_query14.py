import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT RDB\
      FROM RDB\
      WHERE RDB\ = 0 AND RDB\ LIKE '%CONTA%'
  """)
print([r[0].strip() for r in cur_q.fetchall()])
