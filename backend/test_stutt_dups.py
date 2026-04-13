import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.services.revenue_time_pipeline import get_receitas_caixa

def test():
    stutt_emp_id = 335
    receitas_meta, _, _ = get_receitas_caixa(959, '2025-01-01', '2025-01-31', [stutt_emp_id])
    
    stutt = list(receitas_meta.values())[0]
    unidades = stutt.get("unidades", [])
    
    uni_count = len(unidades)
    unique_unis = len(set([u["unidade"] for u in unidades]))
    
    print(f"Total unidades ativas: {uni_count}")
    print(f"Distinct unidades ativas: {unique_unis}")
    
    if uni_count != unique_unis:
        from collections import Counter
        c = Counter([u["unidade"] for u in unidades])
        for k,v in c.items():
            if v > 1:
                print(f"Duplicate: {k} ({v} times)")

if __name__ == "__main__":
    test()
