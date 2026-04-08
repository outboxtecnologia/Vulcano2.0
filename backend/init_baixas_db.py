import sqlite3

def init_db():
    conn = sqlite3.connect('poc_database.sqlite')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS operacoes_baixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_receber INTEGER UNIQUE NOT NULL,
            empresa_id INTEGER NOT NULL,
            data_pagamento TEXT NOT NULL,
            valor_pago REAL NOT NULL,
            descontos REAL DEFAULT 0,
            acrescimos REAL DEFAULT 0,
            transacao_referencia TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Table created successfully")

if __name__ == "__main__":
    init_db()
