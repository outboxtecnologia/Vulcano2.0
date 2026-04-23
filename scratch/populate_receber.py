import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend")
import main

def populate_receber_fast():
    conn = main.get_conn('vulcano')
    cur = conn.cursor()
    
    print("Buscando IDs já efetivados na RECEBER...")
    cur.execute("SELECT IDVENDAFORMAPAGTOPRAZO FROM RECEBER WHERE IDVENDAFORMAPAGTOPRAZO IS NOT NULL")
    efetivados = set([r[0] for r in cur.fetchall()])
    print(f"Total efetivados na RECEBER: {len(efetivados)}")
    
    print("Buscando parcelas projetadas...")
    cur.execute("""
        SELECT 
            p.ID AS prazo_id,
            p.DATA AS data_venc,
            p.VALOR AS valor,
            p.REFERENCIA AS parcela_ref,
            f.ID AS forma_pagto_id,
            f.IDVENDA AS venda_id,
            v.ID_CLIENTE AS cliente_id
        FROM VENDAFORMAPAGTOPRAZO p
        JOIN VENDAFORMAPAGTO f ON f.ID = p.IDVENDAFORMAPAGTO
        JOIN VENDA v ON v.ID = f.IDVENDA
    """)
    projetadas = cur.fetchall()
    print(f"Total projetadas: {len(projetadas)}")
    
    pendentes = [p for p in projetadas if p[0] not in efetivados]
    print(f"Parcelas abertas (pendentes de inserção): {len(pendentes)}")
    
    if not pendentes:
        conn.close()
        return

    cur.execute("SELECT COALESCE(MAX(ID), 0) FROM RECEBER")
    novos_id = cur.fetchone()[0] + 1
    
    inseridos = 0
    print("Inserindo parcelas pendentes na RECEBER...")
    for p in pendentes:
        prazo_id, data_venc, valor, parcela_ref, forma_pagto_id, venda_id, cliente_id = p
        
        cur.execute("""
            INSERT INTO RECEBER (
                ID, IDVENDA, IDCLIENTE, DATA, VALORPARCELA, 
                VALORVARIACAO, TOTALPAGO, PARCELA, OBS, 
                IDVENDAFORMAPAGTO, DESCONTO, IDVENDAFORMAPAGTOPRAZO
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            novos_id, venda_id, cliente_id, data_venc, float(valor or 0), 
            0.0, 0.0, parcela_ref, "Gerado via Motor Vulcano 2.0 (Aberto)", 
            forma_pagto_id, 0.0, prazo_id
        ))
        novos_id += 1
        inseridos += 1
        if inseridos % 5000 == 0:
            conn.commit()
            print(f"{inseridos} inseridas...")
            
    conn.commit()
    print(f"Sucesso! {inseridos} parcelas abertas foram inseridas na RECEBER.")
    conn.close()

if __name__ == "__main__":
    populate_receber_fast()
