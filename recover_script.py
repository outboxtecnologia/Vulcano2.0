import os
import glob
import shutil

history_dir = r"C:\Users\dirfe\AppData\Roaming\Cursor\User\History"

app_candidates = []
vulcano_candidates = []

print(f"Scanning {history_dir}...")
count = 0

for root, dirs, files in os.walk(history_dir):
    for file in files:
        if file.endswith('.json'): continue  # VSCode entries.json
        filepath = os.path.join(root, file)
        
        try:
            stat = os.stat(filepath)
            # Both files were fairly large. App.jsx was > 10KB, VulcanoViews was > 50KB
            if stat.st_size < 10000:
                continue
                
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(20000) # Read first 20K to check
                
                if 'function App()' in content and 'BrowserRouter' in content:
                    app_candidates.append((filepath, stat.st_mtime))
                elif 'export const RecebimentosView' in content or 'VulcanoViews' in content:
                    # Let's double check it really looks like VulcanoViews
                    if 'import React' in content and 'max-w' in content:
                        vulcano_candidates.append((filepath, stat.st_mtime))
        except Exception as e:
            pass
        
        count += 1
        if count % 1000 == 0:
            print(f"Scanned {count} files...")

app_candidates.sort(key=lambda x: x[1], reverse=True)
vulcano_candidates.sort(key=lambda x: x[1], reverse=True)

print(f"Found {len(app_candidates)} App.jsx candidates.")
print(f"Found {len(vulcano_candidates)} VulcanoViews.jsx candidates.")

if app_candidates:
    best_app = app_candidates[0][0]
    shutil.copy2(best_app, r'c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\App.jsx')
    print(f"Restored App.jsx from {best_app}")

if vulcano_candidates:
    best_vulcano = vulcano_candidates[0][0]
    shutil.copy2(best_vulcano, r'c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx')
    print(f"Restored VulcanoViews.jsx from {best_vulcano}")
