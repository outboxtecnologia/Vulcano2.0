# Diretrizes de UI/UX (Cores e Paletas)

## Fontes de Dados e Cores Padrão
Para evitar confusão cognitiva nas telas de Conciliação, Kanban e Tabelas, as cores atreladas a cada sistema ou versão de motor devem seguir ESTRITAMENTE a paleta abaixo e ser usadas em badges, bordas e totalizadores:

| Fonte | Cor | Código |
|---|---|---|
| **Questor Físico** | Azul | `#3b82f6` |
| **VU 1.0** (Legado) | Roxo | `#9945ff` |
| **VU 2.0** (Societário) | Magma / Laranja Queimado | `#ff4500` |

### Regras de Aplicação
1. **NUNCA** misturar essas cores. Se Questor for `#3b82f6`, ele deve ser `#3b82f6` no Kanban, na Tabular e em gráficos.
2. A cor verde `#22c55e` deve ser reservada APENAS para status de SUCESSO (ex: BATEU, Conciliação Completa). Nunca vincule a cor de sucesso a uma única fonte.
3. A cor vermelha `#d32f2f` ou `#ef4444` deve ser reservada para DIVERGÊNCIAS numéricas, e nunca como a cor fixa de um Motor (Magma é `#ff4500`).
