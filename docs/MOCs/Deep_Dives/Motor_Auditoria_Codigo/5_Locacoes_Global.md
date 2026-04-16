# 5. Injeção de Rendas Diversas (GLOBAL_LOC)
Resolvendo os "Aluguéis Desaparecidos". As filiais/matriz recebem locações brutas de apartamentos antigos que escapam do IFRS 15.

**Regra dura em Python que corrigimos:**
Fomos à caçada da conta cravada de depósitos bancários, garantindo o Match com Segurança:
```python
# O usuário garantiu ser o Banco Principal:
c_deb_deposito = 4910  # Clientes Depósito
c_cred_receita = 230   # Receita Acumulada

for estab in todos_estabs:
    v_loc = loc_mes.get(estab, 0.0)
    if abs(v_loc) > 0.01:
        # Injeta dinamicamente para Matriz ou SCPs:
        inject_loc_entry(c_deb_deposito, v_loc, 'D', f"Recebimento Locação {nome_filial}")
        inject_loc_entry(c_cred_receita, v_loc, 'C', f"Receita de Locação {nome_filial}")
```
*Sendo acoplado no pacote virtual "GLOBAL_LOC" impedindo sobreposição nos empreendimentos novos.*
