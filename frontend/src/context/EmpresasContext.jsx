import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { API_BASE } from '../apiBase';

/**
 * Lista de empresas (nodes) disponiveis.
 *
 * Montado dentro do <RequireAuth>, entao o fetch nao roda mais antes do login — antes
 * disparava no mount do App, com deps [], independente de autenticacao. Fica acima de
 * /empresas e de /empresa/:id, entao ir e voltar entre a selecao e o shell nao refaz
 * a chamada.
 */
const EmpresasContext = createContext(null);

export function EmpresasProvider({ children }) {
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingSlow, setLoadingSlow] = useState(false); // true se passar de 4s
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const ac = new AbortController();
    const slowTimer = setTimeout(() => setLoadingSlow(true), 4000);

    // loading/error ja comecam no valor certo; quem os rearma e o reload().
    fetch(`${API_BASE}/api/vulcano/empresas`, { signal: ac.signal })
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) {
          const msg = typeof d.detail === 'string' ? d.detail : (d.detail ? JSON.stringify(d.detail) : r.statusText);
          throw new Error(msg || `HTTP ${r.status}`);
        }
        setEmpresas(Array.isArray(d) ? d : (d.data || []));
        setLoading(false);
        setLoadingSlow(false);
      })
      .catch((e) => {
        if (e.name === 'AbortError') return;
        setError(
          e.message?.includes('Failed to fetch') || e.name === 'TypeError'
            ? `Erro de conexão com o backend (${API_BASE}). Verifique se a API está no ar.`
            : `Falha ao carregar empresas: ${e.message}`
        );
        setEmpresas([]);
        setLoading(false);
        setLoadingSlow(false);
      })
      .finally(() => { clearTimeout(slowTimer); });

    return () => { clearTimeout(slowTimer); ac.abort(); };
  }, [reloadToken]);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setReloadToken((t) => t + 1);
  }, []);

  /** Os ids vem numericos da API e o useParams() sempre devolve string. */
  const findEmpresa = useCallback(
    (id) => empresas.find((e) => String(e.id) === String(id)) || null,
    [empresas]
  );

  const value = useMemo(
    () => ({ empresas, loading, error, loadingSlow, reload, findEmpresa }),
    [empresas, loading, error, loadingSlow, reload, findEmpresa]
  );

  return <EmpresasContext.Provider value={value}>{children}</EmpresasContext.Provider>;
}

// Ver nota em SessionContext.jsx sobre manter provider e hook no mesmo arquivo.
// eslint-disable-next-line react-refresh/only-export-components
export function useEmpresas() {
  const ctx = useContext(EmpresasContext);
  if (!ctx) throw new Error('useEmpresas() precisa estar dentro de <EmpresasProvider>');
  return ctx;
}
