import { useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';

/**
 * Ordenacao de tabela por cabecalho clicavel.
 *
 * O tipo de cada coluna e DECLARADO, nunca inferido do valor. Adivinhar erraria
 * neste projeto: `parcela` e "12/60" numa tela e 1234.56 na outra, e `id` e
 * numero para parcelas reais e "prazo_123" para as projetadas.
 *
 * Descritor de coluna:
 *   key       identificador (tambem o nome do campo, quando `field` e `get` faltam)
 *   label     texto do cabecalho
 *   type      'number' | 'text' | 'date' | 'parcela'  (ausente = nao ordenavel)
 *   field     campo alternativo para ordenar — permite exibir a data em
 *             DD/MM/YYYY e ordenar pelo ISO que o backend ja manda
 *   get       acessor, quando o valor ordenavel e derivado (vence `field`)
 *   right     alinhamento a direita
 *   firstDir  direcao do primeiro clique ('asc' por padrao; use 'desc' em dinheiro)
 *   when      predicado de visibilidade da coluna
 */

const VAZIO = Symbol('vazio');

function ehVazio(v) {
  return v === null || v === undefined || v === '';
}

/** "12/60" -> 12 | "ATO" -> 0 (a entrada precede a parcela 1) */
function numeroDaParcela(v) {
  if (ehVazio(v)) return VAZIO;
  const s = String(v).trim();
  if (/^ato$/i.test(s)) return 0;
  const m = s.match(/^(\d+)/);
  return m ? Number(m[1]) : VAZIO;
}

/**
 * Data comparavel como string: YYYYMMDD.
 * Aceita as duas grafias que circulam na API (ISO e brasileira) e NUNCA usa
 * `new Date()` — data sem hora entra como UTC e volta um dia no fuso local.
 */
function dataOrdenavel(v) {
  if (ehVazio(v)) return VAZIO;
  const s = String(v).trim();
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return m[1] + m[2] + m[3];
  m = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (m) return m[3] + m[2] + m[1];
  return VAZIO;
}

function numeroOrdenavel(v) {
  // Vazio nao e zero: o backend serializa numerico nulo como string vazia
  // (.fillna('')), e 0,00 e valor legitimo em Desconto/Variacao.
  if (ehVazio(v)) return VAZIO;
  const n = Number(v);
  return Number.isNaN(n) ? VAZIO : n;
}

function textoOrdenavel(v) {
  if (ehVazio(v)) return VAZIO;
  const s = String(v).trim();
  return s === '' ? VAZIO : s;
}

const EXTRATORES = {
  number: numeroOrdenavel,
  text: textoOrdenavel,
  date: dataOrdenavel,
  parcela: numeroDaParcela,
};

/**
 * Comparador de uma coluna.
 *
 * Vazios vao SEMPRE para o fim, nas duas direcoes. Numa coluna como "Data
 * Pagto", em que a maioria das linhas esta vazia, mandar o vazio para cima no
 * primeiro clique entregaria uma parede de celulas em branco e esconderia
 * justamente o que se clicou para ver. Consequencia assumida: o segundo clique
 * nao e o reverso exato do primeiro — o bloco de vazios nao sobe.
 */
export function criaComparador(coluna, dir) {
  const extrai = EXTRATORES[coluna.type] || textoOrdenavel;
  const ler = coluna.get
    ? (linha) => coluna.get(linha)
    : (linha) => linha?.[coluna.field || coluna.key];
  const sinal = dir === 'desc' ? -1 : 1;

  return (a, b) => {
    const va = extrai(ler(a));
    const vb = extrai(ler(b));

    if (va === VAZIO && vb === VAZIO) return 0;
    if (va === VAZIO) return 1;
    if (vb === VAZIO) return -1;

    if (coluna.type === 'text') {
      // sensitivity 'base' junta acentuado com nao acentuado; numeric poe
      // "APTO 2" antes de "APTO 10".
      return sinal * va.localeCompare(vb, 'pt-BR', { sensitivity: 'base', numeric: true });
    }
    if (va < vb) return -sinal;
    if (va > vb) return sinal;
    return 0;
  };
}

/**
 * @param colunas  array de descritores (constante de modulo, nao recrie por render)
 * @param options  { persistKey }  — informado, guarda a ordenacao na URL
 */
export function useTableSort(colunas, options = {}) {
  const { persistKey } = options;
  const PARAM_KEY = persistKey || 'ord';
  const PARAM_DIR = PARAM_KEY + 'Dir';

  // Hook nao pode ser condicional: os dois estados existem sempre e o retorno
  // escolhe qual vale.
  const [keyLocal, setKeyLocal] = useState('');
  const [dirLocal, setDirLocal] = useState('asc');
  const [params, setParams] = useSearchParams();

  const keyBruta = persistKey ? (params.get(PARAM_KEY) || '') : keyLocal;
  const dirBruta = persistKey ? (params.get(PARAM_DIR) || 'asc') : dirLocal;

  /**
   * Grava coluna e direcao numa unica atualizacao.
   *
   * Nao separe em dois setters: cada setSearchParams e uma navegacao, e duas no
   * mesmo evento leem ambas a URL do render corrente — a segunda sobrescreveria
   * a primeira e a coluna nunca chegaria a ser gravada.
   */
  const setOrdenacao = useCallback((k, d) => {
    if (!persistKey) {
      setKeyLocal(k || '');
      setDirLocal(d || 'asc');
      return;
    }
    setParams((prev) => {
      const novo = new URLSearchParams(prev);
      if (!k) {
        novo.delete(PARAM_KEY);
        novo.delete(PARAM_DIR);
      } else {
        novo.set(PARAM_KEY, k);
        novo.set(PARAM_DIR, d || 'asc');
      }
      return novo;
    }, { replace: true });
  }, [persistKey, setParams, PARAM_KEY, PARAM_DIR]);

  const colunaAtiva = useMemo(() => {
    if (!keyBruta) return null;
    // Valida contra a lista: protege de ?ord=qualquer-coisa na URL.
    const c = colunas.find((x) => x.key === keyBruta && x.type);
    return c || null;
  }, [colunas, keyBruta]);

  const key = colunaAtiva ? colunaAtiva.key : null;
  const dir = dirBruta === 'desc' ? 'desc' : 'asc';

  const clear = useCallback(() => setOrdenacao('', 'asc'), [setOrdenacao]);

  const toggle = useCallback((k) => {
    const c = colunas.find((x) => x.key === k);
    if (!c || !c.type) return; // coluna sem tipo nao ordena
    if (keyBruta === k) {
      setOrdenacao(k, dirBruta === 'asc' ? 'desc' : 'asc');
    } else {
      setOrdenacao(k, c.firstDir === 'desc' ? 'desc' : 'asc');
    }
  }, [colunas, keyBruta, dirBruta, setOrdenacao]);

  const apply = useCallback((linhas) => {
    // Sem ordenacao ativa devolve a MESMA referencia: enquanto ninguem clicar,
    // a tela se comporta exatamente como antes (inclusive identidade de array).
    if (!colunaAtiva || !Array.isArray(linhas)) return linhas;
    // Array.sort e estavel desde ES2019, entao o empate preserva a ordem que
    // veio do backend. Nao acrescente desempate por indice: quebraria, por
    // exemplo, a adjacencia das parcelas de uma mesma venda.
    return [...linhas].sort(criaComparador(colunaAtiva, dir));
  }, [colunaAtiva, dir]);

  const headerProps = useCallback((k) => {
    const c = colunas.find((x) => x.key === k);
    const sortable = Boolean(c && c.type);
    const active = sortable && key === k;
    return {
      sortable,
      active,
      dir: active ? dir : null,
      onClick: sortable ? () => toggle(k) : undefined,
      ariaSort: !sortable ? undefined : active ? (dir === 'asc' ? 'ascending' : 'descending') : 'none',
    };
  }, [colunas, key, dir, toggle]);

  // Objeto memoizado: quem coloca `sort` em deps de useMemo/useEffect (as duas
  // telas colocam) rodaria a cada render se a identidade mudasse sempre.
  return useMemo(
    () => ({ key, dir, toggle, clear, apply, headerProps }),
    [key, dir, toggle, clear, apply, headerProps]
  );
}
