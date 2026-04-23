import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend")
import main

def sync_abertas():
    # 1. Busca dados do Firebird (Legado)
    print("Conectando ao Firebird (Legado)...")
    conn_fb = main.get_conn('vulcano')
    cur_fb = conn_fb.cursor()
    
    print("Buscando IDs já efetivados na RECEBER...")
    cur_fb.execute("SELECT IDVENDAFORMAPAGTOPRAZO FROM RECEBER WHERE IDVENDAFORMAPAGTOPRAZO IS NOT NULL")
    efetivados = set([r[0] for r in cur_fb.fetchall()])
    
    print("Buscando parcelas projetadas na VENDAFORMAPAGTOPRAZO...")
    cur_fb.execute("""
        SELECT 
            p.ID AS prazo_id,
            p.DATA AS data_venc,
            p.VALOR AS valor,
            p.REFERENCIA AS parcela_ref,
            f.ID AS forma_pagto_id,
            f.IDVENDA AS venda_id,
            v.ID_CLIENTE AS cliente_id,
            c.NOME AS cliente_nome,
            u.DESCRICAO AS unidade_descricao,
            b.IDEMPREENDIMENTO AS empreendimento_id
        FROM VENDAFORMAPAGTOPRAZO p
        JOIN VENDAFORMAPAGTO f ON f.ID = p.IDVENDAFORMAPAGTO
        JOIN VENDA v ON v.ID = f.IDVENDA
        JOIN CLIENTE c ON c.ID = v.ID_CLIENTE
        LEFT JOIN VENDAUNIDADE vu ON vu.IDVENDA = v.ID
        LEFT JOIN UNIDADE u ON u.ID = vu.IDUNIDADE
        LEFT JOIN BLOCO b ON b.ID = u.IDBLOCO
    """)
    projetadas = cur_fb.fetchall()
    conn_fb.close()
    
    # 2. Filtra as abertas (não efetivadas) e deduplica por prazo_id (devido a múltiplas unidades por venda)
    abertas_dict = {}
    for p in projetadas:
        if p[0] not in efetivados:
            abertas_dict[p[0]] = p
    
    abertas = list(abertas_dict.values())
    print(f"Total de parcelas em aberto calculadas (únicas): {len(abertas)}")
    
    # 3. Salva no SQLite (Vulcano 2.0)
    print("Conectando ao SQLite (Vulcano 2.0)...")
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../backend/poc_database.sqlite")
    conn_sq = sqlite3.connect(db_path)
    cur_sq = conn_sq.cursor()
    
    cur_sq.execute("""
        CREATE TABLE IF NOT EXISTS parcelas_abertas_projetadas (
            prazo_id INTEGER PRIMARY KEY,
            data_venc TEXT,
            valor REAL,
            parcela_ref TEXT,
            forma_pagto_id INTEGER,
            venda_id INTEGER,
            cliente_id INTEGER,
            cliente_nome TEXT,
            unidade_descricao TEXT,
            empreendimento_id INTEGER
        )
    """)
    
    print("Limpando cache anterior...")
    cur_sq.execute("DELETE FROM parcelas_abertas_projetadas")
    
    print("Populando Vulcano 2.0...")
    cur_sq.executemany("""
        INSERT INTO parcelas_abertas_projetadas (
            prazo_id, data_venc, valor, parcela_ref, forma_pagto_id, 
            venda_id, cliente_id, cliente_nome, unidade_descricao, empreendimento_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        p[0], 
        p[1].strftime("%Y-%m-%d") if hasattr(p[1], "strftime") else str(p[1]), 
        float(p[2] or 0), 
        str(p[3] or ""), 
        p[4], p[5], p[6], 
        str(p[7] or ""), 
        str(p[8] or ""), 
        p[9]
    ) for p in abertas])
    
    conn_sq.commit()
    conn_sq.close()
    print("Sincronização concluída com sucesso! Banco do Vulcano 2.0 populado.")

if __name__ == "__main__":
    sync_abertas()
