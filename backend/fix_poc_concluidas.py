import firebirdsql
import calendar

try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB', charset='WIN1252')
    cur = conn.cursor()

    # The 4 old properties we backfilled
    target_ids = (154, 189, 370, 371)
    
    cur.execute('SELECT MAX(ID) FROM POC')
    max_id_row = cur.fetchone()[0]
    next_poc_id = int(max_id_row) + 1 if max_id_row else 1

    cur.execute('SELECT MAX(ID) FROM POC_CUSTOS')
    max_id_row = cur.fetchone()[0]
    next_custos_id = int(max_id_row) + 1 if max_id_row else 1

    placeholders = ','.join(['?'] * len(target_ids))
    cur.execute(f'SELECT ID, OBRACONCLUIDA, DATACONCLUSAO, CUSTOORCADO FROM EMPREENDIMENTO WHERE ID IN ({placeholders})', target_ids)
    emps = cur.fetchall()

    for emp in emps:
        emp_id = emp[0]
        obra_concluida = str(emp[1]).strip().upper() if emp[1] else 'N'
        data_conclusao = emp[2]
        custo_orcado = float(emp[3] or 0.0)

        if obra_concluida == 'S':
            # See if POC reached 100%
            cur.execute('SELECT MAX(PERCENTUAL) FROM POC WHERE ID_EMPREENDIMENTO = ?', (emp_id,))
            max_poc = cur.fetchone()[0]
            max_poc = float(max_poc or 0.0)

            if max_poc < 99.99:
                # We need to inject a 100% record
                cur.execute('SELECT MAX(CUSTO_ACUMULADO) FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ?', (emp_id,))
                max_custo = cur.fetchone()[0]
                max_custo = float(max_custo or 0.0)
                
                # Use Date of Conclusion, or end of 2018 if none
                if data_conclusao:
                    # e.g. 2018-12-31
                    ano = data_conclusao.year
                    mes = data_conclusao.month
                else:
                    ano = 2020
                    mes = 12
                    
                gap_mensal = custo_orcado - max_custo if custo_orcado > max_custo else 0.0
                custo_final = custo_orcado if custo_orcado > max_custo else max_custo
                
                # Check if there is already a record in that month
                periodo_str = f'{str(mes).zfill(2)}/{ano}'
                cur.execute('SELECT COUNT(*) FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO = ? AND PERIODO = ?', (emp_id, periodo_str))
                cnt = cur.fetchone()[0]
                if cnt > 0:
                    # shift by one month
                    mes += 1
                    if mes > 12:
                        mes = 1
                        ano += 1
                    periodo_str = f'{str(mes).zfill(2)}/{ano}'

                last_day = calendar.monthrange(ano, mes)[1]
                periodo_data = f'{ano}-{mes:02d}-{last_day:02d}'

                # Insert 100%
                try:
                    cur.execute('INSERT INTO POC (ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?)', (emp_id, periodo_data, 100.0))
                except:
                    cur.execute('INSERT INTO POC (ID, ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?, ?)', (next_poc_id, emp_id, periodo_data, 100.0))
                    next_poc_id += 1

                try:
                    cur.execute('INSERT INTO POC_CUSTOS (ID_EMPREENDIMENTO, ANO, MES, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                                (emp_id, ano, mes, periodo_str, gap_mensal, custo_final, 100.0))
                except:
                    cur.execute('INSERT INTO POC_CUSTOS (ID, ID_EMPREENDIMENTO, ANO, MES, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                                (next_custos_id, emp_id, ano, mes, periodo_str, gap_mensal, custo_final, 100.0))
                    next_custos_id += 1

                print(f'Emp {emp_id}: Concluido injetado em {periodo_str}!')

    conn.commit()
    print('Feito.')

except Exception as e:
    print('Error:', e)
