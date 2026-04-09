import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

cur = get_conn("questor").cursor()
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 AND RDB$RELATION_NAME LIKE '%SALDO%'")
print([r[0].strip() for r in cur.fetchall()])
