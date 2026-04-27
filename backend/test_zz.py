import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

cur = get_conn("questor").cursor()
cur.execute("SELECT FIRST 10 * FROM LCTOCTB WHERE CODIGOORIGLCTOCTB='ZZ'")
print(cur.fetchall())
