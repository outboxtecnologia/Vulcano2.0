import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import get_receitas_caixa

def run():
    resp = get_receitas_caixa(empresa_id=959, data_fim="2025-06-30")
    
    dashboard_meta = resp.get("dashboard_meta", {})
    if not dashboard_meta:
        print("No dashboard meta returned.")
        return
        
    for k, v in dashboard_meta.items():
        print(f"Empreendimento: {k}")
        for u in v.get("unidades", []):
            print(f"  Unidade: {u['unidade']} - VGV: {u['vgv']} - CAIXA_MES: {u['caixa_mes']}")

if __name__ == "__main__":
    run()
