with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'hist = f"\{descr\} \{compl\}".strip\(\)', text)
for m in matches:
    start = max(0, m.start())
    end = min(len(text), m.start() + 1000)
    print(text[start:end])
    break
