import sqlite3
import glob

print("Procurando templates...")
db_files = glob.glob('*.db') + glob.glob('*.sqlite*') + glob.glob('*.sqlite3')
for f in set(db_files):
    try:
        conn = sqlite3.connect(f)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'pdf_parser_templates' in tables:
            row = conn.execute("SELECT id, nome, python_code FROM pdf_parser_templates ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                with open("last_generated.py", "w", encoding="utf-8") as out:
                    out.write(row[2])
                print(f"Salvo script {row[0]} em last_generated.py")
    except Exception as e:
        pass
