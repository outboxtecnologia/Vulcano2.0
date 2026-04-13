import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.services.graph_logic_builder import AccountingGraphPipeline

def test():
    res_dict = AccountingGraphPipeline.api_contabilizacoes(2025, 1, 959)
    res_list = res_dict.get("data", [])
    
    stutt = None
    for emp in res_list:
        n = emp.get("empreendimento", "")
        if "STUTTGART" in n.upper() or "STTUTGART" in n.upper():
            stutt = emp
            break

    if stutt:
        for c in stutt.get("contas_virtuais", []):
            if c["conta"] == 5639 or "ESTOQUE" in c.get("nome", "").upper() or "CONCLU" in c.get("nome", "").upper():
                print(f"CONTA 5639 Saldo Anterior: {c['saldo_anterior']}")
                print(f"CONTA 5639 Movimento Disp: {c['movimento_liquido']}")
                break

if __name__ == "__main__":
    test()
