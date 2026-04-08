import os
import re

logs_dir = r'c:\Users\dirfe\.gemini\antigravity\brain'
largest_app = ""
largest_app_path = ""

for root, dirs, files in os.walk(logs_dir):
    for f in files:
        if f == 'overview.txt':
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as logfile:
                    content = logfile.read()
                    # Find any big block with import React and export default App
                    matches = re.findall(r'(import React.*?export default App;?)', content, re.DOTALL)
                    for match in matches:
                        # Ensure it's not truncated
                        if len(match) > len(largest_app):
                            largest_app = match
                            largest_app_path = path

            except Exception as e:
                pass

if largest_app:
    print(f"FOUND App.jsx of size {len(largest_app)} in {largest_app_path}")
    with open('recovered_app_super.jsx', 'w', encoding='utf-8') as out:
        out.write(largest_app)
else:
    print("NO App.jsx found")

largest_vulcano = ""
largest_vulcano_path = ""

for root, dirs, files in os.walk(logs_dir):
    for f in files:
        if f == 'overview.txt':
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as logfile:
                    content = logfile.read()
                    # Find any big block matching VulcanoViews components
                    matches = re.findall(r'(export const DashboardMeta.*?)(?:```|<|\\n\\n\Z)', content, re.DOTALL)
                    for match in matches:
                        if len(match) > len(largest_vulcano):
                            largest_vulcano = match
                            largest_vulcano_path = path
            except Exception as e:
                pass

if largest_vulcano:
    print(f"FOUND Vulcano part of size {len(largest_vulcano)} in {largest_vulcano_path}")
    with open('recovered_vulcano_super.jsx', 'w', encoding='utf-8') as out:
        out.write(largest_vulcano)
else:
    print("NO Vulcano found")
