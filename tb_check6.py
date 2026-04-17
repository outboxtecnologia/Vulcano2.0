import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn
import traceback
try:
    conn_v = get_conn()
    cur = conn_v.cursor()
    cur.execute("SELECT ID, NOME, METRAGEMTOTAL FROM EMPREENDIMENTO WHERE CODIGOCENTROCUSTO = 35")
    emp = cur.fetchone()
    print("EMP:", emp)
    
    cur.execute("SELECT FIRST 5 U.ID, U.METRAGEM FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?", (emp[0],))
    print("UNIDADES U.METRAGEM:", cur.fetchall())
except Exception as e:
    traceback.print_exc()
