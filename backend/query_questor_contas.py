import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

try:
    conn = get_conn("questor", 959)
    cur = conn.cursor()

    print("== TABELACONTABIL COLUMNS ==")
    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'TABELACONTABIL'")
    cols = [r[0].strip() for r in cur.fetchall()]
    print(cols)

    where_clause = "CODIGOEMPRESA = 959 AND " if "CODIGOEMPRESA" in cols else ""

    print("\n== CLIENTES ==")
    cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%CLIENTE%'")
    for r in cur.fetchall(): print(r)

    print("\n== DIFERIDOS ==")
    cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%DIFERID%'")
    for r in cur.fetchall(): print(r)
        
    print("\n== ANTECIPADOS ==")
    cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%ANTECIPAD%'")
    for r in cur.fetchall(): print(r)
        
    print("\n== TRIBUTOS ==")
    cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} (DESCRTABCTB LIKE '%PIS%' OR DESCRTABCTB LIKE '%COFINS%' OR DESCRTABCTB LIKE '%IRPJ%' OR DESCRTABCTB LIKE '%CSLL%')")
    for r in cur.fetchall(): print(r)
        
except Exception as e:
    print("ERRO:", e)
