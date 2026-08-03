/* eslint-disable react-refresh/only-export-components --
   Este arquivo e configuracao de rotas, nao um modulo de componentes: os wrappers
   abaixo existem so para ligar contexto as telas e nunca sao importados fora daqui. */
import { createBrowserRouter, Navigate, Outlet, useLocation, useNavigate, useOutletContext } from 'react-router';
import LoginView from './LoginView.jsx';
import EmpresaSelectionView from './components/EmpresaSelectionView.jsx';
import EmpresaLayout from './layouts/EmpresaLayout.jsx';
import ViewErrorBoundary from './components/ViewErrorBoundary.jsx';
import { SessionProvider, useSession } from './context/SessionContext.jsx';
import { ThemeProvider } from './context/ThemeContext.jsx';
import { EmpresasProvider, useEmpresas } from './context/EmpresasContext.jsx';
import { NAV_ITEMS, DEFAULT_SLUG } from './routes/navigation.js';

/** Providers que precisam sobreviver a qualquer navegacao. */
function RootLayout() {
  return (
    <ThemeProvider>
      <SessionProvider>
        <Outlet />
      </SessionProvider>
    </ThemeProvider>
  );
}

/** So aceita caminho interno como destino pos-login (nao redireciona para fora). */
function safeFrom(from) {
  if (typeof from !== 'string') return null;
  return from.startsWith('/') && !from.startsWith('//') ? from : null;
}

function LoginRoute() {
  const { user, login } = useSession();
  const location = useLocation();
  const destino = safeFrom(location.state?.from) || '/empresas';

  if (user) return <Navigate to={destino} replace />;

  // A maquina de estados interna do LoginView (login | primeiro-acesso |
  // primeiro-acesso-senha) e proposital: sao passos de um mesmo formulario, nao
  // telas do app. Nao transforme em rotas.
  return <LoginView onLogin={login} />;
}

function RequireAuth() {
  const { user } = useSession();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  // A lista de empresas so e buscada depois do login, e o logout a descarta junto.
  return (
    <EmpresasProvider>
      <Outlet />
    </EmpresasProvider>
  );
}

function EmpresasRoute() {
  const { empresas } = useEmpresas();
  const { logout } = useSession();
  const navigate = useNavigate();

  return (
    <EmpresaSelectionView
      globalEmpresas={empresas}
      onSelectEmpresa={(id) => navigate(`/empresa/${id}/${DEFAULT_SLUG}`)}
      onLogout={logout}
    />
  );
}

/**
 * Adapta uma view ao router sem tocar na assinatura dela: continua recebendo
 * a prop selectedEmpresa como sempre recebeu.
 *
 * O key={empresaId} e correcao, nao enfeite: trocar de empresa nao limpava o
 * drill-down das telas (o empreendimento selecionado em Custos, o CNO em Sero, o
 * modal aberto em Empreendimentos, os dados apurados em Fiscal), entao dado de uma
 * empresa aparecia sob o nome de outra. Remontar zera isso. O que precisa sobreviver
 * a troca — periodo, competencia — vive na URL, e a remontagem o le de volta.
 */
function ViewRoute({ item }) {
  const { empresaId } = useOutletContext();
  const navigate = useNavigate();
  const { Component, global } = item;

  if (global) return <Component />;

  return (
    <Component
      key={empresaId}
      selectedEmpresa={empresaId}
      onNavigate={(slug, param) =>
        navigate(`/empresa/${empresaId}/${slug}${param != null ? `/${param}` : ''}`)
      }
    />
  );
}

const viewRoutes = NAV_ITEMS.map((item) => ({
  path: item.childPath ? `${item.slug}/${item.childPath}` : item.slug,
  element: <ViewRoute item={item} />,
  // Erro fica contido nesta view: o shell continua navegavel.
  errorElement: <ViewErrorBoundary />,
}));

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: '/login', element: <LoginRoute /> },
      {
        element: <RequireAuth />,
        children: [
          { path: '/', element: <Navigate to="/empresas" replace /> },
          { path: '/empresas', element: <EmpresasRoute /> },
          {
            path: '/empresa/:empresaId',
            element: <EmpresaLayout />,
            children: [
              { index: true, element: <Navigate to={DEFAULT_SLUG} replace /> },
              ...viewRoutes,
            ],
          },
        ],
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
