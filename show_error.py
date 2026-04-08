with open('build_error.log', 'r', encoding='utf-16') as f:
    text = f.read()
with open('clear_error.txt', 'w', encoding='utf-8') as f:
    f.write(text)
