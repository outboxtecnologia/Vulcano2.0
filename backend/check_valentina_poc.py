import firebirdsql
conn = firebirdsql.connect(
    host='localhost',
    database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB',
    user='SYSDBA',
    password='masterkey',
    charset='WIN1252'
)
c = conn.cursor()
c.execute("SELECT ID FROM EMPREENDIMENTO WHERE NOME='VALENTINA RESIDENCE'")
emp_id_row = c.fetchone()
if not emp_id_row:
    print("Not found")
else:
    emp_id = emp_id_row[0]
    print(f'EMP ID: {emp_id}')
    c.execute(f"SELECT MES, ANO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS WHERE ID_EMPREENDIMENTO={emp_id} ORDER BY ANO, MES")
    print('POC_CUSTOS:', c.fetchall())
    c.execute(f"SELECT PERIODO, PERCENTUAL FROM POC WHERE ID_EMPREENDIMENTO={emp_id} ORDER BY PERIODO")
    rows = []
    for r in c.fetchall():
        try:
           period = r[0].decode('win1252').strip() if isinstance(r[0], bytes) else r[0]
        except:
           period = r[0]
        rows.append((period, r[1]))
    print('POC:', rows)
conn.close()
