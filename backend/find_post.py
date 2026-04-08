with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('post_emp_utf8.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        if '@app.post("/api/vulcano/empreendimentos")' in line:
            for j in range(i, i+38):
                out.write(f'{j+1}: {lines[j]}')
