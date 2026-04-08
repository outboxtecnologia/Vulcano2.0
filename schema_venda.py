import sys
import fdb

try:
    conn = fdb.connect(dsn='127.0.0.1:C:/Vulcano/Database/VULCANO.FDB', user='SYSDBA', password='masterkey', charset='UTF8')
    cur = conn.cursor()
    cur.execute('SELECT first 1 * FROM VENDA')
    cols = [desc[0] for desc in cur.description]
    
    cur.execute('SELECT first 1 * FROM UNIDADE')
    cols_u = [desc[0] for desc in cur.description]
    
    with open('venda_schema.txt', 'w') as f:
        f.write('VENDA COLS:\n')
        f.write(', '.join(cols) + '\n\n')
        f.write('UNIDADE COLS:\n')
        f.write(', '.join(cols_u) + '\n')

except Exception as e:
    with open('venda_schema.txt', 'w') as f:
        f.write('ERROR: ' + str(e))
