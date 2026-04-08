with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
in_ep = False
with open('contas_ep_utf8.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        if '@app.get("/api/questor/contas")' in line:
            in_ep = True
        if in_ep:
            out.write(line)
            if line.startswith('@app') and i > 0 and 'contas' not in line:
                in_ep = False
