import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_q = conn_questor.cursor()

cur_q.execute("""
      SELECT CONTACTB, CLASSIFCONTA, DESCRCONTA, CODIGOREDUZIDO
      FROM PLANOESPEC
      WHERE CODIGOEMPRESA = 1 AND (CODIGOREDUZIDO = 5639 OR CLASSIFCONTA LIKE '%5639%' OR DESCRCONTA LIKE '%STUTTGART%')
  """)
for r in cur_q.fetchall():
    print(r)
