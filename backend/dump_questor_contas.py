import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

try:
    conn = get_conn("questor", 959)
    cur = conn.cursor()

    cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'TABELACONTABIL'")
    cols = [r[0].strip() for r in cur.fetchall()]

    where_clause = "CODIGOEMPRESA = 959 AND " if "CODIGOEMPRESA" in cols else ""

    with open("questor_contas_dump.txt", "w", encoding="utf-8") as f:
        f.write("== CLIENTES ==\n")
        cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%CLIENTE%' OR DESCRTABCTB LIKE '%RECEBER%'")
        for r in cur.fetchall(): f.write(str(r) + "\n")

        f.write("\n== DIFERIDOS ==\n")
        cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%DIFERID%'")
        for r in cur.fetchall(): f.write(str(r) + "\n")
            
        f.write("\n== RECEITA ==\n")
        cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%RECEITA%' OR DESCRTABCTB LIKE '%VENDA%'")
        for r in cur.fetchall(): f.write(str(r) + "\n")

        f.write("\n== ANTECIPADOS ==\n")
        cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} DESCRTABCTB LIKE '%ANTECIPAD%' OR DESCRTABCTB LIKE '%APROPRIAR%' OR DESCRTABCTB LIKE '%A FATURAR%'")
        for r in cur.fetchall(): f.write(str(r) + "\n")
            
        f.write("\n== TRIBUTOS ==\n")
        cur.execute(f"SELECT CODIGOTABCTB, DESCRTABCTB FROM TABELACONTABIL WHERE {where_clause} (DESCRTABCTB LIKE '%PIS%' OR DESCRTABCTB LIKE '%COFINS%' OR DESCRTABCTB LIKE '%IRPJ%' OR DESCRTABCTB LIKE '%CSLL%')")
        for r in cur.fetchall(): f.write(str(r) + "\n")

    print("Dump successful!")
except Exception as e:
    print("ERRO:", e)
