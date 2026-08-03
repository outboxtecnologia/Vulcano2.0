import { useNavigate, useRouteError } from 'react-router';
import { AlertCircle } from 'lucide-react';

/**
 * errorElement das rotas de view: o crash fica contido no <Outlet/>, entao sidebar e
 * topbar continuam de pe e da para sair da tela quebrada clicando em outra.
 *
 * Antes, o unico anteparo era o GlobalErrorBoundary do main.jsx, que substitui a
 * pagina inteira — e o botao "tentar novamente" dele so limpa o estado de erro e
 * re-renderiza o mesmo dado ruim, quebrando de novo.
 */
export default function ViewErrorBoundary() {
  const erro = useRouteError();
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col items-center justify-center py-24 text-center gap-4">
      <AlertCircle size={44} className="text-[var(--v-error)]" />
      <h2 className="font-headline text-2xl font-black tracking-widest uppercase" style={{ color: 'var(--v-text-bold)' }}>
        Esta tela quebrou
      </h2>
      <p className="text-[11px] max-w-xl font-mono break-words" style={{ color: 'var(--v-text-faint)' }}>
        {erro?.message || String(erro)}
      </p>
      <div className="flex gap-3 mt-4">
        <button
          onClick={() => navigate(0)}
          className="px-6 py-2 border border-[var(--v-line)] text-[9px] font-black uppercase tracking-widest transition-all hover:border-[var(--v-accent)]"
          style={{ color: 'var(--v-text-muted)' }}
        >
          Recarregar
        </button>
        <button
          onClick={() => navigate('..', { relative: 'path' })}
          className="px-6 py-2 bg-[rgb(var(--v-accent-rgb)_/_0.1)] text-[var(--v-accent)] text-[9px] font-black uppercase tracking-widest border border-[var(--v-accent)]/20"
        >
          Voltar
        </button>
      </div>
      {erro?.stack && (
        <pre className="mt-6 max-w-3xl max-h-64 overflow-auto text-left text-[10px] p-4 rounded-[var(--v-radius)] bg-[var(--v-scrim)] border border-[var(--v-line)]"
             style={{ color: 'var(--v-text-faint)' }}>
          {erro.stack}
        </pre>
      )}
    </div>
  );
}
