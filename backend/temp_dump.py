import sys, os, json
sys.path.append(os.getcwd())
from main import get_conn
conn = get_conn("vulcano")
cur = conn.cursor()
cur.execute("SELECT ID, DESCRICAO FROM PLANSIT WHERE ID IN (4829, 4996, 4958, 4845)")
print(cur.fetchall())
