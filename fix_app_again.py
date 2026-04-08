import codecs

app_path = 'frontend/src/App.jsx'
with codecs.open(app_path, 'r', 'utf-8') as f:
    content = f.read()

bad_string = """           {currentView === 'receitas' && (
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
             <React.Fragment>
              <div className="space-y-8 animate-in fade-in duration-700 max-w-[1920px] px-6 mx-auto w-full pb-20">"""

good_string = """           {currentView === 'receitas' && (
             <React.Fragment>
               {loadingReceitas && (
                 <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/90 backdrop-blur-sm animate-in fade-in">
                    <div className="p-8 border border-outline-variant/20 rounded-sm bg-surface-container flex items-center shadow-2xl gap-6 mx-auto max-w-2xl w-full">
                      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin shrink-0"></div>
                      <div>
                        <h3 className="text-primary font-headline font-black uppercase tracking-widest text-xl">Sincronizando Matriz Questor</h3>
                        <p className="text-on-surface-variant font-body text-xs uppercase mt-2 tracking-[0.2em]">O sistema está carregando o modelo pesado ({receitasData?.length || 0} nós soltos). Aguarde.</p>
                      </div>
                    </div>
                 </div>
               )}
              <div className="space-y-8 animate-in fade-in duration-700 max-w-[1920px] px-6 mx-auto w-full pb-20 relative">"""

if bad_string in content:
    content = content.replace(bad_string, good_string)
    with codecs.open(app_path, 'w', 'utf-8') as f:
        f.write(content)
    print("Replaced successfully!")
else:
    print("Bad string not found! Something is implicitly modifying whitespaces.")
