import os
import shutil
import time

history_dir = r"C:\Users\dirfe\AppData\Roaming\Cursor\User\workspaceStorage"
candidates = []

print("Scanning for large recent files...")

for root, dirs, files in os.walk(history_dir):
    for file in files:
        if file.endswith('.json'): continue
        filepath = os.path.join(root, file)
        
        try:
            stat = os.stat(filepath)
            # Both App and VulcanoViews are large
            if stat.st_size > 30000:
                # Only check files modified in the last 24 hours
                if (time.time() - stat.st_mtime) < 86400:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(5000)
                        if 'import ' in content and 'export ' in content and ('react' in content.lower() or 'div' in content):
                            candidates.append((filepath, stat.st_mtime, stat.st_size))
        except Exception:
            pass

candidates.sort(key=lambda x: x[1], reverse=True)

print(f"Found {len(candidates)} recent large JSX-like files.")
os.makedirs('recent_jsxs', exist_ok=True)

# Copy top 20 to a folder for manual inspection
for i, c in enumerate(candidates[:20]):
    dt = time.strftime('%H:%M:%S', time.localtime(c[1]))
    dest = f"recent_jsxs/file_{i}_{dt.replace(':','')}_size_{c[2]}.jsx"
    shutil.copy2(c[0], dest)
    print(f"Copied {c[0]} -> {dest}")
