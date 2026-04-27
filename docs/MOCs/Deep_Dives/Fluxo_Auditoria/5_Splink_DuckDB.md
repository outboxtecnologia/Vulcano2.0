# 4. Motor Probabilístico: Splink / DuckDB (poc_splink.py)
Invés do *RapidFuzz*, o **Splink** é disparado (pelos endpoints que setam use_splink = True da tela Smart Importer) para deduzir em ecossistemas de grande volume.

**Modelo Matemático Fellegi-Sunter no Backend:**
Ele não mede similaridade de String. Ele levanta a Tabela do Legacy Engine VENDAS (Vulcano) no DuckDBAPI em memória temporal:

`python
from splink import DuckDBAPI, Linker
import splink.comparison_library as cl

settings = {
    "link_type": "link_only",
    "comparisons": [
        cl.ExactMatch("num_parcela").configure(term_frequency_adjustments=True),
        cl.JaroWinklerAtThresholds("nome_comprador", [0.9, 0.8]),
        cl.AbsoluteDifferenceAtThresholds("valor_pago", [0.1, 1.0])
    ],
    "retain_matching_columns": True,
    "retain_intermediate_calculation_columns": True
}
`
*Detalhe das Regras:*
A predição "adivinha" ligações que perderam Unidade. Se o 
um_parcela cravar exato, mas o valor oscilar 1 real (AbsoluteDifference=1.0) devido à Mora, ele ainda apita como correlação confirmada, mesmo se o nome vier faturado no CNPJ do Cônjuge (m-probability).
