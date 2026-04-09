import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

cur = get_conn("questor").cursor()
cur.execute("SELECT EXTRACT(MONTH FROM DATALCTOCTB) as M, SUM(VALORLCTOCTB) FROM LCTOCTB WHERE CODIGOEMPRESA=959 AND (CONTACTBDEB=4910 OR CONTACTBCRED=4910) AND EXTRACT(YEAR FROM DATALCTOCTB)=2026 GROUP BY M")
print(cur.fetchall())
