import firebirdsql
import calendar

try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB', charset='WIN1252')
    cur = conn.cursor()

    empset = [189, 370, 371, 154]  # We know these are the ones we touched. Let's get the exact list from POC_CUSTO_MENSAL_REAL
    
    cur.execute('''
        SELECT DISTINCT ID_EMPREENDIMENTO 
        FROM POC_CUSTO_MENSAL_REAL 
    ''')
    all_real = [r[0] for r in cur.fetchall()]
    # actually, I want to delete the ones we just inserted. Since they were missing before our scripts:
    # However we did this for 369, 370, 371, 189...
    # I can just delete ALL from POC and POC_CUSTOS WHERE ID_EMPREENDIMENTO IN these specific ones.
    # To be safe, I will explicitly list them:
    # 189, 370, 371, and 154 (Palas Athenas)
    # Are there any others? The previous script printed: 'Empreendimentos without POC: [189, 370, 371]'
    # Then I did Palas Athenas manually maybe? Wait, Palas Athenas ID is 154. Palas Athenas was in missing_emps when I ran the script a 2nd/3rd time because I ran it generically.
    # So I will clear POC and POC_CUSTOS for all IDs that have NO data in VENDA, wait, no, I just delete where ID_EMPREENDIMENTO IN (154, 189, 370, 371).
    target_ids = (154, 189, 370, 371)
    
    placeholders = ','.join(['?'] * len(target_ids))
    cur.execute(f'DELETE FROM POC WHERE ID_EMPREENDIMENTO IN ({placeholders})', target_ids)
    cur.execute(f'DELETE FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO IN ({placeholders})', target_ids)
    conn.commit()

    cur.execute('SELECT MAX(ID) FROM POC')
    max_id_row = cur.fetchone()[0]
    next_poc_id = int(max_id_row) + 1 if max_id_row else 1

    cur.execute('SELECT MAX(ID) FROM POC_CUSTOS')
    max_id_row = cur.fetchone()[0]
    next_custos_id = int(max_id_row) + 1 if max_id_row else 1

    for emp_id in target_ids:
        cur.execute('SELECT CUSTOORCADO FROM EMPREENDIMENTO WHERE ID = ?', (emp_id,))
        orc_row = cur.fetchone()
        custo_orcado = float(orc_row[0]) if orc_row and orc_row[0] is not None else 0.0

        cur.execute('SELECT ANO, MES, CUSTO_TOTAL FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? ORDER BY ANO, MES', (emp_id,))
        rows = cur.fetchall()

        running_custo = 0.0
        
        for r in rows:
            ano, mes, custo_mensal = r
            custo_mensal = float(custo_mensal)
            running_custo += custo_mensal

            if custo_orcado > 0:
                percentual = (running_custo / custo_orcado) * 100.0
            else:
                percentual = 100.0
            if percentual > 100.0: percentual = 100.0

            # Last day for POC
            last_day = calendar.monthrange(int(ano), int(mes))[1]
            periodo_data = f'{ano}-{int(mes):02d}-{last_day:02d}'
            periodo_str = f'{str(mes).zfill(2)}/{ano}'

            # Insert POC
            try:
                cur.execute('INSERT INTO POC (ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?)', (emp_id, periodo_data, percentual))
            except Exception as e:
                cur.execute('INSERT INTO POC (ID, ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?, ?)', (next_poc_id, emp_id, periodo_data, percentual))
                next_poc_id += 1

            # Insert POC_CUSTOS
            try:
                cur.execute('INSERT INTO POC_CUSTOS (ID_EMPREENDIMENTO, ANO, MES, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                            (emp_id, ano, mes, periodo_str, custo_mensal, running_custo, percentual))
            except Exception as e:
                cur.execute('INSERT INTO POC_CUSTOS (ID, ID_EMPREENDIMENTO, ANO, MES, PERIODO, TOTAL_PERIODO, CUSTO_ACUMULADO, PERCENTUAL_CONCLUIDO) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                            (next_custos_id, emp_id, ano, mes, periodo_str, custo_mensal, running_custo, percentual))
                next_custos_id += 1

    conn.commit()
    print('Fix completed successfully!')

except Exception as e:
    print('Error:', e)
