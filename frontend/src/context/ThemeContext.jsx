import { createContext, useContext, useEffect, useMemo, useState } from 'react';

/**
 * Tema visual: dark | light.
 *
 * Vive acima das rotas, num provider sempre montado: antes o estado era do App e o
 * efeito rodava antes dos early returns dos gates, entao login e selecao de empresa
 * tambem recebiam o data-theme. Com as telas em rotas separadas, um provider no topo
 * e o que mantem esse comportamento — e evita que escolher LIGHT e deslogar deixe
 * data-theme="light" preso no <html> por cima da cena escura do login.
 *
 * O efeito e o dono unico do DOM: nao chame setAttribute em nenhum outro lugar.
 * O primeiro paint e resolvido pelo script inline do index.html — o fallback de la
 * TEM que ser o mesmo daqui.
 */
const ThemeContext = createContext(null);

const STORAGE_KEY = 'vulcano.theme';
const THEMES = ['dark', 'light'];

function readStoredTheme() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light') return 'light';
    // 'night' era o nome antigo do escuro; 'numb' foi removido. Qualquer valor
    // desconhecido cai em dark, e o efeito abaixo regrava a chave ja normalizada —
    // migracao auto-cicatrizante, sem codigo de migracao.
    return 'dark';
  } catch {
    return 'dark';
  }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(readStoredTheme);

  useEffect(() => {
    // data-theme e o unico sinal de tema do app (ver tailwind.config darkMode).
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme; // controles nativos
    try {
      localStorage.setItem(STORAGE_KEY, theme); // preferencia, nao sessao
    } catch {
      // sem persistencia: volta a dark no proximo load
    }
  }, [theme]);

  const value = useMemo(() => ({ theme, setTheme, themes: THEMES }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

// Ver nota em SessionContext.jsx sobre manter provider e hook no mesmo arquivo.
// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme() precisa estar dentro de <ThemeProvider>');
  return ctx;
}
