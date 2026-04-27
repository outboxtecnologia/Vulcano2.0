# 1. API de Contabilizações (Ponto de Partida)
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
