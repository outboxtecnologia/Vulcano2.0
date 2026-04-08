import re
import ast

def extract_strings_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filename)

    strings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        strings[target.id] = node.value.value
    return strings

scripts = [
    'update_app_shell.py',
    'refactor_receitas.py',
    'replace_script_vendas.py',
    'replace_script_receb.py',
]

all_extracted = {}
for s in scripts:
    try:
        all_extracted.update(extract_strings_from_file(s))
    except Exception as e:
        print(f"Failed on {s}: {e}")

for k, v in all_extracted.items():
    preview = v[:50].replace('\n', ' ')
    print(f"{k} (from {len(v)} chars) -> {preview}")
