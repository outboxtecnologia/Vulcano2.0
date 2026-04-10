import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

def replace_dynamic_limit_r(match):
    return """        if len(v_livres) > 40: limit_r = 2
        elif len(v_livres) > 15: limit_r = 3
        else: limit_r = min(4, len(v_livres) + 1)"""

def replace_dynamic_limit_rq(match):
    return """        if len(q_livres) > 40: limit_rq = 2
        elif len(q_livres) > 15: limit_rq = 3
        else: limit_rq = min(4, len(q_livres) + 1)"""

text = re.sub(r'limit_r = min\(4, len\(v_livres\) \+ 1\).*?\n', replace_dynamic_limit_r(None) + '\n', text)
text = re.sub(r'limit_rq = min\(4, len\(q_livres\) \+ 1\).*?\n', replace_dynamic_limit_rq(None) + '\n', text)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Dynamic Pruning OK")
