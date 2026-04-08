import sys
import fdb

conn = fdb.connect(
    dsn='localhost:c:/questor/BD/PRINCIPAL.FDB',
    user='SYSDBA', password='masterkey'
)
cur = conn.cursor()
try:
    cur.execute('SELECT FIRST 5 * FROM TABELACONTABIL')
    cols = [d[0] for d in cur.description]
    with open('tabela_contabil_dump.txt', 'w', encoding='utf-8') as f:
        f.write(str(cols) + '\n')
        for r in cur.fetchall():
            f.write(str(r) + '\n')
            
    cur.execute('SELECT FIRST 10 MODELOPLANO, CONTA, CLASSIFIC, DESCRICAO, TIPO FROM CTB_CONTA')
    cols = [d[0] for d in cur.description]
    with open('ctb_conta_dump.txt', 'w', encoding='utf-8') as f:
        f.write(str(cols) + '\n')
        for r in cur.fetchall():
            f.write(str(r) + '\n')
except Exception as e:
    with open('error_db.txt', 'w') as f: f.write(str(e))
conn.close()
