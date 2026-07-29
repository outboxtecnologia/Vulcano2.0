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
      SELECT EXTRACT(YEAR FROM C.DATALCTOCTB), EXTRACT(MONTH FROM C.DATALCTOCTB), SUM(C.VALORLCTOCTB)
      FROM LCTOCTB C
      WHERE C.CONTACTBCRED = 5639 AND C.CODIGOEMPRESA = ? AND C.DATALCTOCTB >= '2023-12-01'
      GROUP BY 1, 2 ORDER BY 1, 2
  """, (empresa_id,))
print("LCTOCTB 5639 All Credits:")
for r in cur_q.fetchall():
    print(r)
