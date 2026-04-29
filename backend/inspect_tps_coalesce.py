import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT FIRST 10 T.COMPET, 
        SUM(T.VALORORIGEMGPS) as valor_antigo,
        SUM(COALESCE(
            (SELECT SUM(S.VALOR) FROM TERCEIROPGTOSERVICO S 
             WHERE S.CODIGOEMPRESA = T.CODIGOEMPRESA AND S.CODIGOTERC = T.CODIGOTERC AND S.COMPET = T.COMPET AND S.SEQ = T.SEQ),
            T.VALORORIGEMGPS
        )) as valor_novo
    FROM TERCEIROPGTO T
    WHERE T.CODIGOEMPRESA = 959 AND T.COMPET >= '2023-01-01'
    GROUP BY T.COMPET
    ORDER BY T.COMPET
""")
for r in cur.fetchall():
    print(r)
