import sys
sys.path.insert(0, 'backend')

import asyncio
from main import app
from core.services.graph_logic_builder import build_accounting_graph
from core.services.questor_injector import inject_batch_to_questor
from main import get_conn

async def run_test():
    print("Obtendo dados...")
    res_list = build_accounting_graph("2025", "2025-04", "959", "335")
    
    flat_entries = []
    has_ret_distrato = False
    
    for proj in res_list:
        if proj.get("empreendimento_id") != 335:
            continue
            
        for cv in proj.get("contas_virtuais", []):
            conta = cv.get("conta")
            if not conta or conta == 99999: # Ignora saldenhos
                continue
            
            for detalhe in cv.get("detalhes", []):
                if detalhe.get("virtual"):
                    flat_entries.append({
                        "conta": conta,
                        "mov": detalhe.get("valor", detalhe.get("mov", 0.0)),
                        "nat": detalhe.get("natureza", detalhe.get("nat", "D")),
                        "historico": detalhe.get("historico", "")
                    })
                    if "ret distrato" in str(detalhe.get("historico")).lower():
                        has_ret_distrato = True
                        
    print(f"Buscadas {len(flat_entries)} linhas para Stuttgart (CC 35)")
    if has_ret_distrato:
        print("-> Confirmed: Distrato entries exist!")
        
    print("Injetando...")
    res = inject_batch_to_questor(959, "2025-04", flat_entries)
    print("Injector resp:", res)
    
if __name__ == "__main__":
    asyncio.run(run_test())
