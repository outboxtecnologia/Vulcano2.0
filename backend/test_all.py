import sys
import traceback
sys.path.append('backend')

try:
    from main import get_receitas_caixa
    for i in range(1, 6):
        print(f"Testing Empresa {i}...")
        try:
            res = get_receitas_caixa(empresa_id=i)
            print(f"Success! Empresa {i} has {len(res['dashboard_meta'])} projects.")
        except Exception as e:
            print(f"CRASH on Empresa {i}:", e)
            traceback.print_exc()
except Exception as e:
    print("CRASHED IMPORTS:", e)
