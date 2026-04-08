with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('out_ep_utf8.txt', 'w', encoding='utf-8') as out:
    in_get = False
    in_post = False

    for i, line in enumerate(lines):
        if '@app.get("/api/vulcano/empreendimentos")' in line:
            in_get = True
            out.write('--- GET EMPREENDIMENTOS ---\n')
        if '@app.post("/api/vulcano/empreendimentos")' in line:
            in_post = True
            out.write('--- POST EMPREENDIMENTOS ---\n')
            
        if in_get or in_post:
            out.write(line)
            if line.startswith('@app') and i > 0 and 'empreendimentos' not in line:
                in_get = False
                in_post = False
                out.write('--- END ---\n')
