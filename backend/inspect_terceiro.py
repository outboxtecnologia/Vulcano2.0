import firebirdsql

DB_Q = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB"
conn = firebirdsql.connect(host="localhost", database=DB_Q, port=3050, user="SYSDBA", password="masterkey", charset="WIN1252")
cur = conn.cursor()

cur.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'TERCEIROPGTO' ORDER BY RDB$FIELD_POSITION")
cols = [r[0].strip() for r in cur.fetchall()]
print(f"TERCEIROPGTO cols ({len(cols)}):", cols)

if cols:
    cur.execute("SELECT FIRST 3 * FROM TERCEIROPGTO")
    desc = [d[0].strip() for d in cur.description]
    for row in cur.fetchall():
        print(dict(zip(desc, row)))

    cur.execute("""
        SELECT CODIGOEMPRESA, COMPET, COUNT(*) qtd, SUM(VALORORIGEMGPS) soma_gps
        FROM TERCEIROPGTO
        WHERE VALORORIGEMGPS > 0
        GROUP BY CODIGOEMPRESA, COMPET
        ORDER BY COMPET DESC
        ROWS 1 TO 5
    """)
    desc2 = [d[0].strip() for d in cur.description]
    print("\nResumo GPS por empresa/compet:")
    for row in cur.fetchall():
        print(" ", dict(zip(desc2, row)))
else:
    # Verificar se tabela existe com outro nome
    cur.execute("SELECT FIRST 10 RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%TERCEIRO%' OR RDB$RELATION_NAME LIKE '%GPS%'")
    for row in cur.fetchall():
        print("Tabela similar:", row[0].strip())

conn.close()
