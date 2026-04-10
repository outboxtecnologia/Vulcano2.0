import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace limit_r and limit_rq caps
text = re.sub(r'limit_r = min\(6, len\(v_livres\) \+ 1\)\n\s+if len\(v_livres\) > 30: limit_r = min\(limit_r, 4\)\n\s+if len\(v_livres\) > 50: limit_r = min\(limit_r, 3\)', 
              r'limit_r = min(4, len(v_livres) + 1) # Max depth = 3 para evitar loop massivo', text)

text = re.sub(r'limit_rq = min\(6, len\(q_livres\) \+ 1\)\n\s+if len\(q_livres\) > 30: limit_rq = min\(limit_rq, 4\)\n\s+if len\(q_livres\) > 50: limit_rq = min\(limit_rq, 3\)', 
              r'limit_rq = min(4, len(q_livres) + 1) # Max depth = 3 para evitar loop massivo', text)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Replace limits OK")
