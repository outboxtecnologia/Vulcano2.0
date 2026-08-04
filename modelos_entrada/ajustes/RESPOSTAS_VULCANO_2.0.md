# Respostas — Ajustes VULCANO 2.0 (doc de 04/08/2026)

Este arquivo responde as perguntas do documento `VULCANO 2.0.docx` e resume o que foi
implementado em cada item. Tudo está na branch `ajustes-doc-vulcano20`.

---

## EMPREENDIMENTOS

### Tag de pesquisa / número de cadastro
O número de cadastro que o Vulcano antigo gerava é o **ID do empreendimento** — ele já
aparece no card de cada empreendimento ("ID 153", "ID 154"...). Agora a Central de
Empreendimentos tem uma **barra de busca** no topo que localiza por **nome, número de
cadastro (ID), CNPJ ou CNO**. O card também passou a exibir o CNPJ junto do CNO.

### 1 – Dados Gerais
- **CNPJ RET**: o campo existia mas não gravava (bug — a API não persistia). Corrigido.
  Além de digitar, dá para **puxar do Questor**: o botão ao lado do campo lista os
  estabelecimentos da empresa (CNPJ de cada filial/SPE) para vincular com um clique.
- **CNO da obra**: botão ao lado do campo lista as **obras (CNO) cadastradas no Questor**
  para a empresa (tabela de obras OUTRAEMPRESA, tipo 1 = obra/CNO) — seleciona e o CNO
  preenche sozinho.
- **Data inicial RET** (+ **alíquota RET %**): novos campos que aparecem quando
  "Adere ao RET?" = Sim.
- **Endereço layout DIMOB**: o campo único de endereço virou uma grade estruturada —
  Logradouro, Número, Complemento, Bairro, CEP, UF e Código do Município (código do
  Questor; a conversão p/ tabela da DIMOB entra quando evoluirmos o gerador) — o
  formato estruturado que a DIMOB exige. Ao vincular o estabelecimento (CNPJ) ou a obra (CNO) do
  Questor, o endereço vem preenchido automaticamente (e continua editável). O endereço
  estruturado fica no banco novo do Vulcano 2.0 (Postgres `vulcano2`); o campo antigo
  do Vulcano legado continua recebendo o endereço concatenado, então nada quebra.

### 2 – Integração Questor
- **Plano de contas**: já funcionava por empresa (Plano de Contas Especial — PLANOESPEC
  filtrado pela empresa selecionada). Mantido.
- **Centro de custo**: **corrigido** — antes a lista trazia os centros de custo de TODAS
  as empresas do Questor (por isso apareciam coisas como "Trade Marketing"); agora só
  vêm os centros de custo cadastrados para a empresa selecionada.

### 3 – Estrutura Blocos (importação) — **A TRABALHAR JUNTOS**
> *"Como fazer a importação dos dados?"*

Hoje só existe cadastro manual (um bloco/unidade por vez). A proposta para discutirmos:

1. **Planilha modelo** com colunas `Bloco | Unidade | Metragem | Inscrição Imobiliária`
   (mesmo formato do arquivo `GARDEN I.xls` que já está em modelos_entrada).
2. Botão **"Importar planilha"** na aba Estrutura (Blocos): lê o Excel direto no
   navegador, mostra prévia com validação (blocos novos × existentes, unidades
   duplicadas) e grava em lote nos cadastros de blocos/unidades já existentes.
3. Alternativa mais robusta: usar o **Smart Importer** (tela 5), que já tem fila e
   mapeamento de colunas assistido, para PDFs/planilhas fora do padrão.

Nada disso foi implementado ainda — está reservado para definirmos o formato juntos.

---

## VENDAS

### Relatório em Excel
Botão **"Excel"** no topo da tela de Vendas: exporta a lista filtrada (empreendimento +
período + status + busca) com as colunas ID, Data, Empreendimento, Unidade, Comprador
Principal, CPF/CNPJ, Compradores (todos), Total, Permuta, Status e Data Distrato.

### 1 – Cadastrar Nova Venda
> *"Como cadastrar nova venda?"*

