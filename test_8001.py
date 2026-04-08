import urllib.request
import json
import subprocess
import time

try:
    # Start temporary uvicorn
    proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8001"], cwd="backend")
    print("Started uvicorn on 8001")
    time.sleep(3) # Wait for startup
    
    req = urllib.request.Request("http://127.0.0.1:8001/api/receitas-caixa?empresa_id=959", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = response.read().decode('utf-8')
        result = json.loads(data)
        
        leonardo = [u for u in result.get("dashboard_data", []) if "LEONARDO" in str(u.get("comprador", "")).upper()]
        for r in leonardo:
            print(f"VGV: {r.get('vgv')} Caixa: {r.get('receita_caixa')}")
            
    proc.kill()
except Exception as e:
    print("Exception:", e)
    try:
        proc.kill()
    except:
        pass
