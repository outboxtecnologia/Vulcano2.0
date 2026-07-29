import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn
import re

empreendimento_id = 959
empresa_id = 1
cc_empreendimento = 35

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT EXTRACT(YEAR FROM DATALCTOCTB), CONTACTBDEB, CONTACTBCRED, COUNT(*)
      FROM LCTOCTB
      WHERE (CONTACTBDEB = 5639 OR CONTACTBCRED = 5639) AND CODIGOEMPRESA = 959
      GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
  """)
print("DEB / CRED / QUANTIDADE")
for r in cur_q.fetchall():
    print(r)
