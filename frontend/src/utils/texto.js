/**
 * Texto pronto para comparacao: minusculas e sem acento.
 *
 * Buscar "alvaro" tem que achar "ÁLVARO" — nomes de comprador sao o caso de uso
 * principal das buscas do sistema. O projeto ja resolve acento na ORDENACAO
 * (localeCompare com sensitivity 'base', em hooks/useTableSort.js), mas aquilo
 * nao serve para comparar substring.
 */
export const normaliza = (v) =>
  String(v ?? '')
    .toLowerCase()
    .normalize('NFD')
    // ̀-ͯ = marcas de acento separadas pelo NFD. Escapes em vez dos
    // caracteres literais: eles sao invisiveis e nao sobrevivem a um salvamento
    // em encoding errado.
    .replace(/[̀-ͯ]/g, '');

/** Quebra a busca em termos. Vazio quando nao ha nada a procurar. */
export const termosDeBusca = (texto) =>
  normaliza(texto).split(/\s+/).filter(Boolean);
