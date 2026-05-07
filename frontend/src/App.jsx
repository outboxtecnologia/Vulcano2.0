import React, { useState, useEffect } from 'react';
import SmartImporter from './SmartImporter';
import { DashboardMeta, VendasView, RecebimentosView, ConciliadorView } from './VulcanoViews';
import { EmpreendimentosView } from './EmpreendimentosView';
import { FiscalSpedView } from './FiscalSpedView';
import { TributosGlobaisView } from './TributosGlobaisView';
import { EvolucaoPOCView } from './EvolucaoPOCView';
import { SeroView } from './SeroView';
import { RawExplorerView } from './RawExplorerView';
import { CustosView } from './CustosView';
import { ContabilizacoesView } from './ContabilizacoesView';
import { AuditoriaERPView } from './AuditoriaERPView';
import { SindicatosView } from './SindicatosView';
import { JanitorView } from './JanitorView';
import LoginView from './LoginView';
import EmpresaSelectionView from './components/EmpresaSelectionView';
import { API_BASE } from './apiBase';
import './index.css';
import {
  Building2, Database, TableProperties, Fingerprint, PieChart, Construction,
  Users, Activity, ActivityIcon, BookUser, Globe2, Briefcase, Zap, Search, Bell, Download, Sun, Moon,
  RefreshCw, AlertCircle, Plus, UploadCloud, FileSpreadsheet, HandCoins,
  Terminal, ShieldCheck, ShoppingCart, DollarSign, LayoutDashboard, ShieldAlert, Landmark, Cpu, TrendingUp, Trash2
} from 'lucide-react';
import { Loader2, ArrowUpRight, ChevronRight, ChevronLeft } from 'lucide-react';

  const NavItem = ({ icon, label, active, onClick, isSidebarOpen = true }) => {
    return (
      <button 
        onClick={onClick}
        title={!isSidebarOpen ? label : undefined}
        className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-200 ease-in-out border-l-2 outline-none ${
          active 
            ? 'text-primary border-primary bg-surface-container-lowest font-bold shadow-[inset_4px_0_0_0_rgba(1,1,1,0)] shadow-primary/20' 
            : 'text-on-surface-variant border-transparent hover:text-on-surface hover:bg-surface-container-highest/30'
        } ${!isSidebarOpen ? 'justify-center px-0' : ''}`}
      >
        <span className={active ? "text-primary" : "opacity-70"}>{icon}</span>
        {isSidebarOpen && <span className="truncate">{label}</span>}
      </button>
    );
  };


export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const [selectedEmpresa, setSelectedEmpresa] = useState('');
  const [empresaConfirmed, setEmpresaConfirmed] = useState(false);
  const [globalEmpresas, setGlobalEmpresas] = useState([]);
  const [empresasLoading, setEmpresasLoading] = useState(true);
  const [empresasError, setEmpresasError] = useState(null);
  const [loadingSlow, setLoadingSlow] = useState(false); // true se passar de 4s
  const [manualId, setManualId] = useState('959');
  const [currentView, setCurrentView] = useState('receitas');
  const [search, setSearch] = useState('');

  const [theme, setTheme] = useState('night');
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'night') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    // Avisa o usuario se estiver lento após 4s
    const slowTimer = setTimeout(() => setLoadingSlow(true), 4000);
    fetch(`${API_BASE}/api/vulcano/empresas`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) {
          const msg = typeof d.detail === 'string' ? d.detail : (d.detail ? JSON.stringify(d.detail) : r.statusText);
          throw new Error(msg || `HTTP ${r.status}`);
        }
        setGlobalEmpresas(Array.isArray(d) ? d : (d.data || []));
        setEmpresasLoading(false);
        setLoadingSlow(false);
      })
      .catch((e) => {
        setEmpresasError(
          e.message?.includes('Failed to fetch') || e.name === 'TypeError'
            ? `Erro de conexão com o backend (${API_BASE}). Verifique se a API está no ar ou use entrada manual.`
            : `Falha ao carregar empresas: ${e.message}`
        );
        setGlobalEmpresas([]);
        setEmpresasLoading(false);
        setLoadingSlow(false);
      })
      .finally(() => { clearTimeout(slowTimer); });
    return () => { clearTimeout(slowTimer); };
  }, []);


  const handleRunSQL = () => alert('SQL Execution triggered for environment: ' + selectedEmpresa);

  if (!isAuthenticated) {
    return <LoginView onLogin={(userData) => { setUser(userData); setIsAuthenticated(true); }} />;
  }

  if (!empresaConfirmed) {
    return (
      <EmpresaSelectionView
        globalEmpresas={globalEmpresas}
        onSelectEmpresa={(id) => { setSelectedEmpresa(id); setEmpresaConfirmed(true); }}
        onLogout={() => { setIsAuthenticated(false); }}
      />
    );
  }


return (
    <div className="font-body selection:bg-[var(--v-accent)]/30 flex h-screen overflow-hidden transition-colors duration-300 immersive-bg"
         data-theme={theme}
         style={{ color: 'var(--v-text)', background: '#0c0908' }}>
        <div className="absolute inset-0 backdrop-blur-[1px] z-0"
             style={{ background: 'var(--v-blur-bg)' }}></div>

        {/* Lado Esquerdo - Stitch SideNavBar */}
        <aside className={`fixed left-0 top-0 h-full ${isSidebarOpen ? 'w-64' : 'w-20'} z-[60] flex flex-col py-6 transition-all duration-300 ease-in-out`}
               style={{
                 background: '#0c0908',
                 backdropFilter: 'blur(24px)',
                 WebkitBackdropFilter: 'blur(24px)',
                 borderRight: '1px solid rgba(255, 160, 80, 0.08)'
               }}>
            
            {/* Toggle Button */}
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="absolute top-16 -right-3 w-6 h-6 flex items-center justify-center bg-[var(--v-card)] border border-[var(--v-border)] rounded-full text-[var(--v-text-muted)] cursor-pointer z-50 shadow-md hover:text-[var(--v-accent)] transition-all"
            >
              <ChevronRight size={14} className={`transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
            </button>

            <div className={`px-6 mb-10 flex items-center ${isSidebarOpen ? 'gap-3' : 'justify-center px-0'}`}>
                <div className="w-8 h-8 shrink-0 bg-[var(--v-accent)] rounded-[var(--v-radius)] flex items-center justify-center shadow-[0_0_15px_#ff4d0066]">
                  <Cpu size={18} className="text-black" />
                </div>
                {isSidebarOpen && (
                  <div className="whitespace-nowrap overflow-hidden">
                     <h1 className="font-headline font-black text-xl tracking-tighter leading-none" style={{ color: 'var(--v-text-bold)' }}>VULCANO</h1>
                     <p className="text-[9px] tracking-[0.2em] uppercase mt-1 font-black" style={{ color: 'var(--v-accent)' }}>CONTÁBIL · 2.0</p>
                  </div>
                )}
            </div>
            
            <nav className="flex-1 overflow-y-auto w-full no-scrollbar px-3 space-y-8">
                <div className="space-y-1">
                    {isSidebarOpen && <h3 className="text-[10px] font-black opacity-60 uppercase tracking-[0.3em] pl-3 mb-3" style={{ color: 'var(--v-text-muted)' }}>Core Modules</h3>}
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<LayoutDashboard size={16}/>} label="Dashboard" active={currentView === 'receitas'} onClick={() => setCurrentView('receitas')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Building2 size={16}/>} label="Empreendimentos" active={currentView === 'empreendimentos'} onClick={() => setCurrentView('empreendimentos')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<ShoppingCart size={16}/>} label="Vendas" active={currentView === 'vendas'} onClick={() => setCurrentView('vendas')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<DollarSign size={16}/>} label="Recebimentos" active={currentView === 'recebimentos'} onClick={() => setCurrentView('recebimentos')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<FileSpreadsheet size={16}/>} label="Smart Importer" active={currentView === 'importer'} onClick={() => setCurrentView('importer')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<UploadCloud size={16}/>} label="Conversor Universal" active={currentView === 'conciliador'} onClick={() => setCurrentView('conciliador')} />
                </div>
                <div className="space-y-1 border-t border-white/5 pt-6">
                    {isSidebarOpen && <h3 className="text-[10px] font-black opacity-60 uppercase tracking-[0.3em] pl-3 mb-3" style={{ color: 'var(--v-text-muted)' }}>Enterprise Suite</h3>}
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<PieChart size={16}/>} label="Tributos Globais" active={currentView === 'tributos'} onClick={() => setCurrentView('tributos')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Construction size={16}/>} label="Evolução POC" active={currentView === 'poc'} onClick={() => setCurrentView('poc')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<ShieldCheck size={16}/>} label="Auditoria ERP" active={currentView === 'compare'} onClick={() => setCurrentView('compare')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<TrendingUp size={16}/>} label="Contabilizações" active={currentView === 'contabilizacoes'} onClick={() => setCurrentView('contabilizacoes')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Briefcase size={16}/>} label="Fiscal & SPED" active={currentView === 'fiscal'} onClick={() => setCurrentView('fiscal')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<HandCoins size={16}/>} label="Fechamento Custos" active={currentView === 'custos'} onClick={() => setCurrentView('custos')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Activity size={16}/>} label="Sero INSS" active={currentView === 'sero'} onClick={() => setCurrentView('sero')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Users size={16}/>} label="Sindicatos CCT" active={currentView === 'sindicatos'} onClick={() => setCurrentView('sindicatos')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Database size={16}/>} label="Raw Explorer" active={currentView === 'explorer'} onClick={() => setCurrentView('explorer')} />
                    <NavItem isSidebarOpen={isSidebarOpen} icon={<Trash2 size={16}/>} label="🧹 Janitor SRE" active={currentView === 'janitor'} onClick={() => setCurrentView('janitor')} />
                </div>
            </nav>
            <div className="px-4 mt-auto">
                <button className={`w-full bg-[#F97316] text-black py-4 rounded-[var(--v-radius)] font-black uppercase tracking-[0.1em] flex items-center justify-center transition-all shadow-[0_0_20px_#ff4d0033] ${isSidebarOpen ? 'text-[12px]' : 'text-transparent'}`}
                        style={{ ':hover': { background: 'white' } }} title="NOVA OBRA">
                    <Plus size={16} className={isSidebarOpen ? "mr-2" : "text-black"} /> {isSidebarOpen && "NOVA OBRA"}
                </button>
            </div>
        </aside>

        {/* Global Wrapper para TopNav + Content */}
        <div className={`${isSidebarOpen ? 'ml-64' : 'ml-20'} flex-1 flex flex-col h-full bg-transparent transition-all duration-300 relative z-10 w-full overflow-hidden`}>

            {/* TopNavBar Stitch Design */}
            <header className="h-16 flex items-center justify-between px-8 backdrop-blur-2xl shrink-0 z-50 transition-colors"
                    style={{
                      borderBottom: '1px solid rgba(255, 160, 80, 0.08)',
                      background: '#0c0908'
                    }}>
                <div className="flex items-center gap-4 flex-1">
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 transition-colors" size={16}
                                style={{ color: 'var(--v-text-faint)' }} />
                        <input
                            className="text-xs rounded-[var(--v-radius)] pl-10 pr-4 py-2 w-96 outline-none transition-all"
                            style={{
                              background: 'var(--v-card)',
                              border: '1px solid rgba(255, 160, 80, 0.08)',
                              color: 'var(--v-text)',
                            }}
                            placeholder="Pesquisar no Cortex Index..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>
                
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-[var(--v-radius)] shadow-sm transition-colors"
                         style={{ background: 'var(--v-card)', border: '1px solid rgba(255, 160, 80, 0.08)' }}>
                        <Database size={12} className="text-[var(--v-accent)] shrink-0" />
                        <select
                            value={selectedEmpresa}
                            onChange={(e) => setSelectedEmpresa(e.target.value)}
                            className="border-none outline-none text-[10px] w-52 font-black uppercase tracking-[0.2em] cursor-pointer appearance-none truncate bg-transparent"
                            style={{ color: 'var(--v-text)' }}
                        >
                            {globalEmpresas.map(emp => (
                                <option key={emp.id} value={emp.id} style={{ background: 'var(--v-card)', color: 'var(--v-text)' }}>
                                    {emp.id} - {emp.nome}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-4 h-full">
                        <div className="h-8 w-[1px] bg-white/5"></div>
                        <select value={theme} onChange={(e) => { document.documentElement.setAttribute('data-theme', e.target.value); setTheme(e.target.value); }}
                                className="px-2 py-1 outline-none font-bold text-[10px] cursor-pointer uppercase transition-all rounded-[var(--v-radius)]"
                                style={{ color: 'var(--v-text-bold)', border: '1px solid rgba(255, 160, 80, 0.08)', background: 'var(--v-card)' }}>
                            <option value="night">NIGHT</option>
                            <option value="light">LIGHT</option>
                            <option value="numb">NUMB</option>
                        </select>
                        <button onClick={handleRunSQL} className="hover:text-[var(--v-accent)] transition-all relative" style={{ color: 'var(--v-text-faint)' }}><Download size={18}/></button>
                        <button className="hover:text-[var(--v-accent)] transition-all relative" style={{ color: 'var(--v-text-faint)' }}>
                            <Bell size={18} />
                            <span className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--v-accent)] rounded-[var(--v-radius)] shadow-[0_0_8px_#ff4d00]"></span>
                        </button>
                        <div className="h-8 w-8 rounded-[var(--v-radius)] bg-[var(--v-accent)]/10 overflow-hidden ml-2 border border-[#ff4d00]/20 p-[2px]">
                            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedEmpresa || 'Vulcano'}`} alt="User" className="w-full h-full object-cover rounded-[var(--v-radius)]" />
                        </div>
                    </div>
                </div>
            </header>


            {/* MAIN CONTENT AREA */}
            <main className="flex-1 overflow-x-hidden overflow-y-auto transition-colors p-8 relative custom-scrollbar"
                  style={{ background: 'transparent' }}>
              <div className="absolute top-0 right-0 w-[1000px] h-[1000px] rounded-[var(--v-radius)] blur-[150px] pointer-events-none -translate-y-1/2 translate-x-1/3"
                   style={{ background: 'var(--v-magma-glow)' }}></div>
              <div className="max-w-[1920px] mx-auto min-h-full flex flex-col">
                  <div className="w-full h-full">
                      {currentView === 'empreendimentos' && <EmpreendimentosView selectedEmpresa={selectedEmpresa} onNavigate={(view) => setCurrentView(view)} />}
                      {currentView === 'vendas' && <VendasView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'recebimentos' && <RecebimentosView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'receitas' && <DashboardMeta selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'conciliador' && <ConciliadorView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'importer' && <SmartImporter dbPath="poc_database.sqlite" selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'custos' && <CustosView selectedEmpresa={selectedEmpresa} />}
                      
                      {currentView === 'fiscal' && <FiscalSpedView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'tributos' && <TributosGlobaisView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'poc' && <EvolucaoPOCView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'sero' && <SeroView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'sindicatos' && <SindicatosView />}
                      {currentView === 'explorer' && <RawExplorerView />}
                      
                      {currentView === 'compare' && <AuditoriaERPView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'contabilizacoes' && <ContabilizacoesView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'janitor' && <JanitorView />}

                      {['clientes'].includes(currentView) && (
                          <div className="h-full flex flex-col items-center justify-center py-32 text-center relative z-10 w-full animate-in zoom-in-95 duration-500">
                              <div className="w-24 h-24 mb-10 rounded-[var(--v-radius)] bg-black/40 border border-white/5 flex items-center justify-center shadow-2xl relative overflow-hidden group">
                                  <div className="absolute inset-0 bg-[var(--v-accent)] opacity-0 group-hover:opacity-10 transition-opacity"></div>
                                  <Cpu size={40} className="text-[var(--v-accent)] animate-pulse" />
                              </div>
                              <h2 className="font-headline text-4xl font-black tracking-widest text-[var(--v-text-bold)] uppercase mb-4">Módulo Offline</h2>
                              <p className="text-[var(--v-text-faint)] font-black tracking-[0.5em] uppercase text-[10px] max-w-md leading-relaxed">
                                 Aguardando integração do Cortex Node com o ERP Firebird para este dataset específico.
                              </p>
                              <div className="mt-12 flex gap-4">
                                 <button onClick={() => setCurrentView('receitas')} className="px-6 py-2 border border-white/10 text-[9px] font-black uppercase tracking-widest text-[var(--v-text-muted)] hover:border-[#ff4d00] hover:text-[var(--v-text-bold)] transition-all">Voltar ao Nexus</button>
                                 <button className="px-6 py-2 bg-[var(--v-accent)]/10 text-[var(--v-accent)] text-[9px] font-black uppercase tracking-widest border border-[#ff4d00]/20">Abrir Ticket</button>
                              </div>
                          </div>
                      )}
                  </div>
              </div>
            </main>
        </div>
    </div>
  );
}
