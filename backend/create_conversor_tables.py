import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "poc_database.sqlite")

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela Mãe / Batches
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversor_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        import_mode TEXT,
        raw_pdf_text TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela Filha / Dados Mapeados
    # dt_vencimento e dt_pagamento num formato DATE (ISO string no sqlite)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversor_data_staging (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER NOT NULL,
        comprador TEXT,
        cpf_cnpj TEXT,
        empreendimento TEXT,
        unidade TEXT,
        dt_vencimento DATE,
        dt_pagamento DATE,
        parcela TEXT,
        valor_raiz REAL,
        descontos REAL,
        acrescimos_variacoes REAL,
        total_pago REAL,
        FOREIGN KEY(batch_id) REFERENCES conversor_batches(id) ON DELETE CASCADE
    )
    ''')
    
    # Create indexes for quick viewing by batch
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch ON conversor_data_staging(batch_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_empreend ON conversor_data_staging(empreendimento)')
    
    conn.commit()
    conn.close()
    
    print("Sucesso! Tabelas conversor_batches e conversor_data_staging estruturadas no SQLite.")

if __name__ == "__main__":
    create_tables()
