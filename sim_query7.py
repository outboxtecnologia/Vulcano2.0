import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT FIRST 5 ID_CONTA, CLASSIFICACAO, CODIGOREDUZIDO, DESCRICAO
      FROM PLANOCONTAS
      WHERE CODIGOREDUZIDO = 5639 OR CLASSIFICACAO LIKE '%5639%' OR DESCRICAO LIKE '%RESIDENCIAL STUTTGART%'
  """)
for r in cur_q.fetchall():
    print(r)
