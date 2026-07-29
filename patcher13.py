import os

with open('backend/core/services/graph_logic_builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('class DiagnosticoRow')
if start_idx != -1:
    classes_code = text[start_idx:]
    text = text[:start_idx]
    with open('backend/core/services/graph_logic_builder.py', 'w', encoding='utf-8') as f:
        f.write('from pydantic import BaseModel\n' + text)
    
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        main_text = f.read()
    
    lines = classes_code.split('\n')
    unindented_lines = [l[4:] if l.startswith('    ') else l for l in lines]
    classes_code = '\n'.join(unindented_lines)

    main_text = main_text.replace('@app.post("/api/auditoria/diagnostico")', classes_code + '\n@app.post("/api/auditoria/diagnostico")')
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(main_text)
