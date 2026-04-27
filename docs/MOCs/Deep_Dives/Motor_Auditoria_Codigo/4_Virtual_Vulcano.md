# 4. Motor Vulcano Societário (O Lado Virtual)
A direita do balancete. 
A partir do % POC (Calculado via Orçamento Custeio - CUB - Custo Realizado), o motor Virtual apropria IMPOSTOS e RECEITAS.

**Regras no Python:**
Tudo cai na malha da função universal de injeção virtual:
```python
def inject_virtual_entry(conta_id, valor_mes, nat, historico, saldo_ant=0.0):
    cv = get_cv(conta_id)
    cv["saldo_anterior"] += saldo_ant
    if nat == 'D':
        cv["movimento_debito"] += valor_mes
    else:
        cv["movimento_credito"] += valor_mes
    cv["saldo_final"] = cv["saldo_anterior"] + cv["movimento_debito"] - cv["movimento_credito"]
```
É assim que os Impostos (PIS, COFINS, IRPJ) e Lucros Societários brotam sem que estivessem fisicamente preenchidos pelo contador ainda, gerando nossa projeção contra a Física.
