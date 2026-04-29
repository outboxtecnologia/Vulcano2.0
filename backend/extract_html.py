import re
import json

try:
    with open('designs/Vulcano Vendas (1).html', 'r', encoding='utf-8') as f:
        content = f.read()

    # The HTML usually has a script tag with bundled data or just large HTML
    print("Length of content:", len(content))
    
    # Try to find common bundled structures
    match = re.search(r'window\.__data\s*=\s*({.*?});', content, re.DOTALL)
    if match:
        print("Found window.__data")
    else:
        # Just extract script tags
        scripts = re.findall(r'<script.*?</script>', content, re.DOTALL)
        print(f"Found {len(scripts)} script tags")
        for i, s in enumerate(scripts):
            print(f"Script {i} length:", len(s))
            if len(s) > 10000:
                with open(f'script_{i}.js', 'w', encoding='utf-8') as out:
                    out.write(s)
                print(f"Saved script {i}")

except Exception as e:
    print(e)
