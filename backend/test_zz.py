import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\.gemini\\antigravity\\scratch\\questor_mapping\\QUESTOR_EMPRESA_959.FDB')
    cur = conn.cursor()
    cur.execute("SELECT FIRST 10 CHAVEORIGEM, ORIGEMDADO, CODIGOORIGLCTOCTB, CODIGOHISTCTB FROM LCTOCTB WHERE CHAVEORIGEM STARTING WITH 'ZZ'")
    res = cur.fetchall()
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'w', encoding='utf-8').write('LCTOs ZZ: ' + str(res))
    
    # Also find ANY entry with ORIGEMDADO=... that looks like a closing entry
    cur.execute("SELECT FIRST 10 CHAVEORIGEM, ORIGEMDADO, CODIGOLCTOPROG FROM LCTOCTB WHERE CODIGOORIGLCTOCTB = 5 OR CODIGOHISTCTB IN (370, 999) OR TIPOLANCAMENTO = 3")
    res2 = cur.fetchall()
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'a', encoding='utf-8').write('\nOutros encerramentos: ' + str(res2))
except Exception as e:
    open('c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/backend/test_zz_out.txt', 'w', encoding='utf-8').write(str(e))
