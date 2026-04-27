import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.db_firebird import get_vulcano_connection

def test():
    conn_v = get_vulcano_connection()
    cur_v = conn_v.cursor()
    
    cur_v.execute("SELECT ID, NOME FROM EMPREENDIMENTO WHERE NOME LIKE '%STTUTGART%'")
    row = cur_v.fetchone()
    if not row: return
    emp_id, nome = row
    
    cur_v.execute("""
        SELECT V.DESCUNIDIMOB, SUM(U.METRAGEM) 
        FROM VENDA V
        JOIN VENDAUNIDADE VU ON VU.IDVENDA = V.ID
        JOIN UNIDADE U ON U.ID = VU.IDUNIDADE
        JOIN BLOCO B ON B.ID = U.IDBLOCO
        WHERE B.IDEMPREENDIMENTO = ?
        GROUP BY V.DESCUNIDIMOB
    """, (emp_id,))
    
    vendas = cur_v.fetchall()
    sold_area = sum(float(r[1] or 0) for r in vendas)
    
    cur_v.execute("SELECT SUM(U.METRAGEM) FROM UNIDADE U JOIN BLOCO B ON B.ID = U.IDBLOCO WHERE B.IDEMPREENDIMENTO = ?", (emp_id,))
    tot_area_row = cur_v.fetchone()
    tot_area = float(tot_area_row[0]) if tot_area_row and tot_area_row[0] else 1.0
    
    print(f"Emp: {nome}")
    print(f"Area Sold (from VENDA): {sold_area}")
    print(f"Total Area (from UNIDADE): {tot_area}")
    print(f"Sum(fracao_fisica): {sold_area / tot_area if tot_area > 0 else 0}")
    print(f"Total vendas count: {len(vendas)}")

test()
