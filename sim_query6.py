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
      SELECT C.CONTACTBCRED, H.DESCRHISTCTB
      FROM LCTOGER G
      JOIN LCTOCTB C ON C.CHAVELCTOCTB = G.CHAVELCTOCTB AND C.CODIGOEMPRESA = G.CODIGOEMPRESA
      LEFT JOIN HISTORICOCTB H ON H.CODIGOHISTCTB = C.CODIGOHISTCTB
      WHERE G.CODIGOCENTROCUSTO = ? AND G.NATURLCTOCTB = -1 AND G.DATALCTOCTB >= '2020-01-01'
  """, (cc_empreendimento,))
s = set()
for r in cur_q.fetchall():
    t_desc = str(r[1] or '').upper()
    if 'TRANSFER' in t_desc and 'CUSTO' in t_desc:
        s.add(r[0])
print("Distinct CONTACTBCRED for these transfers:", s)
