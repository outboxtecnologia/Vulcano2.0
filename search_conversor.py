import os

def find_conversor():
    base = r'C:\Users\dirfe\.gemini\antigravity\scratch'
    for root, dirs, files in os.walk(base):
        for file in files:
            if file.endswith('.jsx') or file.endswith('.tsx') or file.endswith('.txt'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text = f.read()
                        if 'Conversor XML' in text or 'IMPORTAÇÃO (Questor)' in text or 'Extrator IA' in text:
                            print(f"FOUND MATCH IN: {filepath}")
                except Exception:
                    pass

find_conversor()
print("Search complete.")
