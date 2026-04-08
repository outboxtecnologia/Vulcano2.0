import codecs

with codecs.open('frontend/src/App.jsx', 'r', 'utf-8') as f:
    app_code = f.read()

start_idx = app_code.find("  // POC State")
if start_idx != -1:
    end_idx = app_code.find("  // Compare State", start_idx)
    
    new_state = """  // POC State
  const [pocData, setPocData] = useState([]);
  const [pocPeriodo, setPocPeriodo] = useState(''); // Keep global period as requested
  const [selectedPocEmp, setSelectedPocEmp] = useState(null);
  const [pocInputPct, setPocInputPct] = useState('');
  const [loadingPoc, setLoadingPoc] = useState(false);

"""

    app_code = app_code[:start_idx] + new_state + app_code[end_idx:]

    with codecs.open('frontend/src/App.jsx', 'w', 'utf-8') as f:
        f.write(app_code)
    print("SUCCESS STATE INJECTED")
else:
    print("COULD NOT FIND POC State")
