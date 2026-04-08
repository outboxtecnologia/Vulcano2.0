import fdb
conn_v = fdb.connect(dsn='127.0.0.1:C:/Vulcano/Database/VULCANO.FDB', user='SYSDBA', password='masterkey', charset='UTF8')
cur = conn_v.cursor()
cur.execute("SELECT ID, METRAGEM, NUMCADIMOB FROM UNIDADE WHERE IDBLOCO IN (SELECT ID FROM BLOCO WHERE IDEMPREENDIMENTO = 5) ROWS 5")
print('--- UNIDADES (EMP 5) ---')
for row in cur.fetchall():
    print(row)

cur.execute("SELECT FIRST 5 ID, IDUNIDADE, DISTRATO FROM VENDA")
print('--- VENDA (Algumas) ---')
for row in cur.fetchall():
    print(row)
