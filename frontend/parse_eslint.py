import json
try:
    with open('eslint-results.json', 'r', encoding='utf-16le') as f:
        data = json.load(f)
except:
    with open('eslint-results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

for file in data:
    for msg in file.get('messages', []):
        if msg.get('severity') == 2:
            print(f"{file['filePath']}:{msg['line']}:{msg['column']} - {msg['message']}")
