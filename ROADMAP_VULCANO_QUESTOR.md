# 🚀 ROADMAP E MEMÓRIA DE DESENVOLVIMENTO (VULCANO x QUESTOR)
Este documento serve como memória persistente da inteligência artificial para as próximas iterações do sistema Questor Explorer, englobando a Automação do SERO e a estruturação Fiscal/DIMOB.

## 📌 1. Aferição SERO (Serviço Eletrônico de Aferição de Obras)
**Objetivo:** Eliminar a digitação no portal eCac, extraindo a memória de cálculo completa e as deduções fiscais diretamente do Questor e Vulcano.

### Funcionalidades a Implementar (Backend/SeroView):
* **Identificação de Unidades Autônomas:**
  * O SERO exige o fracionamento da área construtiva. *Resposta para o usuário:* Sim, no SERO lidamos com unidades autônomas (Apartamentos, Salas Comerciais e Garagens) porque áreas de garagem não cobertas ou áreas de uso comum têm redutores específicos de cálculo na Receita Federal.
  * *Ação Técnica:* Fazer o Join no Vulcano (`BLOCO` -> `UNIDADE`) para explodir a `METRAGEMTOTAL` do CNO da aba Sero nas frações exatas de unidades autônomas para relatórios aditivos do eCac.
* **Dados Estruturais (Fatores Redutores):** Trazer categoria (Alvenaria/Madeira), Destinação e Padrão de Acabamento.
* **Deduções Automáticas (Questor Fiscal/Folha):**
  * Cruzar as NF-e de Massa de Concreto Úmido para abater 5% do valor da aferição.
  * Cruzar a EFD-Reinf (NFSe de Subempreiteiros com retenção INSS) atreladas ao CNO para converter em crédito dedutível.
  * Resgatar as guias de Folha de Pagamento patronal (eSocial/GFIP) quitadas contra aquele CNO.

---

## 📌 2. Geração da Obrigação DIMOB 
**Objetivo:** Automatizar o arquivo platibanda (Validador DIMOB) da Receita Federal condensando todas as Vendas, Distratos e Receitas do ano logado.

### Funcionalidades a Implementar (DIMOB-Generator):
* Estruturar o Layout do Arquivo Texto exigido pelo Validador DIMOB.
* Condensar CPF/CNPJ dos Clientes do Vulcano.
* Somar os recebimentos (Recibos emitidos, Parcelas Pagas e Comissões retidas) referentes à venda dos Empreendimentos no ano base.
* Injetar o endpoint no botão da Sero/FiscalView: `GERAR INFORME DIMOB`.

---

## 📌 3. Validação de Lançamentos Fiscais no Questor
**Objetivo:** Assegurar que os botões (Injetar F200, Injetar RET e Processar Distratos) persistam perfeitamente na tabela alvo do Questor Firebird.

### Funcionalidades a Implementar:
* Realizar as amarrações do plano de Contas (estabelecido no formulário de Empreendimentos) com a Tabela de `FATO FISCAL` no Questor.
* **RET (Regime Especial de Tributação 4%):** Validar a amarração na tabela `EFDINCORPIMOBRET`.
* **F200 (Imobiliária Tradicional):** Certificar a baixa das parcelas (`EFDUNIDIMOBVENDIDA`) confrontando com as configurações do Código da Empresa.
* Criar painel de conciliador de relatórios: "Exportar Log de Sucesso" após tentar a injeção contábil em lote.
* 
## 📌 4. Módulo de Apropriação de Custo Contábil (POC Real - IFRS 15 / CPC 47)
**Objetivo:** Automatizar o reconhecimento de custo na DRTEE mensalmente com base na física e financeira da obra.
* **Inteligência de Cálculo:** Calcular o Gasto Total Acumulado Incorrido da Obra através da tabela gerencial do Questor (`LCTOGER` vinculada ao `LCTOCTB` por `CHAVELCTOCTB`), descontando lançamentos de encerramento (`codigohistctb = 370`).
* **Fator de Apuração:** Multiplicar o "Gasto Real" pela "Fração de Unidades Vendidas" (Metragem comercializada / Metragem Total do Empreendimento) levantada no Vulcano.
* **Índice Evolutivo:** Multiplicar novamente o fator apurado pelo `% Evolução POC` inserido na tela do robô.
* Após esse cálculo triplo, abater os custos já apurados (reconhecidos nos meses interiores) e gerar a LCTO para a diferença residual.
