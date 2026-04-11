from main import get_conn
conn_q = get_conn('questor')
cur_q = conn_q.cursor()
try:
    cur_q.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'HISTORICOCTB'")
    print("HISTORICOCTB columns:", [r[0].strip() for r in cur_q.fetchall()])

    cur_q.execute("SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'LCTOCTB'")
    print("\nLCTOCTB columns:", [r[0].strip() for r in cur_q.fetchall()])
    
except Exception as e:
    print('Erro:', e)
