import sqlite3, glob
for f in glob.glob('backend/*.sqlite*'):
    if 'shm' in f or 'wal' in f: continue
    try:
        conn = sqlite3.connect(f)
        tables = [r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type=''table''').fetchall()]
        if 'auditoria_memoria_arraste' in tables:
            print(f'Found table in {f}')
            print(conn.execute('SELECT * FROM auditoria_memoria_arraste').fetchall())
    except Exception as e:
        pass
