# Developer Terms Log (Tutor Memory)
Esta lista registra os termos, comandos, ferramentas e padrões de arquitetura que já foram apresentados pelo agente via **DIRETRIZ DE TUTORIA TÉCNICA**.

Para não repetir conceitos, o agente consulta essa lista ativamente antes de gerar o bloco **🧠 DECODE DO DEV**.

## Termos já explicados:
- Pandas DataFrame (.groupby, .agg)
- Nomeação e Recuperação Dinâmica (`hasattr`, `getattr`, `.get()`)
- Loop de Processamento Desacoplado
- Data Enrichment / Payload Annotation
- Scoped Dictionary Pattern
- CORS (Cross-Origin Resource Sharing) Failures
- UNION POLLUTION (Data Lake vs UI)
- useState (React Hook de Estado Local)
- ReferenceError em Runtime React (tela preta / componente desmontado)
- Prop Derivation por Contexto de Dados (useMemo + inferência de campo a partir dos próprios dados)
- Cross-Empreendimento Data Contamination (Set acumulado vs filtro por campo direto)
- Hashing Determinístico de Estado em Memória (Deterministic State Hashing / Persistência sem ID Primário Relacional)
- Component Extraction & Side Effect Lifecycle Hooks (useEffect / Async UI)
- Silent Error Swallowing (NameError silenciado por except genérico)
- flatMap em resposta paginada (agregar sub-arrays de múltiplas contas da API)
- Prop Drilling Cascata (periodoFim propagado por 3 componentes: raiz → Tabela → Modal)
- Derived Timeline from POC History (reconstruir evolução mensal VU 2.0 com Δpoc × custo × fração)
- Date Cutoff Filter (corte temporal de dados históricos pelo período do Kanban via ym <= corteYM)
- Field Name Mismatch Bug (emp.contas_contabeis.estoque_obras vs CONTAESTAND — campo inexistente causando URL vazia)