import re
with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Add usePgVector state near crossLoading
if 'const [usePgVector' not in text:
    text = re.sub(r'(const \[crossLoading,\s*setCrossLoading\]\s*=\s*useState\(false\);)', 
                  r'\1\n  const [usePgVector, setUsePgVector] = useState(true);', text)

# Add usePgVector toggle button near Cross-Match button
btn_target_re = r'(\{[^}]*\}\s*\{\s*crossLoading\s*\?\s*\'Cruzando\.\.\.\'\s*:\s*\'[^\']+\'\}\s*</button>)'

insert_code = r'''\1
        <button onClick={() => setUsePgVector(!usePgVector)}
          title="Aceleração Vetorial via PostgreSQL (Embeddings Semânticos)"
          className={`px-4 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all border ${
            usePgVector ? 'bg-[#ffcc00]/20 border-[#ffcc00]/60 text-[#ffcc00]' : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[#ffcc00] hover:border-[#ffcc00]/40'
          }`}>
          <Zap size={12}/> {usePgVector ? 'PGVector Ligado' : 'PGVector Desligado'}
        </button>'''

if 'PGVector Ligado' not in text:
    text = re.sub(btn_target_re, insert_code, text)

text = re.sub(r'(threshold:\s*0\.38,?)', r'\1\n          use_pgvector: usePgVector,', text)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patch OK")
