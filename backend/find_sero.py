with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '@app.get("/api/sero/maodeobra")' in line:
        for j in range(i, i+55):
            print(f'{j+1}: {lines[j]}', end='')
