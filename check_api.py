import urllib.request, json
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/questor/contabilizacoes', data=json.dumps({'empresa_id': 959, 'apenas_analiticas': True}).encode('utf-8'), headers={'Content-Type':'application/json'})
    res = urllib.request.urlopen(req).read()
    data = json.loads(res.decode('utf-8'))
    found = False
    for emp in data['data']:
        for acc in emp.get('contas_fisicas', []):
            for det in acc.get('detalhes', []):
                if 'override_apto' in det:
                    print(f'Found override: {det[\"chave\"]} -> {det[\"override_apto\"]}')
                    found = True
    if not found: print('No overrides found in the output!')
except Exception as e:
    print('Error:', e)
