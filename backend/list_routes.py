import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

routes = re.findall(r'@app\.[a-z]+\([\'"](.*?)[\'"]', content)
print('\n'.join(routes))
