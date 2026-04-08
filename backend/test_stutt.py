import os
import sys

sys.path.insert(0, os.path.abspath(".."))
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()
cur.execute("SELECT ID, NOME, CONTACUSTO, CONTACLI, CONTACAIXA FROM EMPREENDIMENTO WHERE NOME LIKE '%STUTT%'")
print("RESULT:", cur.fetchall())
