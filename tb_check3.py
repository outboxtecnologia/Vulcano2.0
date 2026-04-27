import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
conn_v = get_conn()
cur = conn_v.cursor()
cur.execute("SELECT CODIGOEMPREENDIMENTO, NOME_EMPREENDIMENTO, AREA_TOTAL_VENDAVEL FROM EMPREENDIMENTO where CC = 35")
print("EMP:", cur.fetchone())
cur.execute("SELECT AREA_TOTAL FROM UNIDADES where CODIGOEMPREENDIMENTO = (SELECT CODIGOEMPREENDIMENTO FROM EMPREENDIMENTO where CC = 35) ROWS 1")
print("UNI:", cur.fetchone())
