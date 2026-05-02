with open("backend/main.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def _get_smart_importer_db' in line:
        print("".join(lines[i:i+30]))
        break
