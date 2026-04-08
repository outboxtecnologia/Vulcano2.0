out = open('search_out_3.txt', 'w', encoding='utf-8')
with open('main.py', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'detalhes' in line:
            out.write(f"{i}: {line.strip()}\n")
out.close()
