import os
from bs4 import BeautifulSoup

def analyze_html(filepath):
    print(f"--- {filepath} ---")
    if not os.path.exists(filepath):
        print("Not found")
        return
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get all unique CSS classes to see styling approaches (e.g. Tailwind)
    classes = set()
    for tag in soup.find_all(True):
        if tag.get('class'):
            classes.update(tag.get('class'))
            
    print("Top 50 Classes:")
    print(list(classes)[:50])
    print("\nText Content (first 1000 chars):")
    print(soup.get_text(separator=' ', strip=True)[:1000])
    print("\nStructure (main tags with classes):")
    for t in soup.find_all(['h1', 'h2', 'h3', 'button']):
        print(f"{t.name}: {' '.join(t.get('class', []))} -> {t.get_text()[:30]}")

analyze_html("designs/vendas/5b7ed6c0-115e-46da-a56f-7e98ab7532ec")
analyze_html("designs/Vulcano Vendas (1).html")
