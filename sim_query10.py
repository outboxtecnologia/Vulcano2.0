import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_conn

conn_vulcano, conn_questor = get_conn(), get_conn("questor")
cur_v = conn_vulcano.cursor()

cur_v.execute("SELECT ID, NOME, CODIGOCENTROCUSTO, CONTAESTAND FROM EMPREENDIMENTO WHERE NOME LIKE '%STUTTGART%'")
print("Empreendimentos:")
for r in cur_v.fetchall():
    print(r)