O formulário antigo (ID na mão + texto livre) foi substituído. O fluxo agora é:

1. **Nova venda** → selecionar o **empreendimento** na lista (não é mais número digitado).
2. As **unidades disponíveis** do empreendimento carregam sozinhas (bloco + descrição +
   metragem); unidades já vendidas não aparecem. Dá para marcar mais de uma
   (ex.: apartamento + vaga de garagem).
3. Preencher **data** e **total da venda**.
4. **Imóvel permutado?** Sim/Não — novo campo; se Sim, abre o campo opcional
   "Conta Permuta" (conta contábil do Questor para a permuta).
5. **Compradores**: um ou mais. O 1º é o titular; ao digitar o CPF/CNPJ o sistema busca
   o nome no cadastro (Vulcano e, se não achar, no Questor). "Adicionar comprador"
   inclui o 2º, 3º... compradores.
6. **Condições de pagamento** (ver abaixo).
7. **Registrar venda** — o sistema grava: a venda, as unidades vinculadas, os clientes,
   as formas de pagamento com todas as parcelas projetadas e os títulos a receber.

**Venda com mais de um comprador** (campo "vincular venda"): seguimos o modelo do
Vulcano antigo — cada comprador extra vira uma venda **vinculada** à principal (campo
`IDVENDAVINCULADA`, que existia no banco mas nunca era preenchido). Diferença importante:
a venda principal carrega o **valor cheio** e as vinculadas ficam com **valor zero**,
para o total da carteira **não somar em dobro** (no modelo antigo as duas linhas
carregavam o valor cheio — ex.: as vendas #19608/#19609 de R$ 901.636,49 que hoje
aparecem somando R$ 1,8 mi). Na lista, a venda aparece **uma vez** com um selo `+1`
mostrando os demais compradores. Parcelas e recebimentos ficam só na principal; o
distrato da principal cancela também as vinculadas.

*Vendas antigas duplicadas* (como a LIGIA/LARISSA) permanecem como estão — dá para
saneá-las depois preenchendo o vínculo, se quiserem (posso preparar esse ajuste).

### Campo forma de pagamento — onde fica?
> *"Campo forma de pagamento – onde fica?"*

Fica **dentro do próprio formulário de nova venda**, na seção **"Condições de
Pagamento"**. Cada condição tem: tipo (**SINAL, MENSAL, SEMESTRAL, ANUAL, REFORÇO,
INTERMEDIÁRIA, CHAVES, FINANCIAMENTO**), quantidade de parcelas, valor da parcela e
1º vencimento. O rodapé compara a soma das condições com o total da venda e avisa se
divergir. O sistema gera as parcelas automaticamente (REFORÇO detecta intervalo 6/12
meses; CHAVES/FINANCIAMENTO ancoram após a última mensal). Depois de gravada, a venda
mostra as condições e parcelas no painel direito da tela de Vendas (clicar na venda).

---

## Notas técnicas (para a equipe)

- Branch: `ajustes-doc-vulcano20` (a partir do master).
- Correção de bug incluída: o botão de **distrato** chamava uma rota que não existia
  (`/vendas/{id}/distratar`); agora chama a rota real `/api/distratos`, com campos de
  data do distrato e valor devolvido no modal.
- Banco novo do app: Postgres `vulcano2` (mesma instância local 5433 que hospeda
  irpf/academia/rag), configurado por `APP_DB_KIND=postgres` + `APP_PG_*` no
  `backend/.env`. A tabela `empreendimento_endereco` é criada automaticamente no
  primeiro uso. Sem `APP_DB_KIND`, cai no SQLite local (poc_database.sqlite).
- Zero DDL no Firebird do Vulcano legado — só DML em colunas que já existiam
  (CNPJ, CONTA_PERMUTA, IDVENDAVINCULADA, INFCOMP).
- O gerador DIMOB (`gerar_dimob.py`) ainda não consome o endereço estruturado — quando
  formos evoluir o R01/R02, ler primeiro do Postgres com fallback para o legado (e
  migrar a conexão hardcoded dele para o `get_conn`).
