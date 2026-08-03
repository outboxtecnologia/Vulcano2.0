import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';

/**
 * Indicador de ordenacao do cabecalho.
 *
 * Renderiza SEMPRE, mesmo na coluna inativa (ali com opacidade zero, revelada no
 * hover do cabecalho). Se o icone entrasse e saisse do fluxo, o cabecalho pularia
 * alguns pixels a cada hover e a cada clique.
 *
 * O `group-hover` depende da classe `group` no elemento clicavel do cabecalho.
 */
export default function SortIcon({ active, dir }) {
  if (active) {
    const Icone = dir === 'desc' ? ArrowDown : ArrowUp;
    return <Icone size={10} className="shrink-0 text-[var(--v-accent)]" aria-hidden="true" />;
  }
  return (
    <ChevronsUpDown
      size={10}
      aria-hidden="true"
      className="shrink-0 text-[var(--v-text-ghost)] opacity-0 group-hover:opacity-60 transition-opacity"
    />
  );
}
