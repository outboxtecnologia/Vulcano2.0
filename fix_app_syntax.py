import codecs

app_path = 'frontend/src/App.jsx'
with codecs.open(app_path, 'r', 'utf-8') as f:
    content = f.read()

# Bad block introduced earlier:
# {currentView === 'receitas' && (
#              <>
#                {loadingReceitas && (
#                   ...
#                )}
#             <div className="space-y-8 ...">

bad_chunk = '''{currentView === 'receitas' && (
             <>
               {loadingReceitas && (
                 <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-md animate-in fade-in">
                    <div className="p-8 border border-outline-variant/20 rounded-sm bg-surface-container flex flex-col items-center shadow-2xl">
                      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                      <h3 className="text-primary font-headline font-black uppercase tracking-widest text-lg">Sincronizando Matriz Questor</h3>
                      <p className="text-on-surface-variant font-body text-[10px] uppercase mt-2 tracking-[0.2em] max-w-[250px] text-center">Calculando rateios contábeis e provisões IFRS para o volume de dados.</p>
                    </div>
                 </div>
               )}
             <div className="space-y-8 animate-in fade-in duration-700 max-w-[1920px] px-6 mx-auto w-full pb-20">'''

good_chunk = '''{currentView === 'receitas' && (
             <div className="space-y-8 animate-in fade-in duration-700 max-w-[1920px] px-6 mx-auto w-full pb-20 relative">
               {loadingReceitas && (
                 <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/90 backdrop-blur-sm animate-in fade-in">
                    <div className="p-8 border border-outline-variant/20 rounded-sm bg-surface-container flex flex-col items-center shadow-2xl">
                      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                      <h3 className="text-primary font-headline font-black uppercase tracking-widest text-lg">Processando Dados...</h3>
                      <p className="text-on-surface-variant font-body text-[10px] uppercase mt-2 tracking-[0.2em] max-w-[250px] text-center">Aguarde, calculando rateios contábeis e estruturando layout.</p>
                    </div>
                 </div>
               )}'''

# Since we don't know exact spaces, let's use regex
import re

# Match from {currentView === 'receitas' && ( up to max-w-[1920px] ... >
pattern = re.compile(r"\{currentView === 'receitas' && \(\s*<>\s*\{loadingReceitas && \(\s*<div.*?</div>\s*\)\}\s*<div className=\"space-[^\"]+\">", re.DOTALL)

def replacer(match):
    matched_text = match.group(0)
    # the last div is the main container
    div_start = matched_text.rfind('<div className=')
    main_div = matched_text[div_start:]
    # inject ' relative' into main_div
    if 'relative' not in main_div:
        main_div = main_div.replace('">', ' relative">')
    
    loader = '''
               {loadingReceitas && (
                 <div className="absolute inset-0 z-50 flex flex-col items-start justify-center bg-background/90 backdrop-blur-md animate-in fade-in py-20 px-10">
                    <div className="p-8 border border-outline-variant/30 rounded-sm bg-surface-container-high flex items-center gap-6 shadow-2xl mx-auto w-full max-w-2xl">
                      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin shrink-0"></div>
                      <div>
                          <h3 className="text-primary font-headline font-black uppercase tracking-widest text-xl">Processando Lote de Dados</h3>
                          <p className="text-on-surface-variant font-body text-xs mt-2 uppercase tracking-widest">Renderização otimizada em andamento. Isso evita travamentos no console.</p>
                      </div>
                    </div>
                 </div>
               )}'''
               
    return "{currentView === 'receitas' && (\n" + main_div + loader

content = pattern.sub(replacer, content)

with codecs.open(app_path, 'w', 'utf-8') as f:
    f.write(content)

print("Syntax fixed")
