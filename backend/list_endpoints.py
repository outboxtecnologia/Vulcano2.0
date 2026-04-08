with open('main.py', encoding='utf-8') as f:
    lines = f.readlines()
endpoints = [line.strip() for line in lines if '@app.get(' in line or '@app.post(' in line]
with open('endpoints.txt', 'w', encoding='utf-8') as f:
    f.write('\\n'.join(endpoints))
