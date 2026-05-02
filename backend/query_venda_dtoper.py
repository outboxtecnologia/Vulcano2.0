import sys
sys.path.append('c:/Users/dirfe/.gemini/antigravity/scratch/vulcano2.0/backend')
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
try:
    cur.execute("SELECT FIRST 5 DTOPER FROM VENDA")
    print(cur.fetchall())
except Exception as e:
    print('Error:', str(e))
