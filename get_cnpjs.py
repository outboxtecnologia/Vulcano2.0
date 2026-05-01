import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.main import get_conn

conn = get_conn("questor")
try:
    cur = conn.cursor()
    cur.execute("""
        SELECT CODIGOEMPRESA, NOMEESTAB, INSCRFEDERAL
        FROM ESTAB 
        WHERE CODIGOESTAB = 1
          AND CODIGOEMPRESA IN (456, 3764, 2580, 3895, 3788, 1976)
    """)
    with open("cnpjs_empresas.txt", "w", encoding="utf-8") as f:
        for row in cur.fetchall():
            f.write(f"Empresa: {row[0]} - {row[1]}\nCNPJ: {row[2]}\n\n")
    print("Arquivo cnpjs_empresas.txt gerado com sucesso.")
finally:
    conn.close()
