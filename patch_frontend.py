import re
with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Add usePgVector state near crossLoading
if 'const [usePgVector' not in text:
    text = re.sub(r'(const \[crossLoading, setCrossLoading\] = useState\(false\);)', 
                  r'\1\n  const [usePgVector, setUsePgVector] = useState(true);', text)

# Add usePgVector toggle button near Cross-Match button
btn_code = '''{crossLoading ? 'Cruzando...' : '🖇️ Cross-Match'}
        </button>'''

insert_code = '''{crossLoading ? 'Cruzando...' : '🖇️ Cross-Match'}
        </button>
        <button onClick={() => setUsePgVector(!usePgVector)}
          title="Aceleração Vetorial via PostgreSQL (Embeddings Semânticos)"
          className={`px-4 py-2.5 text-[9px] font-black uppercase tracking-widest rounded flex items-center gap-2 transition-all border ${
            usePgVector ? 'bg-[#ffcc00]/20 border-[#ffcc00]/60 text-[#ffcc00]' : 'bg-[var(--v-deep)] border-[var(--v-border)] text-[var(--v-text-faint)] hover:text-[#ffcc00] hover:border-[#ffcc00]/40'
          }`}>
          <Zap size={12}/> {usePgVector ? 'PGVector Ligado' : 'PGVector Desligado'}
        </button>'''

if btn_code in text and 'PGVector Ligado' not in text:
    text = text.replace(btn_code, insert_code)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
