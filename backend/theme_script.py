import re

target = 'c:/Users/dirfe/.gemini/antigravity/scratch/questor_explorer/frontend/src/App.jsx'

with open(target, 'r', encoding='utf-8') as f:
    code = f.read()

# Substitutions for theming
subs = [
    (r'bg-\[\#0b0b0b\]', 'bg-[var(--v-bg)]'),
    (r'bg-\[\#131313\]', 'bg-[var(--v-card)]'),
    (r'bg-\[\#1a1a1a\]', 'bg-[var(--v-hover)]'),
    (r'bg-\[\#1a1a1c\]', 'bg-[var(--v-hover)]'),
    (r'bg-\[\#111\]', 'bg-[var(--v-card)]'),
    (r'bg-\[\#050505\]', 'bg-[var(--v-deep)]'),
    (r'bg-\[\#222\]', 'bg-[var(--v-muted)]'),
    (r'border-\[\#353534\]', 'border-[var(--v-border)]'),
    (r'border-\[\#333\]', 'border-[var(--v-border)]'),
    (r'border-\[\#222\]', 'border-[var(--v-border)]'),
    (r'border-\[\#1a1a1a\]', 'border-[var(--v-border)]'),
    (r'text-\[\#e5e2e1\]', 'text-[var(--v-text)]'),
    (r'text-white', 'text-[var(--v-text-bold)]'),
    (r'text-\[\#aaa\]', 'text-[var(--v-text-muted)]'),
    (r'text-\[\#888\]', 'text-[var(--v-text-muted)]'),
    (r'text-\[\#666\]', 'text-[var(--v-text-muted)]'),
    (r'text-\[\#555\]', 'text-[var(--v-text-faint)]'),
    (r'text-\[\#ff4d00\]', 'text-[var(--v-accent)]'),
    (r'bg-\[\#ff4d00\]', 'bg-[var(--v-accent)]'),
    (r'border-\[\#ff4d00\]', 'border-[var(--v-accent)]'),
    (r'text-black', 'text-[var(--v-text-inv)]'),
    (r'border-\[\#ff9f0a\]', 'border-[var(--v-accent-2)]'),
    (r'bg-\[\#ff9f0a\]', 'bg-[var(--v-accent-2)]'),
    (r'text-\[\#ff9f0a\]', 'text-[var(--v-accent-2)]'),
    (r'border-\[\#34c759\]', 'border-[var(--v-accent-3)]'),
    (r'bg-\[\#34c759\]', 'bg-[var(--v-accent-3)]'),
    (r'text-\[\#34c759\]', 'text-[var(--v-accent-3)]'),
    (r'border-\[\#00c2ff\]', 'border-[var(--v-accent-4)]'),
    (r'bg-\[\#00c2ff\]', 'bg-[var(--v-accent-4)]'),
    (r'text-\[\#00c2ff\]', 'text-[var(--v-accent-4)]'),
    (r'text-\[\#a259ff\]', 'text-[var(--v-accent-5)]'),
    (r'bg-\[\#a259ff\]', 'bg-[var(--v-accent-5)]'),
    (r'border-\[\#a259ff\]', 'border-[var(--v-accent-5)]'),
    (r'text-\[\#ffcc00\]', 'text-[var(--v-accent-6)]'),
    (r'bg-\[\#ffcc00\]', 'bg-[var(--v-accent-6)]'),
    (r'border-\[\#ffcc00\]', 'border-[var(--v-accent-6)]')
]

for pattern, repl in subs:
    code = re.sub(pattern, repl, code)

with open(target, 'w', encoding='utf-8') as f:
    f.write(code)

print("App.jsx Tailwind Hex to CSS Custom Vars replaced efficiently.")
