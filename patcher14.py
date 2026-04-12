import os

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = 1218
end_idx = 1554 # wait, let's just find the exact endpoint end dynamically

for i in range(start_idx, len(lines)):
    if lines[i].startswith('@app'):
        # next endpoint
        end_idx = i
        break

classes_code = ''.join(lines[start_idx:end_idx])

with open('backend/core/services/heuristic_optimizer.py', 'w', encoding='utf-8') as f:
    f.write('from pydantic import BaseModel\n')
    f.write('from typing import List, Dict, Any\n')
    f.write('from collections import defaultdict\n')
    f.write('import re\nimport math\nfrom itertools import combinations\n\n')
    f.write('class OrphansReconciliationService:\n')
    
    # We replace @app.post with @staticmethod
    classes_code = classes_code.replace('@app.post("/api/auditoria/concilia-orfaos")', '@staticmethod')
    classes_code = classes_code.replace('async def api_concilia_orfaos', 'def api_concilia_orfaos')
    
    # Indent everything
    cf = classes_code.split('\n')
    cf = ['    ' + line if line else line for line in cf]
    f.write('\n'.join(cf))

new_main = lines[:start_idx] + [
    '\n# DECOUPLED: OrphansReconciliationService -> heuristic_optimizer\n',
    'from core.services.heuristic_optimizer import OrphansReconciliationService, OrfaoItem, ConciliaOrfaosInput\n\n',
    '@app.post("/api/auditoria/concilia-orfaos")\n',
    'async def api_concilia_orfaos(data: ConciliaOrfaosInput):\n',
    '    return OrphansReconciliationService.api_concilia_orfaos(data)\n\n'
] + lines[end_idx:]

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_main)
