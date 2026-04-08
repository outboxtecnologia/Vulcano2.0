import urllib.request
import json
import traceback

try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/receitas-caixa?empresa_id=959", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = response.read().decode('utf-8')
        result = json.loads(data)
        
        leonardo = [u for u in result.get("dashboard_data", []) if "LEONARDO" in str(u.get("comprador", "")).upper()]
        print(f"Server returned {len(leonardo)} records for Leonardo.")
        for r in leonardo:
            print("ID_Venda?", r.get("id_venda", "MISSING"))
            print("VGV:", r.get("vgv"))
            print("Receita Caixa:", r.get("receita_caixa"))
            print("Societaria:", r.get("receita_societaria"))
            
except Exception as e:
    print("Exception:", e)
    traceback.print_exc()
