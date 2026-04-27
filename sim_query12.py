import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT APELIDOCONTA, CONTACTB, CLASSIFCONTA, DESCRCONTA
      FROM PLANOESPEC
      WHERE CODIGOEMPRESA = 1 AND APELIDOCONTA IN ('5639', 5639)
  """)
print([r for r in cur_q.fetchall()])
