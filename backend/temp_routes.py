lines=open('main.py', encoding='utf-8').readlines()
funcs = []
for i, l in enumerate(lines):
    if '@app.' in l:
        funcs.append(str(i+1) + ': ' + l.strip())
open('temp_routes.txt', 'w', encoding='utf-8').write('\n'.join(funcs))
