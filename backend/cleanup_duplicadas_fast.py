import os
import sys
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import get_conn

def parse_data(d_str):
    if not d_str:
        return None
    d_str = str(d_str)
    # yyyy-mm-dd
    if len(d_str) >= 10:
        try:
            return datetime.datetime.strptime(d_str[:10], "%Y-%m-%d")
        except:
            return None
    return None

def clean_dupes_fast():
    print("Iniciando varredura rápida na memoria para duplicidades...")
    try:
        conn = get_conn("vulcano")
        cur = conn.cursor()
        
        # Puxaremos tudo pertinente (500k é tranquilo na memória do python)
        cur.execute("SELECT ID, IDVENDA, DATA, VALORPARCELA, OBS, TOTALPAGO FROM RECEBER")
        
        # Guardaremos por IDVENDA um array de parcels
        vendas_map = {}
        for row in cur.fetchall():
            rec_id = row[0]
            idvenda = row[1]
            data_val = parse_data(row[2])
            valor = float(row[3]) if row[3] else 0.0
            obs = str(row[4] or "")
            tp = float(row[5]) if row[5] else 0.0
            
            if idvenda not in vendas_map:
                vendas_map[idvenda] = []
                
            vendas_map[idvenda].append({
                "id": rec_id,
                "data": data_val,
                "valor": valor,
                "obs": obs,
                "total_pago": tp
            })
            
        ids_to_del = set()
        
        for idvenda, list_recs in vendas_map.items():
            # Filtra os que são projeções
            projecoes = [x for x in list_recs if x["obs"] == "MIGRACAO PROJETADA" and x["total_pago"] <= 0]
            originais = [x for x in list_recs if x["obs"] != "MIGRACAO PROJETADA"]
            
            for proj in projecoes:
                if not proj["data"]: continue
                # Tem alguma original que seja mesmo valor e a data bata num range de 35 dias?
                for orig in originais:
                    if not orig["data"]: continue
                    if abs(orig["valor"] - proj["valor"]) < 0.1: # valores baterem
                        diff_days = abs((orig["data"] - proj["data"]).days)
                        if diff_days <= 35:
                            # Essa projecao é lixo, o original preenche essa lacuna
                            ids_to_del.add(proj["id"])
                            break
                            
        print(f"Encontradas {len(ids_to_del)} parcelas duplicadas nas projeções!")
        
        if len(ids_to_del) > 0:
            print("Desativando trigger mestre...")
            cur.execute("ALTER TRIGGER RECEBER_BLOQUEIO_BIUD10 INACTIVE")
            conn.commit()
            
            q_del = "DELETE FROM RECEBER WHERE ID = ?"
            deleted = 0
            for m_id in ids_to_del:
                cur.execute(q_del, (m_id,))
                deleted += 1
                
            print(f"Excluindo {deleted} parcelas aberrantes.")
            conn.commit()
            
            print("Reativando trigger mestre...")
            cur.execute("ALTER TRIGGER RECEBER_BLOQUEIO_BIUD10 ACTIVE")
            conn.commit()
            
        conn.close()
        print("Sucesso! Limpeza finalizada.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Erro ao limpar: {e}")

if __name__ == "__main__":
    clean_dupes_fast()
