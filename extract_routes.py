with open("backend/main.py", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "@app." in line:
            print(line.strip())
