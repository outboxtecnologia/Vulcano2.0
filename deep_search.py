import os
import glob
import re

search_dirs = [
    r'c:\Users\dirfe\.gemini\antigravity',
    r'c:\Users\dirfe\AppData\Local',
    r'c:\Users\dirfe\AppData\Roaming'
]

TARGET = b'<label className="text-[10px] uppercase font-bold text-[#888]">Importador Flex</label>'
# Or broadly:
TARGET2 = b"IMPORTA"

def s():
    for d in [r'c:\Users\dirfe\.gemini\antigravity']:
        for root, dirs, files in os.walk(d):
            # Skip heavy caches
            if '.venv' in root or 'node_modules' in root: continue
            
            for f in files:
                if f.endswith('.txt') or f.endswith('.json') or f.endswith('.jsx') or f.endswith('.md'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'rb') as file:
                            content = file.read()
                            if b'get_receitas_caixa' in content and b'loadingReceitas' in content:
                                print(f"MATCH (recent App.jsx): {path}")
                            if b'Conversor XML' in content and b'venda' in content.lower():
                                print(f"MATCH (recent VulcanoViews.jsx): {path}")
                    except Exception:
                        pass
    print("Search done.")
s()
