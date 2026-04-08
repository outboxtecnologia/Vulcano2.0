import firebirdsql
import calendar

try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB')
    cur = conn.cursor()

    cur.execute('''
        SELECT DISTINCT ID_EMPREENDIMENTO 
        FROM POC_CUSTOS 
        WHERE ID_EMPREENDIMENTO NOT IN (SELECT DISTINCT ID_EMPREENDIMENTO FROM POC)
    ''')
    missing_emps = [r[0] for r in cur.fetchall()]

    print(f'Empreendimentos without POC: {missing_emps}')

    inserts = 0

    # Get Max ID
    cur.execute('SELECT MAX(ID) FROM POC')
    max_id_row = cur.fetchone()[0]
    next_id = int(max_id_row) + 1 if max_id_row else 1

    for emp_id in missing_emps:
        cur.execute('SELECT MES, ANO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ? ORDER BY ANO, MES', (emp_id,))
        rows = cur.fetchall()
        for r in rows:
            mes, ano, pct = r
            last_day = calendar.monthrange(int(ano), int(mes))[1]
            periodo = f'{ano}-{int(mes):02d}-{last_day:02d}'
            
            try:
                cur.execute('INSERT INTO POC (ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?)', (emp_id, periodo, float(pct)))
            except Exception as e:
                if 'ID' in str(e).upper() or 'NULL' in str(e).upper():
                    cur.execute('INSERT INTO POC (ID, ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?, ?)', (next_id, emp_id, periodo, float(pct)))
                    next_id += 1
                else:
                    raise e
            inserts += 1

    conn.commit()
    print(f'Successfully inserted {inserts} POC records.')

except Exception as e:
    print('Error:', e)
