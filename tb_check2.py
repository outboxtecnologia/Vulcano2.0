import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn()
cur = conn_v.cursor()
cur.execute("SELECT id_empreendimento, nome, METRAGEM_TOTAL FROM EMPREENDIMENTO where id_empreendimento = 191")
print(cur.fetchone())
cur.execute("SELECT id_unidade, METRAGEM FROM UNIDADE where id_empreendimento = 191 ROWS 1")
print(cur.fetchone())
