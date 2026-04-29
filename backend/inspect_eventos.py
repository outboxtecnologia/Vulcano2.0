import firebirdsql
conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_mapping\QUESTOR_EMPRESA_959.FDB')
cur = conn.cursor()
cur.execute("""
    SELECT FIRST 10 C.CODIGOEVENTO, COUNT(*), SUM(C.VALOREVENTO)
    FROM CALCULORATEIO C
    JOIN PERIODOCALCULO P ON P.CODIGOPERCALCULO = C.CODIGOPERCALCULO
    WHERE C.CODIGOEMPRESA = 959 AND P.COMPET >= '2023-01-01'
    GROUP BY C.CODIGOEVENTO
    ORDER BY 3 DESC
""")
print("\nCALCULORATEIO EVENTS SUM:")
for r in cur.fetchall():
    print(r)
