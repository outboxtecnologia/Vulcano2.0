import urllib.request, json
req = urllib.request.Request(
    'http://127.0.0.1:8002/api/parser/save',
    method='POST',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'nome': 'Test',
        'descricao': '',
        'chat_history': [],
        'final_data': [{'comprador': 'A', 'data': '01/01/2021', 'parcela': '1/1', 'valor_parcela': 100.0, 'total_pago': 100.0, 'desconto': 0.0, 'acrescimo': 0.0}],
        'empresa_id': 1,
        'definir_padrao_empresa': True
    }).encode('utf-8')
)
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode())
