import sys
sys.path.append(r"c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend")
from main import get_conn

cur = get_conn("questor").cursor()
cur.execute("""
    SELECT DATALCTOCTB, VALORLCTOCTB, CODIGOORIGLCTOCTB, CAST(COMPLHIST AS BLOB SUB_TYPE 0) 
    FROM LCTOCTB 
    WHERE CODIGOEMPRESA=959 
      AND (CONTACTBDEB=5665 OR CONTACTBCRED=5665) 
      AND EXTRACT(YEAR FROM DATALCTOCTB)=2024 
      AND EXTRACT(MONTH FROM DATALCTOCTB)=12
""")
for r in cur.fetchall():
    print(str(r[0]), float(r[1]), r[2], r[3].decode('cp1252') if isinstance(r[3], (bytes, bytearray)) else str(r[3]))
