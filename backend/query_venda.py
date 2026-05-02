import sys
sys.path.append('c:/Users/dirfe/.gemini/antigravity/scratch/vulcano2.0/backend')
from main import get_conn
conn = get_conn('vulcano')
cur = conn.cursor()
try:
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'VENDA'")
    print([r[0].strip() for r in cur.fetchall()])
except Exception as e:
    print('Error:', str(e))
