import {
  Activity, Briefcase, Building2, Construction, Database, DollarSign, FileSpreadsheet,
  HandCoins, LayoutDashboard, ListPlus, PieChart, ShieldCheck, ShoppingCart, Trash2,
  TrendingUp, UploadCloud, Users,
} from 'lucide-react';

import { DashboardMeta, VendasView, RecebimentosView, ConciliadorView } from '../VulcanoViews';
import { EmpreendimentosView } from '../EmpreendimentosView';
import { FiscalSpedView } from '../FiscalSpedView';
import { RecebimentosMensalView } from '../RecebimentosMensalView';
import { GeracaoParcelasView } from '../GeracaoParcelasView';
import { TributosGlobaisView } from '../TributosGlobaisView';
import { EvolucaoPOCView } from '../EvolucaoPOCView';
import { SeroView } from '../SeroView';
import { RawExplorerView } from '../RawExplorerView';
import { CustosView } from '../CustosView';
import { ContabilizacoesView } from '../ContabilizacoesView';
import { AuditoriaERPView } from '../AuditoriaERPView';
import { SindicatosView } from '../SindicatosView';
import { JanitorView } from '../JanitorView';
import SmartImporter from '../SmartImporter';

/**
 * Fonte unica da navegacao: alimenta ao mesmo tempo a sidebar e as rotas.
 *
 * Antes eram duas listas soltas no App.jsx — os NavItem e o switch de currentView —
 * em ordens diferentes e ja divergentes (o slug era 'compare' para a "Auditoria ERP").
 *
 * Campos:
 *   slug       segmento da URL sob /empresa/:empresaId/
 *   childPath  segmento extra da rota, quando a view tem sub-rota (ex.: 'fiscal/:tab?')
 *   global     view que nao recebe selectedEmpresa (dados do sistema, nao da empresa)
 *   scopedTail true = o resto da URL pertence a esta empresa e deve cair ao trocar
 *   dropQuery  params de busca que nao sobrevivem a troca de empresa
 */
export const NAV_SECTIONS = [
  {
    title: 'Core Modules',
    items: [
      { slug: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, Component: DashboardMeta },
      { slug: 'empreendimentos', label: 'Empreendimentos', icon: Building2, Component: EmpreendimentosView },
      { slug: 'vendas', label: 'Vendas', icon: ShoppingCart, Component: VendasView },
      { slug: 'recebimentos', label: 'Recebimentos', icon: DollarSign, Component: RecebimentosView },
      { slug: 'recebimentos-mensal', label: 'Receb. Mensal', icon: DollarSign, Component: RecebimentosMensalView },
      { slug: 'gerar-parcelas', label: 'Geração de Parcelas', icon: ListPlus, Component: GeracaoParcelasView, dropQuery: ['emp'] },
      { slug: 'importer', label: 'Smart Importer', icon: FileSpreadsheet, Component: SmartImporter },
      { slug: 'conciliador', label: 'Conversor Universal', icon: UploadCloud, Component: ConciliadorView },
    ],
  },
  {
    title: 'Enterprise Suite',
    items: [
      { slug: 'tributos', label: 'Tributos Globais', icon: PieChart, Component: TributosGlobaisView },
      { slug: 'poc', label: 'Evolução POC', icon: Construction, Component: EvolucaoPOCView },
      { slug: 'auditoria-erp', label: 'Auditoria ERP', icon: ShieldCheck, Component: AuditoriaERPView, dropQuery: ['filtroEmp'] },
      { slug: 'contabilizacoes', label: 'Contabilizações', icon: TrendingUp, Component: ContabilizacoesView, dropQuery: ['filtroEmp'] },
      { slug: 'fiscal', label: 'Fiscal & SPED', icon: Briefcase, Component: FiscalSpedView, childPath: ':tab?' },
      { slug: 'custos', label: 'Fechamento Custos', icon: HandCoins, Component: CustosView, childPath: ':empId?', scopedTail: true },
      { slug: 'sero', label: 'Sero INSS', icon: Activity, Component: SeroView },
      { slug: 'sindicatos', label: 'Sindicatos CCT', icon: Users, Component: SindicatosView, global: true },
      { slug: 'explorer', label: 'Raw Explorer', icon: Database, Component: RawExplorerView, global: true },
      { slug: 'janitor', label: '🧹 Janitor SRE', icon: Trash2, Component: JanitorView, global: true },
    ],
  },
];

export const NAV_ITEMS = NAV_SECTIONS.flatMap((s) => s.items);

export const DEFAULT_SLUG = 'dashboard';

const BY_SLUG = new Map(NAV_ITEMS.map((item) => [item.slug, item]));

/**
 * Reescreve o resto da URL ao trocar de empresa pelo seletor do topbar.
 *
 * A view e preservada, mas o que pertence a empresa antiga nao pode ir junto:
 * /empresa/959/custos/4995 -> /empresa/1001/custos, porque 4995 e um empreendimento
 * da 959 e consultado contra a 1001 traria dado errado em silencio. Filtros globais
 * (ano, mes, periodo) sobrevivem.
 */
export function rewriteTailForEmpresa(tail, search) {
  const [slug, ...rest] = (tail || '').split('/').filter(Boolean);
  const item = BY_SLUG.get(slug);
  if (!item) return { path: DEFAULT_SLUG, search: '' };

  const path = item.scopedTail || rest.length === 0 ? item.slug : [item.slug, ...rest].join('/');

  if (!search) return { path, search: '' };
  const params = new URLSearchParams(search);
  (item.dropQuery || []).forEach((key) => params.delete(key));
  const qs = params.toString();
  return { path, search: qs ? `?${qs}` : '' };
}
