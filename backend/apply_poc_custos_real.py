import firebirdsql

try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB', charset='WIN1252')
    cur = conn.cursor()

    cur.execute('''
        SELECT DISTINCT ID_EMPREENDIMENTO 
        FROM POC_CUSTO_MENSAL_REAL 
        WHERE ID_EMPREENDIMENTO NOT IN (SELECT ID_EMPREENDIMENTO FROM POC_CUSTOS)
    ''')
    missing_emps = [r[0] for r in cur.fetchall()]
    print(f'Populating POC_CUSTOS for missing emps: {missing_emps}')

    cur.execute('SELECT MAX(ID) FROM POC_CUSTOS')
    max_id_row = cur.fetchone()[0]
    next_id = int(max_id_row) + 1 if max_id_row else 1
    
    inserts = 0

    for emp_id in missing_emps:
        cur.execute('SELECT CUSTOORCADO FROM EMPREENDIMENTO WHERE ID = ?', (emp_id,))
        orcado_row = cur.fetchone()
        custo_orcado = float(orcado_row[0]) if orcado_row and orcado_row[0] is not None else 0.0

        cur.execute('SELECT ANO, MES, CUSTO_TOTAL FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? ORDER BY ANO, MES', (emp_id,))
        rows = cur.fetchall()

        previous_custo = 0.0
        
        for r in rows:
            ano, mes, custo_total = r
            custo_total = float(custo_total)
            
            mensal = custo_total - previous_custo
            previous_custo = custo_total

            if custo_orcado > 0:
                percentual = (custo_total / custo_orcado) * 100.0
            else:
                percentual = 100.0
            if percentual > 100.0: percentual = 100.0

            periodo_str = f'{str(mes).zfill(2)}/{ano}'

            try:
                cur.execute('INSERT INTO POC_CUSTOS (ID_EMPREENDIMENTO, ANO, MES, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                            (emp_id, ano, mes, periodo_str, mensal, custo_total, percentual))
            except Exception as e:
                if 'ID' in str(e).upper() or 'NULL' in str(e).upper():
                    cur.execute('INSERT INTO POC_CUSTOS (ID, ID_EMPREENDIMENTO, ANO, MES, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                                (next_id, emp_id, ano, mes, periodo_str, mensal, custo_total, percentual))
                    next_id += 1
                else:
                    raise e
            inserts += 1

    conn.commit()
    print(f'Successfully inserted {inserts} records into POC_CUSTOS.')

except Exception as e:
    print('Error:', e)
