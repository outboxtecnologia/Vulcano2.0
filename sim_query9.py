import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_v = conn_vulcano.cursor()

cur_v.execute("SELECT NOME, CONTAESTAND FROM EMPREENDIMENTO WHERE ID = 959")
print("Empreendimento Vulcano:")
print(cur_v.fetchone())
