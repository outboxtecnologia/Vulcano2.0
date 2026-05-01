from bs4 import BeautifulSoup
import re

def style_to_dict(style_str):
    if not style_str.strip(): return "{}"
    parts = style_str.split(';')
    result = {}
    for p in parts:
        if ':' not in p: continue
        k, v = p.split(':', 1)
        k = k.strip()
        v = v.strip().replace('"', "'")
        parts_k = k.split('-')
        k_camel = parts_k[0] + ''.join(word.title() for word in parts_k[1:])
        if k_camel == "float": k_camel = "cssFloat"
        result[k_camel] = v
    items = []
    for k, v in result.items():
        if v.replace('.', '', 1).isdigit() and k not in ('fontWeight', 'zIndex'):
            items.append(f"{k}: '{v}'") # React expects strings for pixels anyway, safer to just use strings
        else:
            items.append(f"{k}: '{v}'")
    return "{{ " + ", ".join(items) + " }}"

def process_node(node):
    if isinstance(node, str):
        return node.replace('{', '{{').replace('}', '}}')
    
    tag = node.name
    attrs = []
    for k, v in node.attrs.items():
        if k == 'class':
            attrs.append(f'className="{" ".join(v)}"')
        elif k == 'style':
            attrs.append(f'style={style_to_dict(v)}')
        elif k == 'for':
            attrs.append(f'htmlFor="{v}"')
        else:
            if isinstance(v, list):
                v = " ".join(v)
            attrs.append(f'{k}="{v}"')
            
    attrs_str = " " + " ".join(attrs) if attrs else ""
    
    if tag in ['img', 'input', 'br', 'hr']:
        return f"<{tag}{attrs_str} />"
    
    children_html = "".join(process_node(c) for c in node.children)
    return f"<{tag}{attrs_str}>{children_html}</{tag}>"

with open('tributos_review_structure.html', 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')

main_container = soup.find('div', style=lambda s: s and 'flex: 1 1 0%' in s and 'flex-direction: column' in s)

if main_container:
    jsx = process_node(main_container)
    with open('tributos_jsx.txt', 'w', encoding='utf-8') as f:
        f.write(jsx)
    print("JSX generated successfully.")
else:
    print("Could not find main container")
