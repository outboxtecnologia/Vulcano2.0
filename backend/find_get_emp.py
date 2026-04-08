with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
in_ep = False
with open('get_emp.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        if 'def get_vulcano_empreendimentos' in line or '@app.get("/api/vulcano/empreendimentos")' in line:
            in_ep = True
        if in_ep:
            out.write(f'{i+1}: {line}')
            if line.startswith('@app') and i > 0 and 'empreendimentos' not in line:
                in_ep = False
                break
