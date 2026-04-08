import codecs

with codecs.open('frontend/src/App.jsx', 'r', 'utf-8') as f:
    app_code = f.read()

app_code = app_code.replace('\\r\\n', '\\n')

# 1. Unify useEffects (Lines 383-415 approximately)
start_idx = app_code.find("  useEffect(() => {\\n    if (!empresaConfirmed) return;")
if start_idx != -1:
    end_idx = app_code.find("  }, [selectedEmpresa, empresaConfirmed]);\\n")
    if end_idx != -1:
        end_idx += len("  }, [selectedEmpresa, empresaConfirmed]);\\n")
        
        unified_effect = """  useEffect(() => {
    if (!empresaConfirmed) return;
    
    // Unified fetcher for View/Empresa shifts (prevents duplicate loop)
    if (currentView === 'receitas' || currentView === 'poc') {
      fetchReceitas();
      fetchPoc();
    } else if (currentView === 'compare') {
      fetchCompare();
      fetchClientesEEmps();
    } else if (currentView === 'llama_painel') {
      setHistoricoMapeamento([]);
      setIaFiltroEmp('');
      setIaFiltroPeriodo('');
      fetchClientesEEmps();
    }
    
    if (currentView !== 'explorer') {
      setSelectedTable(null);
      setTableData([]);
    }
  }, [currentView, selectedEmpresa, empresaConfirmed]);
"""
        app_code = app_code[:start_idx] + unified_effect + app_code[end_idx:]
        print("Success: Unified useEffect")
    else:
        print("Error: Could not find end of second useEffect")
else:
    print("Error: Could not find start of first useEffect")

# 2. Rename 'Conversor XML' -> 'IMPORTAÇÃO'
old_nav = "<NavItem icon={<Zap size={16}/>} label=\"Conversor XML\" active={currentView === 'conciliador'} onClick={() => setCurrentView('conciliador')} />"
new_nav = "<NavItem icon={<Database size={16}/>} label=\"IMPORTAÇÃO (Questor)\" active={currentView === 'conciliador'} onClick={() => setCurrentView('conciliador')} />"
app_code = app_code.replace(old_nav, new_nav)

with codecs.open('frontend/src/App.jsx', 'w', 'utf-8') as f:
    f.write(app_code)

print("SUCCESS APP.JSX UPDATE")
