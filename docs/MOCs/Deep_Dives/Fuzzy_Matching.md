---
tags: [fuzzy, heuristica, splink]
---

# 🔀 Fuzzy Matching e Pareamento Probabilístico

O Pareamento Probabilístico, ou Fuzzy Matching, é um pilar vital no sistema do **Auditoria ERP** porque os dados contábeis (como descrições de lançamentos ou históricos) digitados por operadores humanos muitas vezes contém erros de grafia, abreviações não padronizadas ou pequenas inversões nas palavras.

## ⚙️ A Lógica Interna (`SequenceMatcher`)

O sistema Vulcano utiliza internamente algoritmos de similaridade de strings (semelhantes ao **Levenshtein Distance** e ao módulo **`SequenceMatcher`** do Python).

### Como funciona no processo ("Concilia Órfãos")?

Quando temos um débito no Questor e tentamos achar seu "irmão" no Vulcano:
1. **Deduplicação Determinística**: Primeiro o sistema tenta encontrar valores *exatos* no mesmo dia. Se achar, encerra.
2. **Motor Fuzzy (Probabilidade)**: 
   - Se sobram "órfãos", o sistema compara o *Histórico Contábil* de cada laçamento remanescente usando `SequenceMatcher.ratio()`.
   - Se o score for maior que um limiar aceitável (ex: `0.7` ou `70%` de similaridade), o sistema pontua essa conexão como **"Alta Probabilidade"**.
3. **Inversão de Naturezas**: O sistema também é treinado para cruzar um Débito de um lado com um Crédito do outro (partidas dobradas), varrendo a "Natureza" de entrada.

## 🚀 Integração Splink

Em pipelines mais robustos de grandes batedores de dados, também adotamos a mentalidade do **Splink** (Biblioteca focada em linkage probabilístico record), que atribui "Pesos" diferentes estatísticos (Ex: bater CNPJ tem um peso matematicamente maior do que bater um fragmento do Histórico).

👉 *Retornar para* [[docs/MOCs/Logica_e_LLM|Lógica Principal]]
