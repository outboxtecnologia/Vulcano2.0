import sys
sys.path.append(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

conn = get_conn("vulcano")
cur = conn.cursor()
cur.execute("SELECT FIRST 1 * FROM VENDA")
desc = [d[0] for d in cur.description]
print("COLUMNS IN VENDA:", desc)
conn.close()
