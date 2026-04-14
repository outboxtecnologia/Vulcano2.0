import fdb
conn = fdb.connect(dsn='127.0.0.1:3050:C:\\Projetos\\Firebird\\Questor.fdb', user='SYSDBA', password='masterkey')
cur = conn.cursor()
cur.execute("SELECT FIRST 10 ID_EMPREENDIMENTO, ID_CONTA_DEBITO, ID_CONTA_CREDITO, VALOR FROM LANCAMENTO_CONTABIL")
for row in cur.fetchall():
    print(row)
conn.close()
