import sqlite3
import glob

print("Procurando banco de dados com parser_templates...")
db_files = glob.glob('*.db') + glob.glob('*.sqlite*') + glob.glob('*.sqlite3')
for f in set(db_files):
    try:
        conn = sqlite3.connect(f)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'parser_templates' in tables:
            print(f"Encontrado no banco: {f}")
            row = conn.execute("SELECT id, nome, python_code FROM parser_templates ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                print(f"ID: {row[0]}, Nome: {row[1]}")
                print(row[2])
            else:
                print("Tabela vazia.")
    except Exception as e:
        print(f"Erro ao ler {f}: {e}")
