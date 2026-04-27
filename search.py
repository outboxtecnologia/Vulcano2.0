with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

for i, line in enumerate(lines):
    if 'r_meta.get("unidades"' in line:
        print(f'Line {i}')
        for j in range(i, i+30):
            print(f'{j}: {lines[j].strip()}')
        break
