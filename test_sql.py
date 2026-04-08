import fdb

try:
    con = fdb.connect(dsn='C:\\Users\\dirfe\\.gemini\\antigravity\\scratch\\questor_explorer\\backend\\VULCANO.FDB',
                      user='sysdba', password='masterkey', charset='WIN1252')
    cur = con.cursor()
    cur.execute("SELECT FIRST 5 v.ID, v.ID_CLIENTE, c.NOME FROM VENDA v LEFT JOIN CLIENTE c ON v.ID_CLIENTE = c.ID")
    print(cur.fetchall())
except Exception as e:
    print(e)
