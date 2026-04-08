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
            # Files are larger
            if stat.st_size < 10000:
                continue
                
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(200000) # Read the entire history chunk
                
                # Loose matching App.jsx
                if 'export default App;' in content and '<div' in content and 'BrowserRouter' in content:
                    app_candidates.append((filepath, stat.st_mtime, stat.st_size))
                
                # Loose matching VulcanoViews.jsx
                if 'export const ' in content and 'RecebimentosView' in content and 'onClick' in content:
                    vulcano_candidates.append((filepath, stat.st_mtime, stat.st_size))
        except Exception as e:
            pass
        
        count += 1
        if count % 2000 == 0:
            print(f"Scanned {count} files...")

app_candidates.sort(key=lambda x: x[1], reverse=True)
vulcano_candidates.sort(key=lambda x: x[1], reverse=True)

print(f"Found {len(app_candidates)} App.jsx candidates.")
if app_candidates:
    print(f"Best App.jsx: {app_candidates[0][0]} / Size: {app_candidates[0][2]} bytes")

print(f"Found {len(vulcano_candidates)} VulcanoViews.jsx candidates.")
if vulcano_candidates:
    print(f"Best VulcanoViews.jsx: {vulcano_candidates[0][0]} / Size: {vulcano_candidates[0][2]} bytes")

if app_candidates:
    best_app = app_candidates[0][0]
    shutil.copy2(best_app, r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\App.jsx')
    print(f"Restored App.jsx from {best_app}")

if vulcano_candidates:
    best_vulcano = vulcano_candidates[0][0]
    shutil.copy2(best_vulcano, r'c:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\VulcanoViews.jsx')
    print(f"Restored VulcanoViews.jsx from {best_vulcano}")
