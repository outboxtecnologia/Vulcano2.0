# 2. Vetorização com Pandas (main.py)
O JSON retornado do Vertex é convertido imediatamente em pd.DataFrame. Fazer loops normais mataria a CPU para limpeza de dados.

**Aceleradores de Código no API do Vulcano:**
`python
# df é preenchido com a query bruta do Firebird ou da IA
df = pd.read_sql_query(query, conn, params=tuple(params))

# Vetorização de formatação de nulos para o JSON do FastAPI não engasgar:
df = df.replace({np.nan: None})

# Tratamento Temporal (Isso resolve Bugs de UI no React instantaneamente)
df['DATA_STR'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
df['DATA_ISO'] = pd.to_datetime(df['DATA'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
`
> O backend despacha encimento_iso (para a matemática do < do Javascript operar perfeitamente no *Filtro de Período*) nativamente, não exigindo or loop.
