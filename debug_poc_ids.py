import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.main import get_conn

conn = get_conn('vulcano')
cur = conn.cursor()
cur.execute("SELECT FIRST 5 ID, ID_EMPREENDIMENTO, PERCENTUAL FROM POC")
print("POC IDs:", cur.fetchall())

cur.execute("SELECT FIRST 5 ID_EMPREENDIMENTO, ANO, MES, CUSTO_TOTAL FROM POC_CUSTO_MENSAL_REAL")
print("POC CUSTO IDs:", cur.fetchall())
