import { createContext, useCallback, useContext, useMemo, useState } from 'react';

/**
 * Sessao do usuario logado, persistida em sessionStorage (some ao fechar a aba).
 *
 * ATENCAO — isto NAO e uma barreira de seguranca. O backend nao emite token nem
 * cookie: POST /api/auth/login (backend/main.py) responde so {success, user}, e
 * nenhuma rota da API valida sessao — inclusive POST /api/explorer/query, que
 * executa SQL arbitrario. O <RequireAuth> existe para dar destino as rotas e para
 * nao pedir login a cada F5. Quem tiver curl acessa a API inteira do mesmo jeito.
 * Se um dia o backend emitir token, e aqui que ele passa a ser guardado.
 */
const SessionContext = createContext(null);

const STORAGE_KEY = 'vulcano.user';

function readStoredUser() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null; // sessionStorage bloqueado (modo restrito) ou JSON corrompido
  }
}

export function SessionProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);

  const login = useCallback((userData) => {
    setUser(userData);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    } catch {
      // sem persistencia: a sessao vale so enquanto a pagina nao recarregar
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // idem
    }
  }, []);

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

// O provider e o hook moram juntos de proposito: separa-los em dois arquivos so para
// satisfazer o fast refresh deixaria o contexto mais dificil de ler que de recarregar.
// eslint-disable-next-line react-refresh/only-export-components
export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession() precisa estar dentro de <SessionProvider>');
  return ctx;
}
