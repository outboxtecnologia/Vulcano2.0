import sqlite3

def check_db(name):
    try:
        conn = sqlite3.connect(name)
        tables = [x[0] for x in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        with open('db_tables.txt', 'w') as f:
             f.write(f"Tables in {name}: {tables}\n")
             if 'POC' in tables:
                 f.write("POC schema: " + conn.execute("SELECT sql FROM sqlite_master WHERE name='POC'").fetchone()[0] + "\n")
             if 'POC_CUSTOS' in tables:
                 f.write("POC_CUSTOS schema: " + conn.execute("SELECT sql FROM sqlite_master WHERE name='POC_CUSTOS'").fetchone()[0] + "\n")
             if 'EMPREENDIMENTO' in tables:
                 f.write("EMPREENDIMENTO schema: " + conn.execute("SELECT sql FROM sqlite_master WHERE name='EMPREENDIMENTO'").fetchone()[0] + "\n")
    except Exception as e:
        print(f"Error reading {name}: {e}")

check_db('poc_database.sqlite')
