import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

cur = get_conn("questor").cursor()
cur.execute("SELECT SUM(CASE WHEN CONTACTBDEB=5665 THEN VALORLCTOCTB ELSE -VALORLCTOCTB END) FROM LCTOCTB WHERE CODIGOEMPRESA=959 AND (CONTACTBDEB=5665 OR CONTACTBCRED=5665) AND CODIGOORIGLCTOCTB='ZZ'")
print('ZZ Impact:', cur.fetchone()[0])
