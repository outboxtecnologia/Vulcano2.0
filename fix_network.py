import os

def fix_network(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    
    text = text.replace('http://localhost:', 'http://127.0.0.1:')
    text = text.replace('https://localhost:', 'https://127.0.0.1:')
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

fix_network(r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\App.jsx")
fix_network(r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx")

print("Network fixed to 127.0.0.1")
