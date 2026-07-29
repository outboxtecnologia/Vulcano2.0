import os

with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, l in enumerate(lines):
    if l.startswith('@app.post("/api/auditoria/concilia-orfaos")'):
        if start_idx == -1 or "def api_concilia_orfaos" in lines[i+1]:
            # This is the actual endpoint, wait:
            if "def api_concilia_orfaos(data: ConciliaOrfaosInput):" in lines[i+1]:
                start_idx = i
    if l.startswith('@app.post("/api/auditoria/diagnostico")'):
        end_idx = i

if start_idx != -1 and end_idx != -1:
    print(f"Start: {start_idx}, End: {end_idx}")
    
    # Export it
    func_code = ''.join(lines[start_idx+1:end_idx]) # skip @app.post decorator
    func_code = func_code.replace('async def api_concilia_orfaos', 'def api_concilia_orfaos')
    
    with open('backend/core/services/heuristic_optimizer.py', 'a', encoding='utf-8') as f:
        # indent func code
        cf = func_code.split('\n')
        cf = ['    ' + line if line else line for line in cf]
        f.write('\n    @staticmethod\n' + '\n'.join(cf))

    # Remove it from main.py except the mock
    new_main = lines[:start_idx-1] + [
        '\n# Endpoint mapped via OrphansReconciliationService in heuristic_optimizer.py\n',
        '@app.post("/api/auditoria/concilia-orfaos")\n',
        'async def api_concilia_orfaos(data: OrphansReconciliationService.ConciliaOrfaosInput):\n',
        '    return OrphansReconciliationService.api_concilia_orfaos(data)\n\n'
    ] + lines[end_idx:]

    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.writelines(new_main)
