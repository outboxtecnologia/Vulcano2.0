# Entidade: Clientes

## 1. Mapeamento de Colunas e Tipos de Dados

A entidade de Clientes no backend baseia-se primordialmente na tabela `CLIENTE` do banco de dados legado (Vulcano). O sistema também possui uma rota de busca (fallback) que acessa a tabela `PESSOA` no banco de dados contábil (Questor).

**Tabela: `CLIENTE` (Banco Vulcano)**
- `ID`: Numérico (`Integer`). Identificador único do cliente.
- `NOME`: Texto (`String / Varchar`, decodificado de `Win1252`). Nome do cliente.
- `CNPJ`: Texto (`String / Varchar`, decodificado de `Win1252`). Documento do cliente (utilizado para armazenar CPF ou CNPJ).

**Tabela: `PESSOA` (Banco Questor - Utilizada apenas na busca fallback)**
- `CODIGOPESSOA`: Numérico (`Integer`).
- `NOMEPESSOA`: Texto (`String / Varchar`).
- `INSCRFEDERAL`: Texto (`String / Varchar` - correspondente ao CPF/CNPJ).

---

## 2. Estrutura Exata do JSON (API Responses)

Existem atualmente **dois endpoints** principais expondo aos consumidores a entidade de Clientes.

### A. Listagem de Clientes por Empresa
**Rota:** `GET /api/vulcano/clientes?empresa_id={id}`
**Descrição:** Retorna de forma plana uma lista de clientes únicos (DISTINCT) que possuem, pelo menos, uma Venda (`VENDA`) atrelada ao id da empresa conectada.

**Exemplo de Resposta (JSON):**
```json
[
  {
    "id": 1054,
    "nome": "JOAO DA SILVA",
    "cpf_cnpj": "111.222.333-44"
  },
  {
    "id": 1055,
    "nome": "EMPRESA EXEMPLO LTDA",
    "cpf_cnpj": "12.345.678/0001-90"
  }
]
```
*(Nota: as chaves são de formato lowercase plano, não estão atreladas a sub-ojetos ou metadados de paginação).*

### B. Busca Rápida de Cliente via CPF/CNPJ
**Rota:** `GET /api/vulcano/clientes/search?cpf_cnpj={doc}`
**Descrição:** Busca o registro do cliente unicamente pelo documento. Na consulta, primeiramente valida a existência daquele documento na base Vulcano; caso não encontre (false), realiza um fallback cruzando a busca na base Questor.

**Exemplo de Resposta (JSON - Encontrado em Vulcano):**
```json
{
  "found": true,
  "origem": "Vulcano",
  "id_vulcano": 1054,
  "nome": "JOAO DA SILVA",
  "cpf_cnpj": "11122233344"
}
```

**Exemplo de Resposta (JSON - Encontrado em Questor):**
```json
{
  "found": true,
  "origem": "Questor",
  "id_questor": 59912,
  "nome": "MARIA DAS GRACAS",
  "cpf_cnpj": "00011122233"
}
```

**Exemplo de Resposta (JSON - Inexistente nas 2 bases):**
```json
{
  "found": false
}
```

---

## 3. Regras de Paginação e Volume de Dados

**Situação Atual do Backend:** **Não existe paginação em servidor (Server-Side Pagination) ou estratégias de lazy loading/offset/cursor implementadas.** 

- **Na Listagem Base (`/api/vulcano/clientes`):** 
  - A query SQL extrai indiscriminadamente todos os registros associados à empresa (`.fetchall()`). 
  - **Quantidade média esperada:** A requisição devolve entre poucas dezenas a milhares de clientes dependendo da filial (100% da volumetria ativa retornada num único array).
  - **Paginação Client-Side Necessária:** Como o payload retorna um array completo e linear, a experiência de scroll pode congelar a interface (DOM memory lag). É **fortemente exigido/recomendado** que implementemos **Paginação Virtual (Client-Side)** no Frontend (ex: arrays `slice()`, virtualização de listas em tabelas/select boxes exibindo pacotes renderizáveis de 15 a 50 itens por frame).

- **Na Busca Dinâmica (`/api/vulcano/clientes/search`):** 
  - O volume é de exatos **1 único registro JSON** (limitação na query via `SELECT FIRST 1...`). Retorno imediato, comportando-se estritamente como um fallback/ID abstrato sem massa de paginação.
