import codecs

with codecs.open('frontend/src/App.jsx', 'r', 'utf-8') as f:
    app_code = f.read()

app_code = app_code.replace('\\r\\n', '\\n')

# 1. First useEffect (mount / view switch)
t1 = """    if (currentView === 'poc') {
      fetchPoc();
    }"""
n1 = """    if (currentView === 'poc') {
      fetchPoc();
      fetchReceitas();
    }"""
app_code = app_code.replace(t1, n1)

# 2. Second useEffect (selectedEmpresa changes)
t2 = "    if (currentView === 'receitas') fetchReceitas();"
n2 = "    if (currentView === 'receitas') fetchReceitas();\\n    if (currentView === 'poc') fetchReceitas();"
app_code = app_code.replace(t2, n2)

with codecs.open('frontend/src/App.jsx', 'w', 'utf-8') as f:
    f.write(app_code)

print("SUCCESS")
