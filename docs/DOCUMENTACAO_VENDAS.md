# Tela / Entidade: Vendas

## 1. Mapeamento de Colunas e Tipos de Dados

O painel de Vendas baseia-se na tabela central `VENDA` com um Dataframe do Pandas vetorizando e decodificando valores (Win1252) antes de exportá-los. Ele injeta joins em `CLIENTE` e `EMPREENDIMENTO` no backend.

**Colunas e Tipos Retirados da Base ERP (`VENDA v`, `CLIENTE c`, `EMPREENDIMENTO e`):**
- `v.ID`: Numérico (`Integer`). ID identificador da Venda.
- `v.NUMCADIMOB`: Texto formatado (`String`). Inscrição M imobiliária ou número lógico.
- `v.DTOPER`: Data (`Date`). Data operacional da venda, tratada no pandas para `'%d/%m/%Y'`.
- `v.DESCUNIDIMOB`: Texto (`String / Varchar`). Nome ou bloco/apto da unidade transacionada.
- `c.CNPJ` e `c.NOME`: Textos (`String`). Cadastro acoplado do id do cliente da venda.
- `v.TOTALVENDA`: Numérico (`Float`, preenchimento nativo Pandas zero-filled em valores nulos). Valor total negociado.
- `v.DISTRATO`: Texto/Data (`String`). Se houve distrato.
- `v.PERMUTA`: Texto/Booleana (`String` 'S'/'N'). Indica permuta financeira ou física.
- `e.NOME`: Texto (`String`). Identificação em cache do projeto no banco de dados.

---

## 2. Estrutura Exata do JSON (API Response)

**Rota Utilizada:** `GET /api/vulcano/vendas?empresa_id={id}`
**Mapeamento e Retorno:** Diferente das consultas raw, as colunas do DB são aliás (mapped) para nomes mais intuitivos (`CLIENTE_NOME -> cliente_nome`, `DTOPER -> data`) por meio do script de vetorização num array de dicts serializável em JSON.

**Exemplo de Resposta (JSON):**
```json
[
  {
    "id": 41258,
    "num_cad": "AP-302-B",
    "data": "15/05/2025",
    "descricao": "APARTAMENTO 302 BLOCO B",
    "cliente_cnpj": "111.111.111-22",
    "cliente_nome": "SILVA IMOVEIS LTDA",
    "total": 550000.0,
    "distrato": "",
    "permuta": "N",
    "empreendimento": "RESIDENCIAL VISTA MAR"
  }
]
```

---

## 3. Regras de Paginação e Volume de Dados

- **Paginação / Limite de Pesquisa (Backend):** Toda e qualquer operação de busca via este endpoint não detém mecanismos de cursor explícito no servidor, dependendo apenas do parâmetro `empresa_id` e uma clausula SQL de `ORDER BY v.DTOPER DESC`. Todo o lote histórico de vendas da incorporadora cai na carga da chamada.
- **Volume Esperado:** Intermediário a Altíssimo. Certas matrizes de incorporadoras poderão cruzar dados de mais de **3.000 a 15.000 Vendas (linhas ativas)** num painel só. 
- **Necessidades Vitais (UX/Operador):** 
  Ao ser consumido pela View do "VulcanoViews.jsx", o grande array renderizado precisa mandaturalmente passar por **Paginação e Virtualização Virtual do Lado do Cliente (Client-Side)**. Expor uma tabela HTML nativa ou listas DOM que reinderizem mais do que 200 vendas ativas em cascata poderá crashar por sobrealcarga da React VDOM. Bibliotecas de Windowing ou propriedades robustas `<DataGrid pagination={true} pageSize={25} />` são fundamentais para o operador ter uma experiência fluida de scroll sobre o extenso histórico retornado.
