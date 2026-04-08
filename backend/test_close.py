import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\.gemini\\antigravity\\scratch\\questor_mapping\\QUESTOR_EMPRESA_959.FDB')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 10 DATALCTOCTB, VALORLCTOCTB, CHAVEORIGEM, ORIGEMDADO, CODIGOORIGLCTOCTB, CODIGOHISTCTB FROM LCTOCTB WHERE CODIGOEMPRESA = 959 AND EXTRACT(MONTH FROM DATALCTOCTB) = 12 AND EXTRACT(DAY FROM DATALCTOCTB) = 31 ORDER BY DATALCTOCTB DESC, VALORLCTOCTB DESC")
    print('LCTOs 31/12:', cur.fetchall())
except Exception as e:
    print(e)
