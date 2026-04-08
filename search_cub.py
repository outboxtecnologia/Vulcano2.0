import os
for root, dirs, files in os.walk(r'c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0'):
    for f in files:
        if f.endswith('.md') or f.endswith('.txt'):
            path = os.path.join(root, f)
            if 'node_modules' in path or '.venv' in path: continue
            try:
                for idx, l in enumerate(open(path, encoding='utf-8', errors='ignore')):
                    if 'cub' in l.lower():
                        print(f"{f}:{idx+1}:{l.strip()}")
            except: pass
