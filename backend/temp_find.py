lines=open('main.py', encoding='utf-8').readlines()
funcs = []
for i, l in enumerate(lines):
    if '@app.post' in l or 'sync' in l.lower() or 'tributos' in l.lower() or 'imposto' in l.lower():
        funcs.append(str(i+1) + ': ' + l.strip())
open('temp_find.txt', 'w', encoding='utf-8').write('\n'.join(funcs))
