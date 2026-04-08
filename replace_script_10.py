import codecs

with codecs.open('frontend/src/App.jsx', 'r', 'utf-8') as f:
    app_code = f.read()

# Normalize line endings for reliable matching
app_code = app_code.replace('\\r\\n', '\\n')

target_str = """  const handleSaveSinglePoc = (emp, pct) => {
    if (!pocPeriodo || pct === undefined || pct === '') {
       alert('Selecione o mês de referência (Período) no topo e preencha um percentual válido!');
       return;
    }
    
    setLoadingPoc(prev => ({...prev, [emp]: true}));
    fetch(`${API_BASE}/api/poc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empreendimento: emp,
        periodo: pocPeriodo,
        percentual: parseFloat(pct)
      })
    })
    .then(res => res.json())
    .then(() => {
       fetchPoc();
       setPocDrafts(prev => { const n = {...prev}; delete n[emp]; return n; });
    })
    .catch((err) => console.error("Erro", err))
    .finally(() => setLoadingPoc(prev => ({...prev, [emp]: false})));
  };"""

new_logic = """  const handleSavePocDetail = (e) => {
    e.preventDefault();
    if (!selectedPocEmp || !pocPeriodo || !pocInputPct) {
       alert('Selecione um Empreendimento, informe o Mês/Ano Referência no topo e digite o POC Novo %!');
       return;
    }
    
    setLoadingPoc(true);
    fetch(`${API_BASE}/api/poc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        empreendimento: selectedPocEmp,
        periodo: pocPeriodo,
        percentual: parseFloat(pocInputPct)
      })
    })
    .then(res => res.json())
    .then(() => {
       fetchPoc();
       setPocInputPct('');
    })
    .catch((err) => console.error("Erro", err))
    .finally(() => setLoadingPoc(false));
  };"""

if target_str in app_code:
    app_code = app_code.replace(target_str, new_logic)
    
    with codecs.open('frontend/src/App.jsx', 'w', 'utf-8') as f:
        f.write(app_code)
    print("SUCCESS")
else:
    print("TARGET NOT FOUND. Let me dry run with startswith/endswith matching...")
    start_idx = app_code.find("  const handleSaveSinglePoc = (emp, pct) => {")
    end_idx = app_code.find("};", app_code.find(".finally(() => setLoadingPoc")) + 2
    
    if start_idx != -1 and end_idx != -1:
        app_code = app_code[:start_idx] + new_logic + app_code[end_idx:]
        with codecs.open('frontend/src/App.jsx', 'w', 'utf-8') as f:
            f.write(app_code)
        print("SUCCESS VIA INDEX SEARCH")
    else:
        print("TOTAL FAILURE")
