import os, sys, traceback, json
sys.path.append(r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend')
from dotenv import load_dotenv
load_dotenv(os.path.join(sys.path[-1], '.env'))
import main

try:
    res = main._gemini_generate_json('Retorne um JSON com a chave "status" e o valor "OK"')
    with open('error_out.txt', 'w', encoding='utf-8') as f:
        f.write('SUCCESS: ' + json.dumps(res))
except Exception as e:
    with open('error_out.txt', 'w', encoding='utf-8') as f:
        f.write('ERROR: ' + str(e))
