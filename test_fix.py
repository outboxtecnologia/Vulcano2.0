import shutil
import os

shutil.copy('frontend/src/App.jsx', 'frontend/src/App.jsx.bak')

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    fixed = content.encode('cp1252').decode('utf-8')
    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(fixed)
    print("Fixed App.jsx successfully.")
    
    # Let's read the specific line to verify
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for l in lines:
            if 'Janitor SRE' in l:
                print("Line:", l.strip())
except Exception as e:
    print("Error:", e)
