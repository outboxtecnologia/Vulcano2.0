import os
import sys

# Add backend dir to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

def run_migration():
    print("Iniciando Migração de Projeções (VENDAFORMAPAGTOPRAZO -> RECEBER)...")
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        # 1. Achar todos os prazos (VENDAFORMAPAGTOPRAZO) que não correspondem a nenhuma parcela em RECEBER com a mesma DATA e mesmo CONTRATO.
        # Nós pegamos IDVENDAFORMAPAGTOPRAZO via left join. Se o banco velho nao tinha o id populado, batemos por (DATA e IDVENDA).
        
        query_prazos = """
            SELECT p.ID AS PRAZO_ID, p.IDVENDAFORMAPAGTO, p.DATA, p.VALOR, p.REFERENCIA, f.IDVENDA, v.ID_CLIENTE
            FROM VENDAFORMAPAGTOPRAZO p
            JOIN VENDAFORMAPAGTO f ON p.IDVENDAFORMAPAGTO = f.ID
            JOIN VENDA v ON f.IDVENDA = v.ID
        """
        cur.execute(query_prazos)
        todos_prazos = cur.fetchall()
        
        print(f"Encontrados {len(todos_prazos)} prazos projetados na matriz de condições.")
        
        cur.execute("SELECT IDVENDA, DATA, VALORPARCELA, ID, TOTALPAGO FROM RECEBER")
        # Criar lookup rápido para os recebimentos existentes. Em firebird 'DATA' é string ou date dependendo, compararemos YYYY-MM
        receber_hash = {}
        for row in cur.fetchall():
            idv = row[0]
            dt = str(row[1])[:7] if row[1] else ""  # YYYY-MM
            vp = float(row[2]) if row[2] else 0.0
            
            key = f"{idv}_{dt}_{int(vp)}"
            receber_hash[key] = row[3] # id 
            key_no_val = f"{idv}_{dt}"
            if key_no_val not in receber_hash:
                receber_hash[key_no_val] = row[3]

        cur.execute("SELECT COALESCE(MAX(ID), 0) FROM RECEBER")
        current_max_id = cur.fetchone()[0]

        novos_inserts = 0
        for prazo in todos_prazos:
            prazo_id, fp_id, dt_val, vl, ref, idvenda, idclient = prazo
            
            dt_str = str(dt_val)[:7] if dt_val else ""
            vl_f = float(vl) if vl else 0.0
            
            key_strict = f"{idvenda}_{dt_str}_{int(vl_f)}"
            key_loose = f"{idvenda}_{dt_str}"
            
            if key_strict in receber_hash or key_loose in receber_hash:
                # Já existe uma parcela no RECEBER para esta Venda, neste Mês. Abortar injeção duplicada.
                continue
                
            # Se não existe, vamos INJETAR a projeção na tabela RECEBER!
            current_max_id += 1
            rec_id = current_max_id
            
            q_rec = """
                INSERT INTO RECEBER (ID, IDVENDA, IDCLIENTE, DATA, VALORPARCELA, PARCELA, OBS, IDVENDAFORMAPAGTO, IDVENDAFORMAPAGTOPRAZO, TOTALPAGO)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Para evitar erros de tipagem com data nula ou timestamp longos (SQL Error -303)
            dt_real = str(dt_val)[:10] if dt_val else None
            
            cur.execute(q_rec, (rec_id, idvenda, idclient, dt_real, vl_f, ref, "MIGRACAO PROJETADA", fp_id, prazo_id, 0.0))
            novos_inserts += 1

            # Update the in-memory cache to prevent multiple prazos in the same month from duplicate bypass
            receber_hash[key_strict] = rec_id
            receber_hash[key_loose] = rec_id
            
        conn.commit()
        conn.close()
        print(f"Sucesso! {novos_inserts} parcelas projetadas foram materializadas na tabela RECEBER.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Erro:", str(e))

if __name__ == "__main__":
    run_migration()
