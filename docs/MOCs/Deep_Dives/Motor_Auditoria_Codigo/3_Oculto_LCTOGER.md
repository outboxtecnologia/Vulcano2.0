# 3. O Físico Oculto (LCTOGER / Estoque Obras)
*(Como trouxemos os gastos de construção do Stuttgart!)*

O `LCTOCTB` omite gastos diretos de obra quando não são realização de custo. Precisamos hackear o `LCTOGER` buscando não pela conta, mas pelo `Centro de Custo` (CC).

**Python Rule para Injeção Gross-Fetch:**
```python
# Se movimentou na conta de Estoque Direta, injeta no balancete como D/C bruto pro Frontend ver (ESTOQUE-INJECT):

if abs(mov_debito_mes) > 0.01:
    inject_virtual_entry(
        c_estoque, mov_debito_mes, 'D',
        f"Gastos Incorridos {nome_emp} (Débitos)",
        saldo_ant=custo_gasto_anterior if not injected_any else 0.0
    )
```
*Graças a isso, a conta de Imóveis a Comercializar ganha vida do lado físico, permitindo conciliação!*
