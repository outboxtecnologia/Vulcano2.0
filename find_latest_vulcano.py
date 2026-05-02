import os
import time

history_dir = r"C:\Users\dirfe\AppData\Roaming\Cursor\User\workspaceStorage"

candidates = []

print(f"Scanning {history_dir}...")

for root, dirs, files in os.walk(history_dir):
    for file in files:
        if file.endswith('.json'): continue
        filepath = os.path.join(root, file)
        
        try:
            stat = os.stat(filepath)
            if stat.st_size < 1000: continue
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if 'RecebimentosView' in content and 'IMPORTA' in content.upper():
                    candidates.append((filepath, stat.st_mtime, len(content)))
        except Exception as e:
            pass

candidates.sort(key=lambda x: x[1], reverse=True)

print(f"Found {len(candidates)} versions of VulcanoViews.jsx with 'IMPORTAÇÃO'.")
for c in candidates[:5]:
    dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c[1]))
    print(f" - {c[0]} (Size: {c[2]}, Time: {dt})")

if candidates:
    import shutil
    shutil.copy2(candidates[0][0], r'C:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx')
    print("Restored LATEST VulcanoViews!")
