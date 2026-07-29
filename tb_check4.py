import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn()
cur = conn_v.cursor()
cur.execute("SELECT FIRST 1 METRAGEM, AREA_TOTAL FROM UNIDADE WHERE DESCRICAO LIKE '%APTO 201%'")
print(cur.fetchone())
