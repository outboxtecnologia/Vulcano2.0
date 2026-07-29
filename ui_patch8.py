with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

bad = '''        {/* POPUP DE DETALHES DA UNIDADE */}
        {detalheModal && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 p-4 animate-in fade-in">'''

good = '''        {/* POPUP DE DETALHES DA UNIDADE */}
        {detalheModal && (
          <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/90 p-4 animate-in fade-in" onClick={e => e.stopPropagation()}>'''

text = text.replace(bad, good)

# Fix onClick QMENSAL to stopProp
import re
text = text.replace('onClick={() => setDetalheModal(', 'onClick={(e) => { e.stopPropagation(); setDetalheModal(')

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
