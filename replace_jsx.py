import re

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Map specific hex classes to CSS variables
# Backgrounds
text = re.sub(r'bg-\[\#(050505|060606|080808|090909|000|000000)\]', 'bg-[var(--v-bg)]', text) # Darkest bg
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

# Rounded replacements to respect theme variable
text = re.sub(r'rounded-(sm|md|lg|xl|2xl|full|\[.*?\])', 'rounded-[var(--v-radius)]', text)

# Inject Theme Switcher Component
theme_switcher = """
// ─── THEME SWITCHER ─────────────────────────────────────────────
const ThemeSwitcher = () => (
  <div className="flex items-center gap-2 bg-[var(--v-deep)] p-1 rounded-[var(--v-radius)] border border-[var(--v-border)]">
    <button onClick={() => document.documentElement.setAttribute('data-theme', 'night')} className="px-3 py-1 text-[11px] font-bold text-[var(--v-text-bold)] hover:bg-[var(--v-hover)] rounded-[var(--v-radius)] uppercase tracking-wider">Night</button>
    <button onClick={() => document.documentElement.setAttribute('data-theme', 'light')} className="px-3 py-1 text-[11px] font-bold text-[var(--v-text-bold)] hover:bg-[var(--v-hover)] rounded-[var(--v-radius)] uppercase tracking-wider">Light</button>
    <button onClick={() => document.documentElement.setAttribute('data-theme', 'numb')} className="px-3 py-1 text-[11px] font-bold text-[var(--v-text-bold)] hover:bg-[var(--v-hover)] rounded-[var(--v-radius)] uppercase tracking-wider">Numb</button>
  </div>
);
"""

# Place it before the main export
idx_export = text.find('export function AuditoriaERPView')
if idx_export != -1:
    text = text[:idx_export] + theme_switcher + text[idx_export:]

# Also inject into the Header UI of AuditoriaERPView
# It usually has something like <div className="flex items-center gap-4"> near the title section
header_pattern = r'(<h1 className="text-xl font-black text-\[var\(--v-text-bold\)\] uppercase tracking-tight">.*?</h1>)'
header_match = re.search(header_pattern, text, re.DOTALL)
if header_match:
    replacement = header_match.group(1) + '\\n        <ThemeSwitcher />'
    text = text.replace(header_match.group(1), replacement)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Facelift JSX refactored OK")
