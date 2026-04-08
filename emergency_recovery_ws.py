import os
import shutil

history_dir = r"C:\Users\dirfe\AppData\Roaming\Cursor\User\workspaceStorage"

app_candidates = []
vulcano_candidates = []

print(f"Scanning {history_dir}...")

for root, dirs, files in os.walk(history_dir):
    for file in files:
        if file.endswith('.json'): continue
        # Cursor local history files are usually named `entries.json` or random hashes inside LocalHistory
        filepath = os.path.join(root, file)
        
        try:
            stat = os.stat(filepath)
            if stat.st_size < 1000: continue
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if 'currentView ===' in content and 'BrowserRouter' in content and 'receitas-caixa' not in content:
                    app_candidates.append((filepath, stat.st_mtime, len(content)))
                
                if 'export const RecebimentosView' in content:
                    vulcano_candidates.append((filepath, stat.st_mtime, len(content)))
        except Exception as e:
            pass

app_candidates.sort(key=lambda x: x[1], reverse=True)
vulcano_candidates.sort(key=lambda x: x[1], reverse=True)

print(f"Found {len(app_candidates)} App.jsx candidates.")
for c in app_candidates[:3]:
    print(f" - {c[0]} (Size: {c[2]}, Time: {c[1]})")

print(f"Found {len(vulcano_candidates)} VulcanoViews.jsx candidates.")
for c in vulcano_candidates[:3]:
    print(f" - {c[0]} (Size: {c[2]}, Time: {c[1]})")

if app_candidates:
    best_app = app_candidates[0][0]
    shutil.copy2(best_app, r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\App.jsx')
    print(f"Restored App.jsx from {best_app}")

if vulcano_candidates:
    best_vulcano = vulcano_candidates[0][0]
    shutil.copy2(best_vulcano, r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\frontend\src\VulcanoViews.jsx')
    print(f"Restored VulcanoViews.jsx from {best_vulcano}")
