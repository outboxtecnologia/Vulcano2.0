import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from main import get_conn

conn_v = get_conn("vulcano")
cur_v = conn_v.cursor()

try:
    cur_v.execute('SELECT FIRST 1 PERIODO FROM POC')
    print("POC PERIODO:", cur_v.fetchone()[0])
except Exception as e:
    print("POC Error:", e)

try:    
    cur_v.execute('SELECT FIRST 1 MES FROM INDICE_REAJUSTE_TABELA')
    print("INDICE MES:", cur_v.fetchone()[0])
except Exception as e:
    print("INDICE Error:", e)

conn_v.close()
