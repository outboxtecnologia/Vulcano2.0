import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

def clean_dupes():
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        # Firebird syntax for difference in days: DATEDIFF(day, d1, d2)
        # We find projected rows (m) that have a counterpart legacy row (p)
        query = """
        SELECT m.ID, m.IDVENDA, m.DATA, m.VALORPARCELA, p.DATA, p.ID
        FROM RECEBER m
        JOIN RECEBER p ON m.IDVENDA = p.IDVENDA 
               AND m.VALORPARCELA = p.VALORPARCELA
               AND p.ID <> m.ID
               AND p.OBS IS DISTINCT FROM 'MIGRACAO PROJETADA'
               AND ABS(DATEDIFF(day, m.DATA, p.DATA)) <= 35
        WHERE m.OBS = 'MIGRACAO PROJETADA' AND m.TOTALPAGO <= 0
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        # Deduplicate IDs to delete just in case multiple legacy rows match
        ids_to_del = set()
        for row in rows:
            ids_to_del.add(row[0])
            
        print(f"Encontradas {len(ids_to_del)} parcelas duplicadas (MIGRACAO PROJETADA) próximas a parcelas já existentes.")
        
        if len(ids_to_del) > 0:
            print("Desativando trigger mestre...")
            cur.execute("ALTER TRIGGER RECEBER_BLOQUEIO_BIUD10 INACTIVE")
            
            q_del = "DELETE FROM RECEBER WHERE ID = ?"
            deleted = 0
            for m_id in ids_to_del:
                cur.execute(q_del, (m_id,))
                deleted += 1
                
            print(f"Excluindo {deleted} parcelas aberrantes.")
            
            print("Reativando trigger mestre...")
            cur.execute("ALTER TRIGGER RECEBER_BLOQUEIO_BIUD10 ACTIVE")
            conn.commit()
        
        conn.close()
        print(f"Sucesso! Limpeza finalizada.")

    except Exception as e:
        print(f"Erro ao limpar: {e}")

if __name__ == "__main__":
    clean_dupes()
