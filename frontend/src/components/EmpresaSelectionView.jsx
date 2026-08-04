import React, { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import Lenis from 'lenis';
import LavaBackground from '../LavaBackground';
import { Search, LogOut } from 'lucide-react';
import '../EmpresaSelectionView.css';

export default function EmpresaSelectionView({ globalEmpresas, onSelectEmpresa, onLogout }) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [sort, setSort] = useState('vgv');
  const [selectedNode, setSelectedNode] = useState(null);
  
  const cursorRef = useRef(null);
  const railRef = useRef(null);
  const railBackRef = useRef(null);
  const lenisRef = useRef(null);
  const magElementsRef = useRef(new WeakSet());

  // Decorate globalEmpresas with mock/fallback data if not present, to match the design aesthetics
  const decoratedEmpresas = globalEmpresas.map(e => ({
    ...e,
    tipo: e.nome.toLowerCase().includes('incorporadora') || e.nome.toLowerCase().includes('empreendimento') ? 'incorporacao' :
          e.nome.toLowerCase().includes('holding') ? 'holding' : 'construcao',
    vgv: e.vgv || Math.floor(Math.random() * 1000000000),
    contratos: e.contratos || Math.floor(Math.random() * 500),
    alertas: e.alertas !== undefined ? e.alertas : Math.floor(Math.random() * 3),
    updated: e.updated || 'há pouco',
    cnpj: e.cnpj || '00.000.000/0000-00',
  }));

  const RECENT_IDS = decoratedEmpresas.slice(0, 4).map(e => e.id);

  // Sorting and filtering
  let filteredList = decoratedEmpresas.filter(c => {
    if (filter !== 'all' && c.tipo !== filter) return false;
    const q = query.toLowerCase();
    if (q && !(c.nome.toLowerCase().includes(q) || c.cnpj.includes(q) || c.id.toString().toLowerCase().includes(q))) return false;
    return true;
  });

  if (sort === 'vgv') filteredList.sort((a,b) => b.vgv - a.vgv);
  if (sort === 'alpha') filteredList.sort((a,b) => a.nome.localeCompare(b.nome));

  // Magnetic cursor bind
  useEffect(() => {
    const bindMagnetic = () => {
      document.querySelectorAll('.mag').forEach(el => {
        if (magElementsRef.current.has(el)) return;
        magElementsRef.current.add(el);
        const strength = parseFloat(el.dataset.mag || '14');
        const inner = el.querySelector('.mag-inner') || el;
        
        const onMouseMove = (e) => {
          const r = el.getBoundingClientRect();
          const x = e.clientX - (r.left + r.width/2);
          const y = e.clientY - (r.top + r.height/2);
          const dx = (x / r.width) * strength * 2;
          const dy = (y / r.height) * strength * 2;
          gsap.to(el, { x: dx*0.5, y: dy*0.5, duration:.4, ease:'power3.out' });
          gsap.to(inner, { x: dx, y: dy, duration:.4, ease:'power3.out' });
          if (el.classList.contains('node')) {
            el.style.setProperty('--mx', ((e.clientX - r.left)/r.width)*100 + '%');
            el.style.setProperty('--my', ((e.clientY - r.top)/r.height)*100 + '%');
          }
        };
        const onMouseLeave = () => {
          gsap.to(el, { x:0, y:0, duration:.55, ease:'elastic.out(1,.6)' });
          gsap.to(inner, { x:0, y:0, duration:.55, ease:'elastic.out(1,.6)' });
        };
        
        el.addEventListener('mousemove', onMouseMove);
        el.addEventListener('mouseleave', onMouseLeave);
      });
    };
    bindMagnetic();
  });

  // Init GSAP & Lenis
  useEffect(() => {
    const lenis = new Lenis({ duration: 1.2, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), smoothWheel: true });
    lenisRef.current = lenis;

    // A MESMA referencia precisa ir para o add e para o remove: gsap.ticker.remove()
    // faz indexOf na lista interna, entao uma arrow nova nunca casa e o callback fica
    // preso no ticker para sempre. Como esta tela virou rota, isso acumularia um loop
    // de raf() por visita, chamando um Lenis ja destruido.
    const rafFn = (time) => { lenis.raf(time * 1000); };
    gsap.ticker.add(rafFn);
    gsap.ticker.lagSmoothing(0);

    lenis.on('scroll', ({ scroll, velocity }) => {
      if (window.__threeUniforms) window.__threeUniforms.uScroll.value = velocity * 60;
      const max = document.body.scrollHeight - window.innerHeight;
      const progressBar = document.getElementById('progressBar');
      if (progressBar) progressBar.style.width = Math.max(0, Math.min(1, scroll / max)) * 100 + '%';
    });

    const onPointerMove = (e) => {
      if (cursorRef.current) gsap.to(cursorRef.current, { left: e.clientX, top: e.clientY, duration: .18, ease: 'power3.out' });
    };
    window.addEventListener('pointermove', onPointerMove);

    gsap.utils.toArray('.r-init').forEach(el => {
      gsap.to(el, { opacity: 1, y: 0, duration: 1, ease: 'power3.out', delay: 0.2 });
    });

    // Loader Curtain
    const lbar = document.getElementById('lbar');
    let prog = 0;
    const ticker = setInterval(() => {
      prog = Math.min(100, prog + 8 + Math.random() * 14);
      if (lbar) lbar.style.width = prog + '%';
      if (prog >= 100) {
        clearInterval(ticker);
        setTimeout(() => {
          const curtain = document.getElementById('curtain');
          if (curtain) curtain.classList.add('hidden');
        }, 250);
      }
    }, 110);

    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      // Remover do ticker ANTES de destruir o lenis, senao o ultimo frame chama raf()
      // num objeto ja destruido.
      gsap.ticker.remove(rafFn);
      lenis.destroy();
      gsap.ticker.lagSmoothing(1000, 16); // restaura o default do GSAP (era global)
      clearInterval(ticker);
    };
  }, []);

  const handleCursorEnter = () => cursorRef.current?.classList.add('expand');
  const handleCursorLeave = () => cursorRef.current?.classList.remove('expand');

  const openRail = (nodeId) => {
    const node = decoratedEmpresas.find(e => e.id.toString() === nodeId.toString());
    if (node) {
      setSelectedNode(node);
      railRef.current?.classList.add('open');
      railBackRef.current?.classList.add('open');
    }
  };

  const closeRail = () => {
    railRef.current?.classList.remove('open');
    railBackRef.current?.classList.remove('open');
    setTimeout(() => setSelectedNode(null), 400); // clear after animation
  };

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape') closeRail();
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const fmtBi = (v) => v >= 1e9 ? 'R$ ' + (v / 1e9).toFixed(2).replace('.', ',') + ' Bi' : v >= 1e6 ? 'R$ ' + (v / 1e6).toFixed(0) + ' Mi' : v > 0 ? 'R$ ' + v.toLocaleString('pt-BR') : '—';
  
  const highlight = (text, q) => {
    if (!q) return text;
    const parts = text.split(new RegExp(`(${q})`, 'gi'));
    return parts.map((part, i) => part.toLowerCase() === q.toLowerCase() ? <mark key={i}>{part}</mark> : part);
  };

  return (
    /* Escura por design, como o login: o CSS proprio nao usa as variaveis de tema. */
    <div className="empresa-selection-wrapper" data-theme="dark">
      <LavaBackground />
      <div className="vignette"></div>
      <div className="grain"></div>

      <div className="curtain" id="curtain">
        <div className="text-center">
          <div className="lt">CARREGANDO ECOSSISTEMA</div>
          <div className="lb"><i id="lbar" style={{ width: '0%' }}></i></div>
        </div>
      </div>

      <div className="progress-bar" id="progressBar"></div>
      <div id="cursor" ref={cursorRef}></div>

      <header className="relative z-30 flex items-center justify-between px-7 py-5 r-init">
        <div className="flex items-center gap-3 mag" data-mag="6" style={{ textDecoration: 'none', color: 'inherit' }} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
          <span className="mag-inner flex items-center gap-3">
            <div className="w-12 h-12 rounded-[11px] flex items-center justify-center font-bold text-lg" style={{ background: 'radial-gradient(circle at 30% 30%, rgba(255,200,120,0.55), transparent 60%), linear-gradient(135deg, #ff8a2a 0%, #c93a12 60%, #4a1206 100%)', boxShadow: '0 0 24px rgba(255,122,26,0.55), inset 0 0 0 1px rgba(255,180,90,0.18)', color: '#1a0a04' }}>V</div>
            <span>
              <span className="block font-display font-bold text-[15px] tracking-wide whitespace-nowrap">ARQUIVO VULCANO</span>
              <span className="block font-mono text-[9.5px] text-[#FF8A2A] tracking-[0.24em] mt-0.5">CONTÁBIL · 2.0</span>
            </span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-6 font-mono text-[10px] tracking-[0.2em] text-[#F0E6D8]/80">
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#3dd68c] pulse-dot"></span>
            ECOSSISTEMA · ONLINE
          </span>
          <span>NODES: <span className="text-[#F0E6D8]">{globalEmpresas.length}</span></span>
          <span className="hidden lg:inline">SP · BR</span>
          <button onClick={onLogout} className="ml-2 mag text-[#F0E6D8]/60 hover:text-[#FF8A2A] transition flex items-center gap-2" data-mag="10" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
            <span className="mag-inner flex items-center gap-2">
              <LogOut size={13} strokeWidth={1.6} />
              SAIR
            </span>
          </button>
        </div>
      </header>

      <section className="relative z-20 px-7 pt-10 pb-8 max-w-[1380px] mx-auto">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-8 r-init">
          <div>
            <div className="font-mono text-[10px] text-[#FF8A2A] tracking-[0.36em] mb-3 flex items-center gap-3">
              <span className="w-6 h-px bg-[#FF8A2A]"></span>
              ECOSSISTEMA · MULTI-EMPRESAS
            </div>
            <h1 className="font-display font-semibold text-[clamp(38px,4.6vw,60px)] leading-[1] tracking-[-0.015em]">Empresas do grupo</h1>
            <div className="font-mono text-[10.5px] tracking-[0.18em] text-[#F0E6D8]/55 mt-3">
              <span>{filteredList.length}</span> NODES · ORDEM POR <span className="text-[#FF8A2A]">{sort.toUpperCase()}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 font-mono text-[10px] tracking-[0.18em] text-[#F0E6D8]/65 shrink-0">
            <button className={`px-3 py-1.5 rounded border ${sort === 'vgv' ? 'border-[#FF8A2A]/40 text-[#FF8A2A]' : 'border-[#FF8A2A]/20 hover:text-[#FF8A2A] hover:border-[#FF8A2A]/40'} transition`} onClick={() => setSort('vgv')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>VGV</button>
            <button className={`px-3 py-1.5 rounded border ${sort === 'alpha' ? 'border-[#FF8A2A]/40 text-[#FF8A2A]' : 'border-[#FF8A2A]/20 hover:text-[#FF8A2A] hover:border-[#FF8A2A]/40'} transition`} onClick={() => setSort('alpha')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>A-Z</button>
            <button className={`px-3 py-1.5 rounded border ${sort === 'updated' ? 'border-[#FF8A2A]/40 text-[#FF8A2A]' : 'border-[#FF8A2A]/20 hover:text-[#FF8A2A] hover:border-[#FF8A2A]/40'} transition`} onClick={() => setSort('updated')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>RECENTE</button>
          </div>
        </div>

        <div className="r-init">
          <div className={`search-wrap relative flex items-center bg-black/40 border border-[#FF8A2A]/15 rounded-2xl px-6 py-4`}>
            <Search size={18} strokeWidth={1.7} className="text-[#F0E6D8]/55 shrink-0" />
            <input 
              id="searchInput" type="text" placeholder="Buscar empresa, CNPJ ou node…" 
              className="bg-transparent outline-none border-none w-full ml-3 text-[#F0E6D8] placeholder:text-[#F0E6D8]/40 text-[15px] font-sans"
              value={query} onChange={e => setQuery(e.target.value)}
              onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}
            />
            <kbd className="hidden md:inline font-mono text-[10px] text-[#F0E6D8]/55 border border-[#FF8A2A]/15 rounded px-1.5 py-0.5">⌘K</kbd>
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-5">
            <button className="chip font-mono text-[10px] tracking-[0.18em] uppercase px-3.5 py-1.5 rounded-full border border-[#FF8A2A]/20 text-[#F0E6D8]/75" data-active={filter === 'all'} onClick={() => setFilter('all')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>Todas <span className="text-[#FF8A2A] ml-1">{decoratedEmpresas.length}</span></button>
            <button className="chip font-mono text-[10px] tracking-[0.18em] uppercase px-3.5 py-1.5 rounded-full border border-[#FF8A2A]/20 text-[#F0E6D8]/75" data-active={filter === 'construcao'} onClick={() => setFilter('construcao')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>Construção</button>
            <button className="chip font-mono text-[10px] tracking-[0.18em] uppercase px-3.5 py-1.5 rounded-full border border-[#FF8A2A]/20 text-[#F0E6D8]/75" data-active={filter === 'incorporacao'} onClick={() => setFilter('incorporacao')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>Incorporação</button>
            <button className="chip font-mono text-[10px] tracking-[0.18em] uppercase px-3.5 py-1.5 rounded-full border border-[#FF8A2A]/20 text-[#F0E6D8]/75" data-active={filter === 'holding'} onClick={() => setFilter('holding')} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>Holding</button>
          </div>
        </div>
      </section>

      {!query && filter === 'all' && RECENT_IDS.length > 0 && (
        <section className="relative z-20 px-7 pt-6 max-w-[1380px] mx-auto r-init">
          <div className="font-mono text-[10px] tracking-[0.28em] text-[#F0E6D8]/65 flex items-center gap-3 mb-4">
            <span className="w-6 h-px bg-[#FF8A2A]"></span> ACESSADAS RECENTEMENTE
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {RECENT_IDS.map(id => {
              const c = decoratedEmpresas.find(e => e.id === id);
              if (!c) return null;
              return (
                <button key={'recent-'+c.id} className="recent-tile node mag text-left p-5" data-mag="10" style={{ minHeight: '120px' }} onClick={() => openRail(c.id)} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-8 h-8 rounded flex items-center justify-center font-mono font-semibold text-[10px]" style={{ background: 'linear-gradient(135deg,rgba(255,138,42,0.22),rgba(201,58,18,0.10))', border: '1px solid rgba(255,140,42,0.28)', color: '#ffd28a' }}>{c.id}</div>
                    <span className="font-mono text-[9px] tracking-[0.18em] text-[#F0E6D8]/40">{c.updated.toUpperCase()}</span>
                  </div>
                  <div className="font-display text-[13px] leading-[1.25] text-[#F0E6D8]" style={{ textWrap: 'pretty' }}>{c.nome}</div>
                  <div className="font-mono text-[9px] tracking-[0.22em] text-[#F0E6D8]/45 mt-2">{fmtBi(c.vgv)} · {c.contratos} contratos</div>
                </button>
              );
            })}
          </div>
        </section>
      )}

      <section className="relative z-20 px-7 pt-12 pb-16 max-w-[1380px] mx-auto">
        <div className="font-mono text-[10px] tracking-[0.28em] text-[#F0E6D8]/65 flex items-center gap-3 mb-4 r-init">
          <span className="w-6 h-px bg-[#FF8A2A]"></span> TODOS OS NODES
        </div>

        {filteredList.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredList.map(c => (
              <div key={c.id} className="node mag p-5 r-init" data-mag="10" style={{ minHeight: '140px', opacity: 1, transform: 'translateY(0)' }} onClick={() => openRail(c.id)} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center font-mono font-semibold text-[11px]" style={{ background: 'linear-gradient(135deg,rgba(255,138,42,0.22),rgba(201,58,18,0.10))', border: '1px solid rgba(255,140,42,0.28)', color: '#ffd28a', letterSpacing: '0.04em' }}>{c.id}</div>
                  <svg className="arrow text-[#F0E6D8]/45" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M7 17L17 7M7 7h10v10" /></svg>
                </div>
                <div className="font-mono text-[9px] tracking-[0.26em] text-[#FF8A2A] mb-1.5">{c.tipo === 'incorporacao' ? 'INCORPORAÇÃO' : c.tipo === 'holding' ? 'HOLDING' : 'CONSTRUÇÃO'}</div>
                <h3 className="font-display font-semibold text-[14px] leading-[1.25] text-[#F0E6D8]" style={{ textWrap: 'pretty' }}>{highlight(c.nome, query)}</h3>
                <div className="ember-line"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <div className="font-mono text-[11px] tracking-[0.3em] text-[#FF8A2A]">NENHUM NODE ENCONTRADO</div>
            <div className="text-[#F0E6D8]/60 mt-2 text-sm">Ajuste a busca ou os filtros acima.</div>
          </div>
        )}
      </section>

      <section className="relative z-20 px-7 pb-24 max-w-[1380px] mx-auto">
        <div className="grid md:grid-cols-3 gap-5">
          <div className="r-init bg-[#070506]/65 border border-[#FF8A2A]/15 rounded-2xl p-7 ring-glow" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
            <div className="font-mono text-[10px] tracking-[0.28em] text-[#FF8A2A] mb-3">+ NOVA EMPRESA</div>
            <h3 className="font-display text-xl font-semibold mb-2">Adicione um node ao seu vulcão.</h3>
            <p className="text-sm text-[#F0E6D8]/70 leading-relaxed mb-5">Onboarding guiado: ERP, plano de contas, política CPC 47 e governança em 4 passos.</p>
            <button className="mag font-mono text-[11px] tracking-[0.22em] text-[#FF8A2A] hover:text-[#FFB000] transition" data-mag="10">
              <span className="mag-inner">INICIAR ONBOARDING →</span>
            </button>
          </div>
          <div className="r-init bg-[#070506]/65 border border-[#FF8A2A]/15 rounded-2xl p-7 ring-glow" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
            <div className="font-mono text-[10px] tracking-[0.28em] text-[#FF8A2A] mb-3">DOCUMENTAÇÃO</div>
            <h3 className="font-display text-xl font-semibold mb-2">Como modelar grupos econômicos.</h3>
            <p className="text-sm text-[#F0E6D8]/70 leading-relaxed mb-5">Hierarquias, holdings, SCPs e consolidações — guia técnico do Vulcano.</p>
            <button className="mag font-mono text-[11px] tracking-[0.22em] text-[#FF8A2A] hover:text-[#FFB000] transition" data-mag="10">
              <span className="mag-inner">ABRIR DOCS →</span>
            </button>
          </div>
          <div className="r-init bg-[#070506]/65 border border-[#FF8A2A]/15 rounded-2xl p-7 ring-glow" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
            <div className="font-mono text-[10px] tracking-[0.28em] text-[#FF8A2A] mb-3">SUPORTE 24/7</div>
            <h3 className="font-display text-xl font-semibold mb-2">Time de geólogos contábeis.</h3>
            <p className="text-sm text-[#F0E6D8]/70 leading-relaxed mb-5">Falar com um analista sênior em até 4 minutos — chat ou voz.</p>
            <button className="mag font-mono text-[11px] tracking-[0.22em] text-[#FF8A2A] hover:text-[#FFB000] transition" data-mag="10">
              <span className="mag-inner">CHAMAR ANALISTA →</span>
            </button>
          </div>
        </div>
      </section>

      <footer className="relative z-20 border-t border-[#FF8A2A]/10 py-5 px-7 flex flex-col md:flex-row items-center justify-between gap-3 font-mono text-[10px] tracking-[0.2em] text-[#F0E6D8]/55">
        <span>© 2026 VULCANO · LGPD · ISO 27001 · SOC 2 TYPE II</span>
        <div className="flex gap-5">
          <button onClick={onLogout} className="hover:text-[#FF8A2A] transition" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>VOLTAR AO LOGIN</button>
          <button className="hover:text-[#FF8A2A] transition" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>PRIVACIDADE</button>
          <button className="hover:text-[#FF8A2A] transition" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>CONTATO</button>
        </div>
      </footer>

      {/* Detail rail */}
      <div className="rail-back" id="railBack" ref={railBackRef} onClick={closeRail}></div>
      <aside className="rail" id="rail" ref={railRef}>
        <div className="p-7">
          {selectedNode && (
            <>
              <div className="flex items-start justify-between mb-7">
                <div className="font-mono text-[10px] tracking-[0.32em] text-[#FF8A2A]">NODE · {selectedNode.id}</div>
                <button className="text-[#F0E6D8]/55 hover:text-[#FF8A2A] text-2xl leading-none" onClick={closeRail} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>×</button>
              </div>
              <div className="w-14 h-14 rounded-xl mb-5 flex items-center justify-center font-mono font-semibold text-[14px]" style={{ background: 'linear-gradient(135deg,rgba(255,138,42,0.28),rgba(201,58,18,0.14))', border: '1px solid rgba(255,140,42,0.35)', color: '#ffd28a' }}>
                {selectedNode.id}
              </div>
              <div className="font-mono text-[9.5px] tracking-[0.22em] text-[#FF8A2A] mb-2">{selectedNode.tipo === 'incorporacao' ? 'INCORPORAÇÃO' : selectedNode.tipo === 'holding' ? 'HOLDING' : 'CONSTRUÇÃO'}</div>
              <h2 className="font-display text-[26px] leading-[1.15] font-semibold tracking-[-0.01em] mb-2" style={{ textWrap: 'pretty' }}>{selectedNode.nome}</h2>
              <div className="font-mono text-[10.5px] text-[#F0E6D8]/50 mb-7">{selectedNode.cnpj}</div>

              <div className="space-y-3 mb-7">
                <div className="flex items-baseline justify-between border-b border-[#FF8A2A]/10 pb-3">
                  <span className="font-mono text-[9.5px] tracking-[0.22em] text-[#F0E6D8]/55">VGV CONSOLIDADO</span>
                  <span className="font-display text-[18px] font-semibold" style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtBi(selectedNode.vgv)}</span>
                </div>
                <div className="flex items-baseline justify-between border-b border-[#FF8A2A]/10 pb-3">
                  <span className="font-mono text-[9.5px] tracking-[0.22em] text-[#F0E6D8]/55">CONTRATOS ATIVOS</span>
                  <span className="font-display text-[18px] font-semibold" style={{ fontVariantNumeric: 'tabular-nums' }}>{selectedNode.contratos.toLocaleString('pt-BR')}</span>
                </div>
                <div className="flex items-baseline justify-between border-b border-[#FF8A2A]/10 pb-3">
                  <span className="font-mono text-[9.5px] tracking-[0.22em] text-[#F0E6D8]/55">EXCEÇÕES ABERTAS</span>
                  <span className={`font-display text-[18px] font-semibold ${selectedNode.alertas > 0 ? 'text-[#FF8A2A]' : 'text-emerald-400'}`} style={{ fontVariantNumeric: 'tabular-nums' }}>{selectedNode.alertas}</span>
                </div>
                <div className="flex items-baseline justify-between border-b border-[#FF8A2A]/10 pb-3">
                  <span className="font-mono text-[9.5px] tracking-[0.22em] text-[#F0E6D8]/55">ÚLT. SINCRONIA</span>
                  <span className="font-mono text-[12px] text-[#F0E6D8]/85">{selectedNode.updated}</span>
                </div>
              </div>

              <button className="mag block w-full text-center font-display font-semibold py-4 rounded-xl text-[14px]" style={{ background: 'linear-gradient(135deg,#ff8a2a,#c93a12)', color: '#1a0a04', boxShadow: '0 10px 30px rgba(201,58,18,0.4),inset 0 1px 0 rgba(255,220,180,0.4)' }} data-mag="6" onClick={() => onSelectEmpresa(selectedNode.id.toString())} onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>
                <span className="mag-inner">ENTRAR NO NODE →</span>
              </button>
              <button className="mt-3 w-full text-center font-mono text-[10px] tracking-[0.22em] text-[#F0E6D8]/55 hover:text-[#FF8A2A] py-3 rounded-xl border border-[#FF8A2A]/15 transition" onMouseEnter={handleCursorEnter} onMouseLeave={handleCursorLeave}>VISUALIZAR HIERARQUIA</button>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}
