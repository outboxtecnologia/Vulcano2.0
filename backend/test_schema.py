import sqlite3
c = sqlite3.connect('poc_database.sqlite')
print(c.execute("SELECT sql FROM sqlite_master WHERE name='VENDA'").fetchone()[0])
