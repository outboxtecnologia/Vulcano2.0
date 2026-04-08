import re

with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

routes = re.findall(r'@app\.[a-z]+\("([^"]+)"', text)
for r in routes:
    print(r)
