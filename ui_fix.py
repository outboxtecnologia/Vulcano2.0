with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('min-w-[530px]"', 'min-w-[660px]"')
text = text.replace('grid-cols-7 gap-2 border-l', 'grid-cols-7 gap-4 border-l')

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated UI Layout min-width!")
