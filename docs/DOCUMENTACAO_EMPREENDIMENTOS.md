# Tela / Entidade: Empreendimentos (Central de Gestão)

## 1. Mapeamento de Telas Cativas e Abas de Edição (O Modal)

Diferente de outras rotas simples, quando o operador clica em **"Novo Empreendimento"** ou em **"Editar"** (`EmpreendimentosView.jsx`), a entidade se destrincha em um formulário multipartes complexo segmentado em **5 Abas Cativas Editáveis** que compõem o corpo do payload de criação/atualização.

### Aba 1: Dados & Localização (`tab: dados`)
Campos puros de caracterização e endereço do móvel.
- `nome` (String): Nome da obra.
- `cnpj`, `cno` (String): Identificadores tributários (o CNO é a chave pro SERO).
- `cep`, `siglaestado`, `codigomunic`, `codigoestab`, `codigofilial`, `codigomatriz` (Strings): Endereçamento lógico matriz/filial.
- `metragem` (Float): Total geral de m² (Usado de base pra taxa financeira).
- `custo` (Float): Orçamento presumido base.
- `obra_concluida` (Flag String 'S'/'N'): Regula se o motor continua rodando o POC/Custos em cima da obra ou trava no acumulado final.
- `data_conclusao` (Date String).

### Aba 2: Fiscal/RET (`tab: fiscal`)
Configurações diretas de enquadramento tributário para cálculo de Guias EFD.
- `ret` (Flag String 'S'/'N'): Se está sob Regime Especial Tributário.
- `aliqret` (Float): Percentual global taxado das parcelas recebidas (ex: 4%).
- `datainicioret` (Date String).
- `codigoimposto`, `variacaoimposto` (Int): Apontadores nativos do Questor Tributário para recolhimentos normais de presumido.
- `tributarnormalaposconclusao` (Flag 'S'/'N').

### Aba 3: Parâmetros Automáticos / Motor (`tab: config`)
Esses switches ativam ou desligam as alavancas do robô orçamentário.
- `reajustar_pelo_cub` ('S'/'N'): Corrige as parcelas vincendas inflacionando mensalmente pelo INCC/CUB.
- `ajustefinalpoc` ('S'/'N'): Trava a margem e descarrega todo encargo em Passivos logo após os 100%.
- `considerar_poc_receita` ('S'/'N'): Usa receita gerada para guiar DRE, ignorando o fluxo de caixa recebido de fato.
- `sem_custos` ('S'/'N'): Determina que o motor PULE a leitura de notas fiscais deste número de centro de custo.

### Aba 4: Questor / Contabilidade (`tab: questor`)
Permite o de-para (match) entre as esferas Vulcano e Contas Analíticas Reais do Questor (Listas Auto-Complete numéricas).
- `conta_caixa` (Conta Banco/Depósito).
- `conta_clientes`, `conta_adi_cli` (Contas sintéticas ativas de valores a Receber).
- `conta_estand` (Estoque Andamento), `conta_estcon` (Concluído).
- `conta_rec`, `conta_variacao`, `conta_devolucao`, `conta_despesa` (Mapeamentos de DRE/Deduções).
- `contacusto`, `contalucroacum`, `conta_estorno_devolucao`.
- `centro_custo` (ID Int).
- Históricos Padrão (`hist_venda`, `hist_recebimento`, `hist_اديantamento`, `hist_aprcusto`, `hist_baixaadi`, etc).

### Aba 5: Estrutura Física / Sub-entidades (`tab: estrutura`)
Um empreendimento pai possui Entidades Filhas independentes que populam essa aba: **Blocos** e **Unidades**, que permitem CRUD isolado (Inserir/Editar/Excluir).
- **Bloco (`/api/vulcano/blocos`)**: `nome` (ex: "Bloco A", "Torre Única").
- **Unidade (`/api/vulcano/unidades`)**: Acoplada diretamente a um Bloco. Possui `descricao` (nº apt), `metragem`, `inscricao` (ID de carne municipal) e `unidade_distrato` ('S'/'N').

---

## 2. Estrutura Exata do JSON (API Response)

A base de carregamento (`GET /api/vulcano/empreendimentos`) traz todos esses parâmetros achatados num payload Flat List igual exemplificado na versão anterior da doc.

No entanto, ao abrir a tela de Edição (O Modal) e navegar para a Aba 5 (Estrutura), o frontend dispara a rota adicional **`GET /api/vulcano/empreendimentos/{emp_id}/detalhes`**, que traz a relação de dependência arquitetural da obra.

**Exemplo de Resposta Sub-estrutural (Aba Estrutura):**
```json
{
  "blocos": [
    {
      "id": 1,
      "id_empreendimento": 15,
      "nome": "TORRE SUL"
    }
  ],
  "unidades": [
    {
      "id": 105,
      "id_bloco": 1,
      "descricao": "AP 101",
      "metragem": 75.5,
      "inscricao": "100.555.20-1",
      "unidade_distrato": "N"
    },
    {
      "id": 106,
      "id_bloco": 1,
      "descricao": "AP 102",
      "metragem": 120.0,
      "inscricao": "100.555.20-2",
      "unidade_distrato": "S"
    }
  ]
}
```

---

## 3. Regras de Paginação e Volume de Dados

**Listagem Principal (Painel Pai de Empreendimentos):**
A paginação no servidor não existe. O arrasto de array flat retorna todos os projetos de uma vez. O impacto no frontend é leve, e pode ser acomodado em memória.

**Listagem Filha (Aba de Estrutura Física das Unidades):**
Também **NÃO POSSUI** paginação nativa (Retorna as vezes dezenas ou centenas de unidades dentro do payload de `detalhes` do Empreendimento focado).
Neste escopo do operador (dentro do modal renderizando Unidade por Unidade no `<tbody>`), caso a incorporadora possua arranha-céus ou grandes condomínios fechados (lotes de 1000+ unidades acopladas), o Modal do usuário tenderá a perder Taxa de Quadros (FPS) ao mapear as linhas React. Como solução arquitetural visual, recomenda-se virtualizar o scroll unicamente na caixa `overflow` do Modal correspondente se o cliente escalar para torres imensas.
