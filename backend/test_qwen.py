import urllib.request, json, sqlite3

conn = sqlite3.connect('poc_database.sqlite')
row = conn.execute('SELECT python_code FROM pdf_parser_templates ORDER BY id DESC LIMIT 1').fetchone()[0]

text_content = """COMPRADOR             DATA COMPRA  PARCELA   VALOR      TOTAL PAGO
----------------------------------------------------------------------------------
JAIRTON RODRIGUES     14/11/2022   001/01    2.259,42   2.276,05
MARIA CLARA SOARES    15/11/2022   002/05      300,00     300,00"""

prompt = f"""Você extrai dicionários financeiros de relatórios em PDF com inteligência.
Retorne APENAS um JSON válido seguindo a chave "recebimentos" contendo a lista.

[MANUAL DE EXTRAÇÃO DA EMPRESA ATUAL (OBRIGO VOCÊ A SEGUIR AS REGRAS ABAIXO!)]
{row}

[DADOS TEXTUAIS DO PDF MODO LAYOUT PARA LEITURA]
{text_content}"""

print("Running...")

url = 'http://localhost:11434/api/generate'
data = json.dumps({'model': 'qwen2.5:14b', 'prompt': prompt, 'format': 'json', 'options': {'temperature': 0.0, 'num_ctx': 4096}, 'stream': False}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        res = json.loads(resp.read().decode('utf-8')).get('response')
        with open('qwen_out.json', 'w', encoding='utf-8') as f:
            f.write(res)
        print("Done! View qwen_out.json")
except Exception as e:
    print('ERROR:', e)
