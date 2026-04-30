from bs4 import BeautifulSoup

with open('rendered_smart_dom.html', 'r', encoding='utf-8') as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')

def process_node(node, level=0):
    if node.name is None:
        text = node.strip()
        if text:
            print("  " * level + f"TEXT: {text}")
        return

    if node.name in ['script', 'style', 'head', 'noscript', 'meta', 'title']:
        return
        
    classes = node.get('class', [])
    class_str = ' '.join(classes) if isinstance(classes, list) else classes
    style = node.get('style', '')
    
    attr_str = ''
    if class_str:
        attr_str += f" class='{class_str}'"
    if style:
        attr_str += f" style='{style}'"
    
    if node.name == 'svg':
        print("  " * level + f"<{node.name}{attr_str}>")
        return

    print("  " * level + f"<{node.name}{attr_str}>")
    
    for child in node.children:
        process_node(child, level + 1)
        
    print("  " * level + f"</{node.name}>")

body = soup.find('body')
if body:
    import sys
    sys.stdout = open('dom_smart.txt', 'w', encoding='utf-8')
    process_node(body)
