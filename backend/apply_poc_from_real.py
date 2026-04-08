import firebirdsql
import calendar
import builtins

try:
    conn = firebirdsql.connect(host='localhost', port=3050, user='SYSDBA', password='masterkey', database=r'C:\\Users\\dirfe\\OneDrive\\Documentos\\Vulcano\\VULCANO.FDB', charset='WIN1252')
    cur = conn.cursor()

    # Find missing empreendimentos
    cur.execute('''
        SELECT DISTINCT ID_EMPREENDIMENTO 
        FROM POC_CUSTO_MENSAL_REAL 
        WHERE ID_EMPREENDIMENTO NOT IN (SELECT ID_EMPREENDIMENTO FROM POC)
          AND ID_EMPREENDIMENTO NOT IN (SELECT ID_EMPREENDIMENTO FROM POC_CUSTOS)
    ''')
    missing_emps = [r[0] for r in cur.fetchall()]
    print(f'Empreendimentos sem POC, mas com POC_CUSTO_MENSAL_REAL: {missing_emps}')

    cur.execute('SELECT MAX(ID) FROM POC')
    max_id_row = cur.fetchone()[0]
    next_id = int(max_id_row) + 1 if max_id_row else 1
    
    inserts = 0
    updates = 0

    for emp_id in missing_emps:
        # Get CUSTOORCADO
        cur.execute('SELECT CUSTOORCADO FROM EMPREENDIMENTO WHERE ID = ?', (emp_id,))
        orcado_row = cur.fetchone()
        custo_orcado = float(orcado_row[0]) if orcado_row and orcado_row[0] is not None else 0.0

        cur.execute('SELECT ANO, MES, CUSTO_TOTAL FROM POC_CUSTO_MENSAL_REAL WHERE ID_EMPREENDIMENTO = ? ORDER BY ANO, MES', (emp_id,))
        rows = cur.fetchall()

        max_incurred = 0.0
        
        for r in rows:
            ano, mes, custo_total = r
            custo_total = float(custo_total)
            if custo_total > max_incurred:
                max_incurred = custo_total

            if custo_orcado > 0:
                percentual = (custo_total / custo_orcado) * 100.0
            else:
                # If budget is 0, since we have positive cost, pct is 100%
                percentual = 100.0

            # Cap at 100%
            if percentual > 100.0:
                percentual = 100.0

            last_day = calendar.monthrange(int(ano), int(mes))[1]
            periodo = f'{ano}-{int(mes):02d}-{last_day:02d}'

            # Insert into POC
            try:
                cur.execute('INSERT INTO POC (ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?)', (emp_id, periodo, percentual))
            except Exception as e:
                if 'ID' in str(e).upper() or 'NULL' in str(e).upper():
                    cur.execute('INSERT INTO POC (ID, ID_EMPREENDIMENTO, PERIODO, PERCENTUAL) VALUES (?, ?, ?, ?)', (next_id, emp_id, periodo, percentual))
                    next_id += 1
                else:
                    raise e
            inserts += 1

        # Check if we need to update the budget internally
        if max_incurred > custo_orcado:
            cur.execute('UPDATE EMPREENDIMENTO SET CUSTOORCADO = ? WHERE ID = ?', (max_incurred, emp_id))
            updates += 1

    conn.commit()
    print(f'Total POC records inserted: {inserts}')
    print(f'Total EMPREENDIMENTO CUSTOORCADO updated (aumentando o orçado): {updates}')

except Exception as e:
    print('Error:', e)
