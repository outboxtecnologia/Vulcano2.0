import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

# Replace the !empresaConfirmed block
regex_empresa = re.compile(r'(if \(!empresaConfirmed\) \{.*?return \().*?(\);\s*\}\s*return \()', re.DOTALL)

new_empresa_block = """
      <div className="bg-surface text-on-surface font-body overflow-hidden min-h-screen w-full relative">
        <div className="relative z-10 h-screen w-full flex flex-col items-center justify-between py-12 px-8">
            <header className="w-full max-w-7xl flex justify-between items-center opacity-40 hover:opacity-100 transition-opacity duration-700">
              <span className="font-headline text-lg font-light tracking-[0.6em] text-on-surface">VULCANO</span>
            </header>
            
            <main className="w-full max-w-6xl flex flex-col items-center gap-16 mb-12">
               <div className="text-center space-y-4">
                   <h1 className="font-headline text-4xl md:text-5xl font-extralight tracking-tight text-on-surface">Selecione o Ambiente</h1>
                   <p className="font-body text-[10px] text-on-surface-variant uppercase tracking-[0.5em] opacity-80">Precision Audit Ecosystem</p>
               </div>
               
               {empresasLoading ? (
                  <div className="text-on-surface-variant flex gap-3 items-center"><Loader2 className="animate-spin" /> Carregando empresas...</div>
               ) : empresasError ? (
                  <div className="text-error bg-error-container p-6 max-w-lg text-center rounded-sm font-bold border border-error/50 tracking-widest uppercase text-xs">{empresasError}</div>
               ) : globalEmpresas.length === 0 ? (
                  <div className="text-on-surface-variant uppercase tracking-widest text-xs border border-outline-variant/30 p-8 rounded-sm bg-surface-container">Nenhuma empresa encontrada</div>
               ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full px-4 items-stretch">
                      {globalEmpresas.map((emp, i) => (
                          <div key={emp.id} className="group relative cursor-pointer" onClick={() => { setSelectedEmpresa(emp.id.toString()); setEmpresaConfirmed(true); }}>
                              <div className="p-8 flex flex-col h-full min-h-[250px] justify-between rounded-sm border border-outline-variant/30 hover:border-primary/50 bg-surface-container-low hover:bg-surface-container transition-all duration-300 shadow-xl shadow-background">
                                  <div className="space-y-6">
                                      <div className="w-10 h-10 flex items-center justify-center border border-outline-variant/30 group-hover:border-primary/40 group-hover:bg-primary/10 transition-all duration-300 bg-surface">
                                          <Building2 className="text-on-surface-variant group-hover:text-primary transition-colors" size={20}/>
                                      </div>
                                      <div className="space-y-2">
                                          <h3 className="font-headline text-lg font-bold tracking-widest text-on-surface group-hover:text-primary transition-colors uppercase leading-snug">{emp.id} - {emp.nome}</h3>
                                          <p className="text-on-surface-variant text-xs leading-relaxed font-light tracking-wide opacity-80 group-hover:opacity-100 transition-opacity">ERP Analytics & Tax Governance Node.</p>
                                      </div>
                                  </div>
                                  <div className="flex items-center gap-2 text-primary opacity-50 group-hover:opacity-100 transition-all duration-500 mt-6">
                                      <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Initialize</span>
                                      <ArrowUpRight size={14} className="group-hover:translate-x-1 transition-transform" />
                                  </div>
                              </div>
                          </div>
                      ))}
                  </div>
               )}
            </main>
            
            <footer className="w-full max-w-7xl flex justify-between items-end opacity-40 hover:opacity-100 transition-opacity duration-700 border-t border-outline-variant/20 pt-6">
              <div className="flex items-center gap-4">
                 <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                 <p className="text-[9px] font-body text-on-surface-variant uppercase tracking-[0.2em]">Live Nodes Active</p>
              </div>
            </footer>
        </div>
      </div>
"""

