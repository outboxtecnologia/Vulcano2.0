import firebirdsql
import json

try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB', charset='WIN1252')
    cur = conn.cursor()

    cur.execute('''
        SELECT ID, CODIGOEMPRESA, NOME, CODIGOESTAB
        FROM EMPREENDIMENTO 
        WHERE NOME LIKE '%ATHEN%' OR NOME LIKE '%PALAS%' OR CODIGOEMPRESA = 959
    ''')
    emps = cur.fetchall()
    
    out = {'emps_found': []}
    for e in emps:
        out['emps_found'].append({'ID': e[0], 'CODIGOEMPRESA': e[1], 'NOME': e[2], 'ESTAB': e[3]})
        
    cur.execute('''
        SELECT DISTINCT RDB$RELATION_NAME
        FROM RDB$RELATIONS
        WHERE RDB$VIEW_BLR IS NULL 
        AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
        AND RDB$RELATION_NAME LIKE 'POC%'
    ''')
    tables = [r[0].strip() for r in cur.fetchall()]
    out['poc_tables'] = tables
    
    out['poc_data'] = {}
    
    for emp in out['emps_found']:
        emp_id = emp['ID']
        emp_data = {}
        for tbl in tables:
            try:
                cur.execute(f'SELECT FIRST 5 * FROM {tbl} WHERE ID_EMPREENDIMENTO = ?', (emp_id,))
                rows = cur.fetchall()
                if rows:
                    emp_data[tbl] = len(rows)
            except Exception as e:
                pass
        
        # also check just in case the column is EMPREENDIMENTO
        for tbl in tables:
            try:
                cur.execute(f'SELECT FIRST 5 * FROM {tbl} WHERE EMPREENDIMENTO = ?', (emp_id,))
                rows = cur.fetchall()
                if rows:
                    emp_data[tbl] = len(rows)
            except Exception as e:
                pass
                
        if emp_data:
            out['poc_data'][emp_id] = emp_data

    with open('backend/check_palas.json', 'w') as f:
        json.dump(out, f, indent=2)
        
    print('Search complete.')

except Exception as e:
    print('Error:', e)
