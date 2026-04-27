import re
import glob

jsx_files = glob.glob('frontend/src/*.jsx')

for file_path in jsx_files:
    if 'AuditoriaERPView' in file_path:
        continue # We already did this one manually
        
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    original_text = text

    # Map specific hex classes to CSS variables
    # Backgrounds
    text = re.sub(r'bg-\[\#(050505|060606|080808|090909|000|000000)\]', 'bg-[var(--v-bg)]', text)
    text = re.sub(r'bg-\[\#(0a0a0a|0d0d0d|0e0e0e|111)\]', 'bg-[var(--v-deep)]', text)
    text = re.sub(r'bg-\[\#(131313|141414)\]', 'bg-[var(--v-card)]', text)
    text = re.sub(r'bg-\[\#(1a1a1a|1e1e1e|1a1a1c|222|252525)\]', 'bg-[var(--v-hover)]', text)

    # Borders
    text = re.sub(r'border-\[\#(0a0a0a|0e0e0e|111)\]', 'border-[var(--v-bg)]', text)
    text = re.sub(r'border-\[\#(1a1a1a|1e1e1e|222|333|444)\]', 'border-[var(--v-border)]', text)

    # Text Colors
    text = re.sub(r'text-white', 'text-[var(--v-text-bold)]', text)
    text = re.sub(r'text-\[\#e5e2e1\]', 'text-[var(--v-text)]', text)
    text = re.sub(r'text-\[\#ccc\]', 'text-[var(--v-text)]', text)
    text = re.sub(r'text-\[\#aaa\]', 'text-[var(--v-text-muted)]', text)
    text = re.sub(r'text-\[\#888\]', 'text-[var(--v-text-muted)]', text)
    text = re.sub(r'text-\[\#777\]', 'text-[var(--v-text-faint)]', text)
    text = re.sub(r'text-\[\#666|\#555|\#444\]', 'text-[var(--v-text-faint)]', text)

    # Accent Colors
    text = re.sub(r'text-\[\#ff4d00\]', 'text-[var(--v-accent)]', text)
    text = re.sub(r'bg-\[\#ff4d00\]', 'bg-[var(--v-accent)]', text)
    text = re.sub(r'text-\[\#ff9f0a\]', 'text-[var(--v-accent-2)]', text)
    text = re.sub(r'text-\[\#ffcc00\]', 'text-[var(--v-accent-6)]', text)
    text = re.sub(r'text-\[\#34c759\]', 'text-[var(--v-accent-3)]', text)
    text = re.sub(r'text-\[\#a259ff\]', 'text-[var(--v-accent-5)]', text)
    text = re.sub(r'text-\[\#007aff\]', 'text-[var(--v-accent-4)]', text)

    text = re.sub(r'bg-\[\#1a0800\]', 'bg-[var(--v-magma-glow)]', text) # Glows

    # Rounded replacements
    text = re.sub(r'rounded-(sm|md|lg|xl|2xl|full|\[.*?\])', 'rounded-[var(--v-radius)]', text)

    if text != original_text:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Refactored {file_path}")

print("All JSX files refactored.")
