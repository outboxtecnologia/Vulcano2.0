import re

with open('refatorar_motor3.py', 'r', encoding='utf-8') as f:
    text = f.read()
    
match = re.search(r"new_logic = r'''(.*?)'''", text, re.DOTALL)
if match:
    new_logic = match.group(1)
    
    with open('main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if 'Pesquisa Rápida em RAM (In-Memory Filter)' in line:
            start_idx = i
        if 'return {"resultados": results}' in line and start_idx != -1 and end_idx == -1:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        new_lines = lines[:start_idx] + [new_logic + '\n'] + lines[end_idx:]
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print('SUCCESS: INJECTED SAFELY')
    else:
        print('FAILED: indices', start_idx, end_idx)
else:
    print('FAILED: regex')
