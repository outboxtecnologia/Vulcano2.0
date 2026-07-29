import os
import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# ----------------- PHASE 2: OrphansReconciliationService -----------------
# First, extract find_multimatch
start_multi = text.find('def find_multimatch(')
match_multi = re.search(r'\n(?:    @|    def )', text[start_multi+1:]) # it's inside another function?
# Wait! Let's just find the end of api_concilia_orfaos
start_api = text.find('class OrfaoItem(BaseModel):')
match_api = re.search(r'\n(?:@app|class |def )', text[text.find('def api_concilia_orfaos(')+1:])
end_api = text.find('def api_concilia_orfaos(') + 1 + match_api.start()
func_code = text[start_api:end_api]

with open('backend/core/services/heuristic_optimizer.py', 'w', encoding='utf-8') as f:
    f.write('from pydantic import BaseModel\nfrom typing import List, Dict, Any\nimport re\nimport math\nfrom itertools import combinations\nfrom collections import defaultdict\n\nclass OrphansReconciliationService:\n')
    
    # We remove @app.post from func_code
    func_code = func_code.replace('@app.post("/api/auditoria/concilia-orfaos")\n', '')
    
    # Add injection
    inject = '\n        from backend.main import SplinkMatcher, use_pgvector, get_conn, perform_splink_match\n'
    func_code = func_code.replace('async def api_concilia_orfaos(data: ConciliaOrfaosInput):', 'async def api_concilia_orfaos(data: "OrphansReconciliationService.ConciliaOrfaosInput"):' + inject)
    func_code = func_code.replace('async def api_concilia_orfaos(data: OrphansReconciliationService.ConciliaOrfaosInput):', 'async def api_concilia_orfaos(data: "OrphansReconciliationService.ConciliaOrfaosInput"):' + inject)
    
    cf = func_code.split('\n')
    cf = ['    ' + line if line else line for line in cf]
    f.write('\n'.join(cf))

mock = '''from core.services.heuristic_optimizer import OrphansReconciliationService

@app.post("/api/auditoria/concilia-orfaos")
async def api_concilia_orfaos(data: OrphansReconciliationService.ConciliaOrfaosInput):
    return await OrphansReconciliationService.api_concilia_orfaos(data)'''

# Replace from OrfaoItem to end_api
new_text = text[:start_api] + mock + text[end_api:]

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(new_text)

