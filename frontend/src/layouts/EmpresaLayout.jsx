import { useState } from 'react';
import { NavLink, Navigate, Outlet, useLocation, useMatch, useNavigate, useParams } from 'react-router';
import {
  Bell, ChevronRight, Cpu, Database, Download, Plus, Search,
} from 'lucide-react';
import { useEmpresas } from '../context/EmpresasContext';
import { useTheme } from '../context/ThemeContext';
import { NAV_SECTIONS, DEFAULT_SLUG, rewriteTailForEmpresa } from '../routes/navigation';

const NavItem = ({ icon, label, to, isSidebarOpen = true }) => (
  <NavLink
    to={to}
    title={!isSidebarOpen ? label : undefined}
    className={({ isActive }) =>
      // Antes estas classes vinham do design system Material (--color-*), que respondia
      // a classe `dark` em vez do data-theme — no tema claro resolviam para branco sobre
      // a sidebar escura. Os tokens abaixo tem os MESMOS valores no dark.
      `w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-200 ease-in-out border-l-2 outline-none ${
        isActive
          ? 'text-[var(--v-nav-active)] border-[var(--v-nav-active)] bg-[var(--v-deep)] font-bold shadow-[inset_4px_0_0_0_var(--v-nav-bar)]'
          : 'text-[var(--v-text-soft)] border-transparent hover:text-[var(--v-text-hi)] hover:bg-[var(--v-hover-soft)]'
      } ${!isSidebarOpen ? 'justify-center px-0' : ''}`
    }
  >
    {({ isActive }) => (
      <>
        <span className={isActive ? 'text-[var(--v-nav-active)]' : 'opacity-70'}>{icon}</span>
        {isSidebarOpen && <span className="truncate">{label}</span>}
      </>
    )}
  </NavLink>
);

/**
 * Shell autenticado: sidebar + topbar + <Outlet/> das views.
 *
 * Tambem e o guard da empresa. A ordem das checagens importa: enquanto a lista
 * carrega NAO se redireciona, senao todo F5 em /empresa/959/vendas cairia em
 * /empresas antes de a lista chegar.
 */
