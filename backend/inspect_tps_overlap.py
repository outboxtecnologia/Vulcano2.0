import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT FIRST 5 T.COMPET, T.VALORORIGEMGPS, SUM(S.VALOR)
    FROM TERCEIROPGTO T
    JOIN TERCEIROPGTOSERVICO S ON T.CODIGOEMPRESA = S.CODIGOEMPRESA 
        AND T.CODIGOTERC = S.CODIGOTERC AND T.COMPET = S.COMPET AND T.SEQ = S.SEQ
    WHERE T.CODIGOEMPRESA = 959 AND T.COMPET >= '2023-01-01'
    GROUP BY T.COMPET, T.VALORORIGEMGPS
""")
for r in cur.fetchall():
    print(r)