app_code = regex_empresa.sub(r'\1' + "\n" + new_empresa_block + "\n" + r'\2', app_code)

# Ensure Loader2, Sun, Moon are imported at the top
if 'Loader2' not in app_code:
    app_code = app_code.replace("import { Search,", "import { Search, Loader2, Sun, Moon,")

# Replace the theme state
regex_theme = re.compile(r"const \[theme, setTheme\] = useState\('tecton'\);.*?setTimeout\(\(\) => setThemeAnim\(''\), 1600\);\s*};\s*", re.DOTALL)
new_theme = """
  const [theme, setTheme] = useState('dark');
  useEffect(() => {
     if (theme === 'dark') {
         document.documentElement.classList.add('dark');
     } else {
         document.documentElement.classList.remove('dark');
     }
  }, [theme]);
  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
"""
app_code = regex_theme.sub(new_theme.strip() + "\n", app_code)

# Replace Global Shell (aside + header)
regex_shell = re.compile(r"return \(\s*<div data-theme=\{theme\} className=\"flex h-screen.*?</header>", re.DOTALL)

new_shell = """
return (
    <div className="bg-surface text-on-surface font-body selection:bg-primary-container selection:text-on-primary-container flex h-screen overflow-hidden transition-colors duration-300">
        
        {/* Lado Esquerdo - Stitch SideNavBar */}
        <aside className="fixed left-0 top-0 h-full w-64 z-[60] bg-surface-container-lowest flex flex-col py-6 border-r border-outline-variant/20 transition-colors">
            <div className="px-6 mb-10">
                <h1 className="font-headline font-black text-2xl text-primary tracking-tighter">VULCANO</h1>
                <p className="text-[10px] text-on-surface-variant tracking-widest uppercase mt-1 font-bold">Construction Intelligence</p>
            </div>
            
            <nav className="flex-1 overflow-y-auto w-full no-scrollbar">
                <div className="px-3 mb-2 mt-4 space-y-1">
                    <h3 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest pl-3 mb-3">Gestão Vulcano !</h3>
                    <NavItem icon={<Building2 size={16}/>} label="Empreendimentos" active={currentView === 'empreendimentos'} onClick={() => setCurrentView('empreendimentos')} />
                    <NavItem icon={<Users size={16}/>} label="Clientes" active={currentView === 'clientes'} onClick={() => setCurrentView('clientes')} />
                    <NavItem icon={<ShoppingCart size={16}/>} label="Vendas" active={currentView === 'vendas'} onClick={() => setCurrentView('vendas')} />
                    <NavItem icon={<DollarSign size={16}/>} label="Recebimentos" active={currentView === 'recebimentos'} onClick={() => setCurrentView('recebimentos')} />
                </div>
                <div className="px-3 mb-2 mt-6 space-y-1 border-t border-outline-variant/10 pt-4">
                    <NavItem icon={<Database size={16}/>} label="Database Explorer" active={currentView === 'explorer'} onClick={() => setCurrentView('explorer')} />
                    <NavItem icon={<PieChart size={16}/>} label="Dashboard" active={currentView === 'receitas'} onClick={() => setCurrentView('receitas')} />
                    <NavItem icon={<Landmark size={16}/>} label="Tributos Globais" active={currentView === 'tributos'} onClick={() => setCurrentView('tributos')} />
                    <NavItem icon={<Construction size={16}/>} label="Evolução POC" active={currentView === 'poc'} onClick={() => setCurrentView('poc')} />
                    <NavItem icon={<ShieldAlert size={16}/>} label="Auditoria ERP" active={currentView === 'compare'} onClick={() => setCurrentView('compare')} />
                    <NavItem icon={<Zap size={16}/>} label="Conversor XML" active={currentView === 'conciliador'} onClick={() => setCurrentView('conciliador')} />
                    <NavItem icon={<Briefcase size={16}/>} label="Fiscal & SPED" active={currentView === 'fiscal'} onClick={() => setCurrentView('fiscal')} />
                    <NavItem icon={<Activity size={16}/>} label="Sero INSS" active={currentView === 'sero'} onClick={() => setCurrentView('sero')} />
                </div>
            </nav>
            <div className="px-4 mt-auto space-y-4">
                <button className="w-full bg-primary-container text-on-primary-container py-3 rounded-sm font-bold text-xs uppercase tracking-widest flex items-center justify-center hover:opacity-90 transition-opacity">
                    Nova Obra
                </button>
            </div>
        </aside>

        {/* Global Wrapper para TopNav + Content */}
        <div className="ml-64 flex-1 flex flex-col h-full bg-background transition-colors relative z-10 w-full overflow-hidden">
            
            {/* TopNavBar Stitch Design */}
            <header className="h-16 border-b border-outline-variant/20 flex items-center justify-between px-8 bg-surface-container-low/80 backdrop-blur-xl shrink-0 z-50 transition-colors">
                <div className="flex items-center gap-4 flex-1">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" size={16} />
                        <input 
                            className="bg-surface-container-lowest border border-outline-variant/10 text-sm rounded-sm pl-10 pr-4 py-2 w-96 focus:ring-1 focus:ring-primary/30 text-on-surface outline-none transition-colors" 
                            placeholder="Buscar no ecossistema VULCANO..." 
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>
                
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 bg-surface-container-lowest px-3 py-2 rounded-sm border border-outline-variant/20 shadow-sm transition-colors">
                        <Building2 size={14} className="text-primary shrink-0" />
                        <select 
                            value={selectedEmpresa}
                            onChange={(e) => setSelectedEmpresa(e.target.value)}
                            className="bg-transparent border-none outline-none text-xs w-52 text-on-surface font-bold uppercase tracking-widest cursor-pointer appearance-none truncate"
                        >
                            {globalEmpresas.map(emp => (
                                <option key={emp.id} value={emp.id} className="bg-surface text-on-surface normal-case font-medium">
                                    {emp.id} - {emp.nome}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-4">
                        <button onClick={toggleTheme} className="p-2 text-on-surface-variant hover:text-primary transition-colors bg-surface-container-highest/50 border border-outline-variant/10 rounded-sm">
                            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                        </button>
                        <button onClick={handleRunSQL} className="text-on-surface-variant hover:text-primary transition-colors relative"><Download size={20}/></button>
                        <button className="text-on-surface-variant hover:text-primary transition-colors relative">
                            <Bell size={20} />
                            <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full"></span>
                        </button>
                        <div className="h-8 w-8 rounded-sm bg-surface-container overflow-hidden ml-2 border border-outline-variant/30">
                            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=VulcanoAdmin" alt="User" className="w-full h-full object-cover" />
                        </div>
                    </div>
                </div>
            </header>
"""

app_code = regex_shell.sub(new_shell.strip(), app_code)

# And now, update NavItem component.
regex_navitem = re.compile(r'const NavItem = \(\{ icon, label, active, onClick \}\) => \{.*?return \(.*?</button>\s*\);\s*\};', re.DOTALL)

new_navitem = """
  const NavItem = ({ icon, label, active, onClick }) => {
    return (
      <button 
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-200 ease-in-out border-l-2 outline-none ${
          active 
            ? 'text-primary border-primary bg-surface-container-lowest font-bold shadow-[inset_4px_0_0_0_rgba(1,1,1,0)] shadow-primary/20' 
            : 'text-on-surface-variant border-transparent hover:text-on-surface hover:bg-surface-container-highest/30'
        }`}
      >
        <span className={active ? "text-primary" : "opacity-70"}>{icon}</span>
        <span className="truncate">{label}</span>
      </button>
    );
  };
"""

app_code = regex_navitem.sub(new_navitem.strip(), app_code)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("App.jsx atualizado!")
