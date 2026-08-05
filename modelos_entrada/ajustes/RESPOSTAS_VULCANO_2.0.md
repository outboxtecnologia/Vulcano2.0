# Respostas — Guia de correções e implementos (05/08/2026)

**Tudo do guia foi implementado**, com três respostas diretas:

1. **"Vincular contas ou lançamento manual" (Integração Questor)** — o lançamento
   manual **já funciona**: em qualquer campo de conta da aba, digite o número da
   conta direto (não precisa escolher da lista); a lista do Questor é só um
   facilitador de busca.
2. **"Onde fica para incluir novos clientes?"** — o cliente nasce **no próprio
   cadastro da venda**: digite nome e CPF/CNPJ do comprador; se o CPF já existir
   (no Vulcano ou no Questor) o nome preenche sozinho, senão o cliente é criado
   automaticamente ao registrar a venda. Não há (nem precisa) tela separada.
3. **"Tag todas as parcelas/abertas não funciona"** — o caso testado tinha uma
   única parcela vencendo em **20/04** e paga em **05/06**: pesquisando junho ela
   não aparecia porque a busca era só por *vencimento*. Agora a parcela **aparece
   também no mês do pagamento**; as tags funcionam normalmente.

E o que mudou nas telas: filtros de empreendimento/unidade no cadastro de venda;
campo **Nº Contrato** (único por venda — resolve o erro da DIMOB com o mesmo CPF
comprando 2 unidades); painel da venda sem números inventados (entrada/VPL eram
10%/78% fixos!) e com **Lançar parcela manual funcionando**; totalizador de áreas
e **"usar como metragem total"** na Estrutura; excluir bloco visível + excluir
todos; Smart Importer **sugerindo o de-para sozinho** (usava um serviço que não
existe no servidor — por isso vinha tudo "Ignorar"); Recebimentos Mensal com
setas navegando de verdade, **trava de data fora da competência** e botão
**desfazer baixa** (✕) nas baixas feitas pelo sistema.

---

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

### 3 – Estrutura Blocos (importação) — **IMPLEMENTADO: matrícula de incorporação via IA**
> *"Como fazer a importação dos dados?"*

Resposta: **enviando o PDF da matrícula de incorporação** (certidão de inteiro teor).
Na aba **Estrutura (Blocos)** do empreendimento há o botão **"Enviar matrícula"**:

1. A IA (Vertex/Gemini) lê a certidão escaneada inteira — o cadastro em **3 leituras
   independentes com voto** e a estrutura em **3 leituras com voto por unidade**;
   o que divergir entre leituras vai para **rodadas de desempate focadas**. Isso
   elimina alucinações de leitura única (testado com a matrícula real 105.083 do
   GRAND LIFE RESIDENCE / ALZ: 288 apartamentos em 3 blocos extraídos exatos,
   frações ideais fechando 100%).
2. A **prévia** mostra o cadastro (nome, matrícula, incorporadora, endereço), os
   blocos, as 288 unidades com todas as áreas + vaga vinculada, e os **avisos**:
   campos onde as leituras divergiram (ex.: bairro antigo × atualizado) e unidades
   marcadas p/ conferência. Nada é gravado sem sua confirmação.
3. Você escolhe **qual área vira a metragem** da unidade (privativa, privativa total
   ou real total), se a vaga entra na descrição, e pode aplicar o endereço da
   matrícula direto na aba Dados Gerais.
4. **Gravar** cria blocos+unidades em lote (transação única). Re-importar é seguro:
   unidades que já existem são puladas.

A leitura leva ~3-5 minutos (várias passadas de conferência). Para planilhas simples
(tipo GARDEN I.xls) o cadastro manual da aba continua disponível.

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
`IDVENDAVINCULADA`, que existia no banco mas nunca era preenchido) — e o **contrato é
RATEADO entre os CPFs**: no formulário você define o **% de cada comprador** (padrão:
divisão igual) e cada linha grava a **cota daquele CPF**, somando exatamente o valor
do contrato. É essa cota por adquirente que alimenta a **DIMOB** (o R03 sai por CPF
com o valor da participação, e o valor pago no ano também é rateado na mesma
proporção) e serve de base para a **EFD-Contribuições**. Na lista, a venda aparece
**uma vez** com o valor do contrato e um selo `+N` mostrando os compradores e suas
cotas. Parcelas e recebimentos ficam só na principal (o fluxo financeiro do contrato
é um só); o distrato da principal cancela também as vinculadas.

*Caso LIGIA/LARISSA*: verificamos que a venda #19609 **já estava vinculada** à #19608
na base (campo preenchido); com a listagem nova o par passa a aparecer **uma única
vez**, com o valor do contrato (R$ 901.636,49) e o selo `+1` dos dois compradores —
o total da carteira deixa de somar R$ 1,8 mi. Outras duplicatas antigas que não
tenham o vínculo preenchido podem ser saneadas depois (posso preparar esse ajuste).

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
- **Bugs herdados da troca de base (03/08) corrigidos de brinde**: na base atual
  (`/caminho/para/QUESTOR.FDB`) `VENDA.NUMCADIMOB` é INTEGER (o insert antigo gravava
  a string "MVP-id" e estourava SQL -303 — nenhuma venda nova funcionava) e
  `EMPREENDIMENTO.AJUSTEFINALPOC` é DOUBLE (o form mandava 'N' e **salvar qualquer
  empreendimento falhava**); campos CODIGOESTAB/FILIAL/MATRIZ/MUNIC agora aceitam
  vazio (viram NULL). Testado na base real com transação + rollback e round-trip
  de PATCH restaurando o estado original.
- O gerador DIMOB (`gerar_dimob.py`) ainda não consome o endereço estruturado — quando
  formos evoluir o R01/R02, ler primeiro do Postgres com fallback para o legado (e
  migrar a conexão hardcoded dele para o `get_conn`).
