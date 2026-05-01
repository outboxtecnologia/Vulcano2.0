import re
import json

def style_to_dict(style_str):
    if not style_str.strip(): return "{}"
    parts = style_str.split(';')
    result = {}
    for p in parts:
        if ':' not in p: continue
        k, v = p.split(':', 1)
        k = k.strip()
        v = v.strip().replace('"', "'")
        # camelCase conversion
        parts_k = k.split('-')
        k_camel = parts_k[0] + ''.join(word.title() for word in parts_k[1:])
        if k_camel == "float": k_camel = "cssFloat"
        result[k_camel] = v
    # Format as JSX dict string
    items = []
    for k, v in result.items():
        if v.isdigit():
            items.append(f"{k}: {v}")
        else:
            items.append(f"{k}: '{v}'")
    return "{{ " + ", ".join(items) + " }}"

def html_to_jsx(html):
    # Fix class -> className
    html = re.sub(r'\bclass=', 'className=', html)
    # Fix styles
    def style_replacer(match):
        style_val = match.group(1)
        return f"style={style_to_dict(style_val)}"
    html = re.sub(r'style="([^"]*)"', style_replacer, html)
    # Self-closing tags
    html = re.sub(r'<img([^>]*)(?<!/)>', r'<img\1 />', html)
    html = re.sub(r'<input([^>]*)(?<!/)>', r'<input\1 />', html)
    html = re.sub(r'<br([^>]*)(?<!/)>', r'<br\1 />', html)
    html = re.sub(r'<hr([^>]*)(?<!/)>', r'<hr\1 />', html)
    return html

with open('tributos_review_structure.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract only the main content area
# Looking for `<div style="flex: 1 1 0%; display: flex; flex-direction: column; min-width: 0px;">`
match = re.search(r'(<header.*?</header>\s*<div style="flex: 1 1 0%; display: flex; min-height: 0px">.*)', html, re.DOTALL)
if match:
    main_html = match.group(1)
    # Close the div manually if needed or just use bs4 to extract the node
else:
    main_html = html

jsx = html_to_jsx(html)

with open('temp_jsx.txt', 'w', encoding='utf-8') as f:
    f.write(jsx)
print("done")
