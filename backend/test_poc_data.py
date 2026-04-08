import firebirdsql

try:
    conn_vulcano = firebirdsql.connect(
        host='localhost', 
        port=3050, 
        database=r'C:\Users\dirfe\OneDrive\Documentos\Vulcano\VULCANO.FDB', 
        user='SYSDBA', 
        password='masterkey',
        charset='WIN1252'
    )
    c_v = conn_vulcano.cursor()

    c_v.execute('SELECT e.ID, e.NOME FROM EMPREENDIMENTO e')
    emps = {r[0]: str(r[1]).strip() for r in c_v.fetchall()}
    
    # Read POC_CUSTOS
    c_v.execute('SELECT ID_EMPREENDIMENTO, MES, ANO, PERCENTUAL_CONCLUIDO FROM POC_CUSTOS')
    poc_custos = c_v.fetchall()

    print("POC_CUSTOS examples:")
    for row in poc_custos[:10]:
        print(f"Emp: {emps.get(row[0], row[0])}, Mes: {row[1]}, Ano: {row[2]}, POC: {row[3]}")

    c_v.execute('SELECT ID_EMPREENDIMENTO, PERIODO, PERCENTUAL FROM POC')
    poc_normal = c_v.fetchall()

    print("\nPOC examples:")
    for row in poc_normal[:10]:
        print(f"Emp: {emps.get(row[0], row[0])}, Periodo: {row[1]}, POC: {row[2]}")

    conn_vulcano.close()
except Exception as e:
    print('Error:', e)
