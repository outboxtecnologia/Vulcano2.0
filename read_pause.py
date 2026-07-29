with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'PAUSED' in line:
        start = max(0, i-5)
        end = min(len(lines), i+6)
        print("MATCH AT LINE", i)
        for j in range(start, end):
            print(f"{j}: {lines[j]}", end='')
        print("-" * 50)
