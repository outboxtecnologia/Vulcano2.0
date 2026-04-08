import sqlite3
conn = sqlite3.connect('poc_database.sqlite')
c = conn.cursor()
rows = c.execute('SELECT id, nome, python_code FROM pdf_parser_templates').fetchall()
for r in rows:
    print(f"ID={r[0]} NOME={r[1]}")
    print(f"BODY:\n{r[2]}")
    print("---------------------------------")
