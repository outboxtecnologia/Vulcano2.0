from main import get_conn
conn_q = get_conn('questor')
cur_q = conn_q.cursor()
try:
    cur_q.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME LIKE '%HIST%' AND RDB$SYSTEM_FLAG = 0")
    print([r[0].strip() for r in cur_q.fetchall()])
    
    cur_q.execute("SELECT FIRST 10 L.HISTORICOCTB, L.COMPLLCTOGER, L.CODIGOHISTPADRAO FROM LCTOCTB L WHERE L.CODIGOEMPRESA = 959")
    print("\nLCTOCTB amostra:", cur_q.fetchall())
except Exception as e:
    print('Erro:', e)
