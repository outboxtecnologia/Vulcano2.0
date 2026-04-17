import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn()
cur = conn_v.cursor()
cur.execute("SELECT METRAGEMTOTAL FROM EMPREENDIMENTO WHERE CC = 35")
print("EMPREENDIMENTO:", cur.fetchone())
cur.execute("SELECT FIRST 5 METRAGEM, AREA FROM UNIDADE WHERE IDBLOCO IN (SELECT ID FROM BLOCO WHERE IDEMPREENDIMENTO = 191)")
print("UNIDADES:", cur.fetchall())
