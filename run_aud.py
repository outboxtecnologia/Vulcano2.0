import os
import json

base_dir = r"docs\MOCs\Deep_Dives\Motor_Auditoria_Codigo"
os.makedirs(base_dir, exist_ok=True)

v_aud_main = """# 1. API de Contabilizações (Ponto de Partida)
Como o Dashboard de Auditoria ERP monta a grade (O Espelho)?
Arquivo de origem: `graph_logic_builder.py`

**A Instanciação Assíncrona e Paralela:**
Ao carregar a tela, rodamos Threads pesadas simultâneas via `ThreadPoolExecutor` para acelerar a busca no motor legado.
```python
with ThreadPoolExecutor(max_workers=2) as _pool:
    _f_atual = _pool.submit(get_receitas_caixa, empresa_id=959, data_ini="2025-03", ...)
    _f_pq = _pool.submit(get_receitas_caixa, empresa_id=959, data_ini="2024-03", ...) # Passivo do Quadro (PQ)

receitas_meta_atual = _f_atual.result()
```
*Aqui, se amarram os dados dos Recebimentos Reais (vividos ou importados via Splink/Fuzz do Módulo SmartImporter) para dentro da malha Societária da Auditoria.*
"""

v_aud_fisico = """# 2. Motor Questor Físico (LCTOCTB)
Este é o lado ESQUERDO do painel. A realidade fiscal contábil gravada no DB.

**Evitando A Grande Quebra do 'ZZ':**
Os sistemas contábeis encerram anos (Zeram a DRE) usando uma origem 'ZZ'. Se olharmos as receitas antigas, estariam 0.00.
```python
cur_q.execute('''
    SELECT CONTACTBDEB, CONTACTBCRED, SUM(VALORLCTOCTB)
    FROM LCTOCTB 
    WHERE CODIGOEMPRESA = ? 
      AND DATAINCLUSAO BETWEEN ? AND ?
      AND CODIGOORIGLCTOCTB <> 'ZZ'  # <-- O Segredo!
''')
```
*Assim garantimos que nosso Saldo em `contas_fisicas_empresa` não é corrompido ou sumido (como aconteceu no passado na base Questor).*
"""

v_aud_lctoger = """# 3. O Físico Oculto (LCTOGER / Estoque Obras)
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
"""

v_aud_virtual = """# 4. Motor Vulcano Societário (O Lado Virtual)
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
"""

v_aud_locacoes = """# 5. Injeção de Rendas Diversas (GLOBAL_LOC)
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
"""

notes = {
    "1_API_Contabilizacoes.md": v_aud_main,
    "2_Fisico_Questor.md": v_aud_fisico,
    "3_Oculto_LCTOGER.md": v_aud_lctoger,
    "4_Virtual_Vulcano.md": v_aud_virtual,
    "5_Locacoes_Global.md": v_aud_locacoes
}

for k, content in notes.items():
    with open(os.path.join(base_dir, k), "w", encoding="utf-8") as f:
        f.write(content)

canvas_data = {
  "nodes": [
    {"id": "n1", "type": "file", "file": r"docs\MOCs\Deep_Dives\Motor_Auditoria_Codigo\1_API_Contabilizacoes.md", "x": -600, "y": 0, "width": 400, "height": 380, "color": "4"},
    {"id": "n2", "type": "file", "file": r"docs\MOCs\Deep_Dives\Motor_Auditoria_Codigo\2_Fisico_Questor.md", "x": 0, "y": -200, "width": 400, "height": 380, "color": "1"},
    {"id": "n3", "type": "file", "file": r"docs\MOCs\Deep_Dives\Motor_Auditoria_Codigo\3_Oculto_LCTOGER.md", "x": 0, "y": 250, "width": 400, "height": 400, "color": "1"},
    {"id": "n4", "type": "file", "file": r"docs\MOCs\Deep_Dives\Motor_Auditoria_Codigo\4_Virtual_Vulcano.md", "x": 600, "y": -200, "width": 400, "height": 380, "color": "2"},
    {"id": "n5", "type": "file", "file": r"docs\MOCs\Deep_Dives\Motor_Auditoria_Codigo\5_Locacoes_Global.md", "x": 600, "y": 250, "width": 400, "height": 420, "color": "6"},
    
    {"id": "t1", "type": "text", "text": "## Painel Frontend (Array Combinado)\nA interface de Balancete Comparativo unifica as Contas Fisicas, Contas Virtuais e Orfaos identificados na matriz do `resultados`." , "x": 1200, "y": 0, "width": 400, "height": 180, "color": "3"}
  ],
  "edges": [
    {"id": "e1", "fromNode": "n1", "fromSide": "right", "toNode": "n2", "toSide": "left", "label": "Motor Fisico"},
    {"id": "e2", "fromNode": "n1", "fromSide": "right", "toNode": "n3", "toSide": "left", "label": "Gastos CC"},
    {"id": "e3", "fromNode": "n1", "fromSide": "right", "toNode": "n4", "toSide": "left", "label": "Motor Virtual"},
    {"id": "e4", "fromNode": "n1", "fromSide": "right", "toNode": "n5", "toSide": "left", "label": "Base Rendas"},
    {"id": "e5", "fromNode": "n2", "fromSide": "right", "toNode": "t1", "toSide": "left"},
    {"id": "e6", "fromNode": "n3", "fromSide": "right", "toNode": "t1", "toSide": "left"},
    {"id": "e7", "fromNode": "n4", "fromSide": "right", "toNode": "t1", "toSide": "left"},
    {"id": "e8", "fromNode": "n5", "fromSide": "right", "toNode": "t1", "toSide": "left"}
  ]
}

with open(r"docs\MOCs\Deep_Dives\Lousa_Fluxo_Auditoria_Motor.canvas", "w", encoding="utf-8") as f:
    json.dump(canvas_data, f, indent=2, ensure_ascii=False)

print("Canvas do Motor gerado!")
