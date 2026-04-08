import sqlite3
import json
import urllib.request

conn = sqlite3.connect('poc_database.sqlite')
prompt_manifesto = conn.cursor().execute('SELECT python_code FROM pdf_parser_templates ORDER BY id DESC LIMIT 1').fetchone()[0]
conn.close()

prompt = f"""Você extrai dicionários financeiros de relatórios em PDF com inteligência.
Retorne APENAS um JSON válido seguindo a chave "recebimentos" contendo a lista.

[MANUAL DE EXTRAÇÃO DA EMPRESA ATUAL (OBRIGO VOCÊ A SEGUIR AS REGRAS ABAIXO!)]
{prompt_manifesto}

[DADOS TEXTUAIS DO PDF MODO LAYOUT PARA LEITURA]
14/11/2022  05/12/2022   04/11/2022      001/01    11/11/2022   2.259,42   0,00   0,00   2.259,42     16,63      2.276,05 JAIRTON
"""

url = 'http://localhost:11434/api/generate'
data = json.dumps({'model': 'qwen2.5:14b', 'prompt': prompt, 'format': 'json', 'stream': False}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = resp.read().decode('utf-8')
        raw_text = json.loads(res).get('response', '')
        print("RAW RESPONSE FROM QWEN:\n", raw_text)
except Exception as e:
    print('Error:', e)
