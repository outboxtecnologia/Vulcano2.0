import sys
import os

from core.database import get_conn

conn = get_conn('vulcano')
cur = conn.cursor()
try:
    cur.execute('SELECT ID, NOME, CODIGOCENTROCUSTO, CONTACUSTO, CONTAESTAND FROM EMPREENDIMENTO')
    rows = cur.fetchall()
    print("EMPREENDIMENTO TABLE ROWS:")
    for r in rows: print(r)
except Exception as e:
    print('ERROR:', e)
