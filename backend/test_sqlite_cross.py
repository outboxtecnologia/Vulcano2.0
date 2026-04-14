import sqlite3

try:
    conn = sqlite3.connect('poc_database.sqlite')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('Tabelas no SQLite:', tables)
    
    for t in tables:
        if 'cross' in t.lower() or 'feedback' in t.lower() or 'rules' in t.lower():
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            cnt = cur.fetchone()[0]
            print(f'Tabela {t}: {cnt} registros')
            
            if cnt > 0:
                cur.execute(f'SELECT * FROM {t} LIMIT 1')
                print(f'Amostra {t}:', cur.fetchone())
except Exception as e:
    print('Erro:', e)
