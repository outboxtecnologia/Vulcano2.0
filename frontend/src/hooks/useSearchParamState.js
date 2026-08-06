import { useCallback } from 'react';
import { useSearchParams } from 'react-router';

/**
 * Mesmo contrato do useState, com a URL como fonte da verdade.
 *
 * Serve para filtros que precisam sobreviver a F5, a link colado e a remontagem da
 * view quando se troca de empresa. Como devolve [valor, setter], a troca custa uma
 * linha na declaracao e nenhuma nos pontos de uso.
 *
 *   const [ano, setAno] = useSearchParamState('ano', anoAtual, { parse: Number });
 *
 * `replace: true` (padrao) e importante: digitar num campo de periodo nao deve
 * empilhar uma entrada no historico a cada tecla. Use replace: false so quando a
 * mudanca for uma navegacao de verdade, que o Voltar deva desfazer.
 */
export function useSearchParamState(key, initial, options = {}) {
  const [params, setParams] = useSearchParams();

  // Passe `parse`/`serialize` como referencias estaveis (Number, String, uma funcao
  // de modulo) — sao dependencias do setter. Um `(v) => Number(v)` inline recriaria o
  // setter a cada render.
  const { parse = String, serialize = String, replace = true } = options;

  const raw = params.get(key);
  const value = raw === null ? initial : parse(raw);

  const setValue = useCallback((next) => {
    setParams((prev) => {
      const novo = new URLSearchParams(prev);
      const atualRaw = novo.get(key);
      const atual = atualRaw === null ? initial : parse(atualRaw);
      const resolvido = typeof next === 'function' ? next(atual) : next;
      if (resolvido === '' || resolvido === null || resolvido === undefined) {
        novo.delete(key);
      } else {
        novo.set(key, serialize(resolvido));
      }
      return novo;
    }, { replace });
  }, [key, setParams, parse, serialize, replace, initial]);

  return [value, setValue];
}

/**
 * Escreve VARIOS parametros de uma vez, numa unica navegacao.
 *
 * Use sempre que uma acao mudar mais de um parametro. Dois setters do
 * useSearchParamState no mesmo tick NAO se acumulam: o setSearchParams do
 * react-router resolve a funcao contra o `searchParams` do render atual
 * (useMemo sobre location.search), entao a segunda chamada parte da MESMA
 * origem que a primeira e o navigate dela sobrescreve o anterior.
 *
 *   setMes(9); setAno(2026);   // -> ?ano=2026&mes=8   (o mes 9 se perdeu)
 *   setCompetencia({ mes: 9, ano: 2026 });  // -> ?ano=2026&mes=9
 *
 * Foi o que travou a navegacao de competencia em Recebimentos Mensal: como o
 * ano quase nunca muda junto, o setAno reescrevia o mes antigo por cima e a
 * tela nao saia do lugar.
 */
export function useSearchParamsPatch(options = {}) {
  const [, setParams] = useSearchParams();
  const { replace = true } = options;

  return useCallback((patch) => {
    setParams((prev) => {
      const novo = new URLSearchParams(prev);
      for (const [chave, valor] of Object.entries(patch)) {
        if (valor === '' || valor === null || valor === undefined) {
          novo.delete(chave);
        } else {
          novo.set(chave, String(valor));
        }
      }
      return novo;
    }, { replace });
  }, [setParams, replace]);
}
