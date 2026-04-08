import codecs

app_path = 'frontend/src/App.jsx'
views_path = 'frontend/src/VulcanoViews.jsx'

def expand_widths(content):
    # Expande os limites rígidos para preencher telas ultra-wide, mantendo paddings
    content = content.replace('max-w-7xl mx-auto w-full', 'max-w-[1920px] px-6 mx-auto w-full')
    content = content.replace('max-w-[1600px] mx-auto w-full', 'max-w-[1920px] px-6 mx-auto w-full')
    content = content.replace('max-w-[1400px]', 'max-w-[1800px]')
    content = content.replace('max-w-6xl', 'max-w-[1800px] px-6')
    content = content.replace('max-w-5xl', 'max-w-[1600px] px-6')
    return content

# 1. Update VulcanoViews.jsx
try:
    with codecs.open(views_path, 'r', 'utf-8') as f:
        views_content = f.read()
    
    views_content = expand_widths(views_content)
    
    with codecs.open(views_path, 'w', 'utf-8') as f:
        f.write(views_content)
    print("VulcanoViews.jsx updated!")
except Exception as e:
    print("Error on VulcanoViews:", e)

# 2. Update App.jsx
try:
    with codecs.open(app_path, 'r', 'utf-8') as f:
        app_content = f.read()

    app_content = expand_widths(app_content)

    # Inject the loader overlay inside the Receitas/Dashboard view
    # Look for the start of the receitas view:
    target = "{currentView === 'receitas' && ("
    loader_jsx = '''{currentView === 'receitas' && (
             <>
               {loadingReceitas && (
                 <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-md animate-in fade-in">
                    <div className="p-8 border border-outline-variant/20 rounded-sm bg-surface-container flex flex-col items-center shadow-2xl">
                      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                      <h3 className="text-primary font-headline font-black uppercase tracking-widest text-lg">Sincronizando Matriz Questor</h3>
                      <p className="text-on-surface-variant font-body text-[10px] uppercase mt-2 tracking-[0.2em] max-w-[250px] text-center">Calculando rateios contábeis e provisões IFRS para o volume de dados.</p>
                    </div>
                 </div>
               )}'''
               
    if target in app_content:
        app_content = app_content.replace(target, loader_jsx, 1) # Replace only the first occurrence just in case
        
    with codecs.open(app_path, 'w', 'utf-8') as f:
        f.write(app_content)
    print("App.jsx updated!")
except Exception as e:
    print("Error on App.jsx:", e)
