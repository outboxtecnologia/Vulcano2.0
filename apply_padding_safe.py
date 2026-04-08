import os

def fix_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    for old, new in replacements:
        text = text.replace(old, new)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


fix_file(r'frontend\src\App.jsx', [
    ('max-w-[1920px] px-6 mx-auto w-full', 'w-full px-4'),
    ('max-w-[1800px] px-6', 'w-full px-4'),
    ('max-w-[1600px] px-6', 'w-full px-4'),
    ('p-4 md:p-6 lg:p-8', 'p-4 md:p-5 lg:p-6')
])

fix_file(r'frontend\src\VulcanoViews.jsx', [
    ('max-w-[1920px] px-6 mx-auto w-full', 'w-full px-4'),
    ('max-w-[1800px] px-6', 'w-full px-4'),
    ('max-w-[1600px] px-6', 'w-full px-4')
])

print("Padding fixes applied without wiping!")
