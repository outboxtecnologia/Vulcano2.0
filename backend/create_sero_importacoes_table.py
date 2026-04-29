import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "poc_database.sqlite")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# id (PK)
# empresa_id (INT)
# competencia (TEXT)
# cnpj_cpf (TEXT)
# origem (TEXT)
# valor_original (REAL)
# taxa_correcao (REAL)
# valor_atualizado (REAL)

cursor.execute('''
CREATE TABLE IF NOT EXISTS SERO_IMPORTACOES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    competencia TEXT,
    cnpj_cpf TEXT,
    origem TEXT,
    valor_original REAL,
    taxa_correcao REAL,
    valor_atualizado REAL
)
''')

conn.commit()
conn.close()

print("Table SERO_IMPORTACOES created successfully.")
