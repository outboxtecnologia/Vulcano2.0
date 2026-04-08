import codecs

app_path = 'frontend/src/App.jsx'
with codecs.open(app_path, 'r', 'utf-8') as f:
    content = f.read()

start_str = "           {currentView === 'receitas' && (\n             <>"
end_str = '              <div className="space-y-8 animate-in fade-in duration-700 max-w-[1920px] px-6 mx-auto w-full pb-20">'

if start_str in content and end_str in content:
    start_idx = content.find(start_str)
    end_idx = content.find(end_str) + len(end_str)
    
    good_chunk = '''           {currentView === 'receitas' && (
             <React.Fragment>
               {loadingReceitas && (
                 <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-sm animate-in fade-in">
                    <div className="p-8 border border-outline-variant/20 rounded-sm bg-surface-container flex items-center shadow-2xl gap-6 mx-auto max-w-2xl w-full">
                      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin shrink-0"></div>
                      <div>
                        <h3 className="text-primary font-headline font-black uppercase tracking-widest text-xl">Sincronizando Matriz Questor</h3>
                        <p className="text-on-surface-variant font-body text-xs uppercase mt-2 tracking-[0.2em]">O sistema está carregando o modelo pesado. Aguarde.</p>
                      </div>
                    </div>
                 </div>
               )}
              <div className="space-y-8 animate-in fade-in duration-700 max-w-[1920px] px-6 mx-auto w-full pb-20 relative">'''
              
    content = content[:start_idx] + good_chunk + content[end_idx:]
    with codecs.open(app_path, 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed by index!")
else:
    print("Start or End not found!")

