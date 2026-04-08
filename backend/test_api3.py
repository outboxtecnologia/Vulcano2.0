import sys
import traceback
sys.path.append('backend')

try:
    from main import get_receitas_caixa
    print("Calling function directly...")
    res = get_receitas_caixa(empresa_id=1)
    print("Success! Keys:", getattr(res, "keys", lambda: "Not a dict")())
except Exception as e:
    print("CRASHED:", e)
    traceback.print_exc()
