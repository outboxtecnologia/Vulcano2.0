import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

try:
    conn = get_conn("questor", 959)
    cur = conn.cursor()
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='PLANOESPEC'")
    cols=[r[0].strip() for r in cur.fetchall()]
    
    with open("planoespec_cols_rows.txt", "w", encoding="utf-8") as f:
        f.write("COLUNAS: " + str(cols) + "\n\n")
        
        # Test query for CLASSIFCONTA and DESCRCONTA
        try:
            cur.execute("SELECT CLASSIFCONTA, DESCRCONTA, TIPOCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = 959 AND CLASSIFCONTA IS NOT NULL ORDER BY CLASSIFCONTA")
            f.write("ROWS:\n")
            for r in cur.fetchmany(50):
                f.write(str(r) + "\n")
        except Exception as e2:
            f.write("Aviso ao tentar ler campos diretos: " + str(e2) + "\n")
            
except Exception as e:
    print("Erro:", e)