export default function EmpresaLayout() {
  const { empresaId } = useParams();
  const { empresas, loading, error, loadingSlow, reload, findEmpresa } = useEmpresas();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const match = useMatch('/empresa/:empresaId/*');

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [search, setSearch] = useState('');

  const empresa = findEmpresa(empresaId);

  if (loading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-4 immersive-bg" style={{ background: 'var(--v-shell)' }}>
        <Cpu size={32} className="text-[var(--v-accent)] animate-pulse" />
        <p className="text-[10px] font-black uppercase tracking-[0.4em]" style={{ color: 'var(--v-text-muted)' }}>
          Carregando nodes
        </p>
        {loadingSlow && (
          <p className="text-[10px] tracking-[0.2em] uppercase" style={{ color: 'var(--v-text-faint)' }}>
            O backend está demorando mais que o normal…
          </p>
        )}
      </div>
    );
  }

  // Backend fora do ar nao deve expulsar da tela: segue com o id da URL como rotulo.
  if (!error && !empresa) {
    return <Navigate to="/empresas" replace state={{ notFound: empresaId }} />;
  }

  const empresaAtual = empresa || { id: empresaId, nome: empresaId };

  const handleTrocaEmpresa = (nextId) => {
    const tail = match?.params['*'] || DEFAULT_SLUG;
    const { path, search: qs } = rewriteTailForEmpresa(tail, location.search);
    navigate(`/empresa/${nextId}/${path}${qs}`);
  };

  const handleRunSQL = () => alert('SQL Execution triggered for environment: ' + empresaId);

  return (
    /* Sem data-theme aqui: o atributo mora no <html> (ThemeContext); re-ancorar a
       cascata no meio da arvore criaria um segundo dono do tema. */
    <div className="font-body selection:bg-[rgb(var(--v-accent-rgb)_/_0.3)] flex h-screen overflow-hidden transition-colors duration-300 immersive-bg"
         style={{ color: 'var(--v-text)', background: 'var(--v-shell)' }}>
        <div className="absolute inset-0 backdrop-blur-[1px] z-0"
             style={{ background: 'var(--v-blur-bg)' }}></div>

        {/* Lado Esquerdo - Stitch SideNavBar */}
        <aside className={`fixed left-0 top-0 h-full ${isSidebarOpen ? 'w-64' : 'w-20'} z-[60] flex flex-col py-6 transition-all duration-300 ease-in-out`}
               style={{
                 background: 'var(--v-shell)',
                 backdropFilter: 'blur(24px)',
                 WebkitBackdropFilter: 'blur(24px)',
                 borderRight: '1px solid var(--v-shell-border)'
               }}>

            {/* Toggle Button */}
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="absolute top-16 -right-3 w-6 h-6 flex items-center justify-center bg-[var(--v-card)] border border-[var(--v-border)] rounded-full text-[var(--v-text-muted)] cursor-pointer z-50 shadow-md hover:text-[var(--v-accent)] transition-all"
            >
              <ChevronRight size={14} className={`transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
            </button>

            <div className={`px-6 mb-10 flex items-center ${isSidebarOpen ? 'gap-3' : 'justify-center px-0'}`}>
                <div className="w-8 h-8 shrink-0 bg-[var(--v-accent)] rounded-[var(--v-radius)] flex items-center justify-center shadow-[0_0_15px_var(--v-accent-glow)]">
                  <Cpu size={18} className="text-[var(--v-text-inv)]" />
                </div>
                {isSidebarOpen && (
                  <div className="whitespace-nowrap overflow-hidden">
                     <h1 className="font-headline font-black text-xl tracking-tighter leading-none" style={{ color: 'var(--v-text-bold)' }}>VULCANO</h1>
                     <p className="text-[9px] tracking-[0.2em] uppercase mt-1 font-black" style={{ color: 'var(--v-accent)' }}>CONTÁBIL · 2.0</p>
                  </div>
                )}
            </div>

            <nav className="flex-1 overflow-y-auto w-full no-scrollbar px-3 space-y-8">
                {NAV_SECTIONS.map((section, i) => (
                  <div key={section.title} className={i === 0 ? 'space-y-1' : 'space-y-1 border-t border-[var(--v-line)] pt-6'}>
                      {isSidebarOpen && (
                        <h3 className="text-[10px] font-black opacity-60 uppercase tracking-[0.3em] pl-3 mb-3" style={{ color: 'var(--v-text-muted)' }}>
                          {section.title}
                        </h3>
                      )}
                      {section.items.map((item) => (
                        <NavItem
                          key={item.slug}
                          isSidebarOpen={isSidebarOpen}
                          icon={<item.icon size={16} />}
                          label={item.label}
                          to={`/empresa/${empresaId}/${item.slug}`}
                        />
                      ))}
                  </div>
                ))}
            </nav>
            <div className="px-4 mt-auto">
                <button className={`w-full bg-[var(--v-cta)] text-[var(--v-text-inv)] py-4 rounded-[var(--v-radius)] font-black uppercase tracking-[0.1em] flex items-center justify-center transition-all shadow-[0_0_20px_var(--v-accent-glow-soft)] ${isSidebarOpen ? 'text-[12px]' : 'text-transparent'}`}
                        title="NOVA OBRA">
                    <Plus size={16} className={isSidebarOpen ? "mr-2" : "text-[var(--v-text-inv)]"} /> {isSidebarOpen && "NOVA OBRA"}
                </button>
            </div>
        </aside>

        {/* Global Wrapper para TopNav + Content */}
        <div className={`${isSidebarOpen ? 'ml-64' : 'ml-20'} flex-1 flex flex-col h-full bg-transparent transition-all duration-300 relative z-10 w-full overflow-hidden`}>

            {/* TopNavBar Stitch Design */}
            <header className="h-16 flex items-center justify-between px-8 backdrop-blur-2xl shrink-0 z-50 transition-colors"
                    style={{
                      borderBottom: '1px solid var(--v-shell-border)',
                      background: 'var(--v-shell)'
                    }}>
                <div className="flex items-center gap-4 flex-1">
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 transition-colors" size={16}
                                style={{ color: 'var(--v-text-faint)' }} />
                        <input
                            className="text-xs rounded-[var(--v-radius)] pl-10 pr-4 py-2 w-96 outline-none transition-all"
                            style={{
                              background: 'var(--v-card)',
                              border: '1px solid var(--v-shell-border)',
                              color: 'var(--v-text)',
                            }}
                            placeholder="Pesquisar no Cortex Index..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    {error && (
                      <button onClick={reload}
                              className="text-[10px] font-black uppercase tracking-[0.15em] px-3 py-2 rounded-[var(--v-radius)] border border-red-500/40 text-red-300 hover:bg-red-500/10 transition-all"
                              title={error}>
                        Sem conexão · recarregar
                      </button>
                    )}
                    <div className="flex items-center gap-2 px-4 py-2 rounded-[var(--v-radius)] shadow-sm transition-colors"
                         style={{ background: 'var(--v-card)', border: '1px solid var(--v-shell-border)' }}>
                        <Database size={12} className="text-[var(--v-accent)] shrink-0" />
                        {empresas.length > 0 ? (
                          <select
                              value={String(empresaId)}
                              onChange={(e) => handleTrocaEmpresa(e.target.value)}
                              className="border-none outline-none text-[10px] w-52 font-black uppercase tracking-[0.2em] cursor-pointer appearance-none truncate bg-transparent"
                              style={{ color: 'var(--v-text)' }}
                          >
                              {empresas.map(emp => (
                                  <option key={emp.id} value={String(emp.id)} style={{ background: 'var(--v-card)', color: 'var(--v-text)' }}>
                                      {emp.id} - {emp.nome}
                                  </option>
                              ))}
                          </select>
                        ) : (
                          <span className="text-[10px] w-52 font-black uppercase tracking-[0.2em] truncate" style={{ color: 'var(--v-text)' }}>
                            {empresaAtual.id} - {empresaAtual.nome}
                          </span>
                        )}
                    </div>

                    <div className="flex items-center gap-4 h-full">
                        <div className="h-8 w-[1px] bg-[var(--v-line)]"></div>
                        <select value={theme} onChange={(e) => setTheme(e.target.value)}
                                className="px-2 py-1 outline-none font-bold text-[10px] cursor-pointer uppercase transition-all rounded-[var(--v-radius)]"
                                style={{ color: 'var(--v-text-bold)', border: '1px solid var(--v-shell-border)', background: 'var(--v-card)' }}>
                            <option value="dark">DARK</option>
                            <option value="light">LIGHT</option>
                        </select>
                        <button onClick={handleRunSQL} className="hover:text-[var(--v-accent)] transition-all relative" style={{ color: 'var(--v-text-faint)' }}><Download size={18}/></button>
                        <button className="hover:text-[var(--v-accent)] transition-all relative" style={{ color: 'var(--v-text-faint)' }}>
                            <Bell size={18} />
                            <span className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--v-accent)] rounded-[var(--v-radius)] shadow-[0_0_8px_var(--v-accent)]"></span>
                        </button>
                        <NavLink to="/empresas" title="Trocar de node"
                                 className="h-8 w-8 rounded-[var(--v-radius)] bg-[var(--v-accent-soft)] overflow-hidden ml-2 border border-[var(--v-accent-border)] p-[2px] block">
                            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${empresaId || 'Vulcano'}`} alt="User" className="w-full h-full object-cover rounded-[var(--v-radius)]" />
                        </NavLink>
                    </div>
                </div>
            </header>


            {/* MAIN CONTENT AREA */}
            <main className="flex-1 overflow-x-hidden overflow-y-auto transition-colors p-8 relative custom-scrollbar"
                  style={{ background: 'transparent' }}>
              {/* Removida a div do glow ambiente: era um blur de 1000x1000px pintado
                  com --v-magma-glow, variavel que nunca foi definida em tema nenhum.
                  Renderizava transparente desde sempre. */}
              <div className="max-w-[1920px] mx-auto min-h-full flex flex-col">
                  <div className="w-full h-full">
                      <Outlet context={{ empresaId, empresa: empresaAtual, empresas }} />
                  </div>
              </div>
            </main>
        </div>
    </div>
  );
}
