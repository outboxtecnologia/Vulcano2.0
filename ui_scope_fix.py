with open(r'frontend\src\AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the old hook
text = text.replace('const [dossierExpanded, setDossierExpanded] = useState(false);\n', '')
# also try without newline just in case
text = text.replace('const [dossierExpanded, setDossierExpanded] = useState(false);', '')

# 2. Inject it into AgentTerminalModal
target = "const [status, setStatus] = useState('IDLE'); // IDLE, RUNNING, PAUSED, FINISHED, ERROR"
if target in text:
    new_target = target + "\n  const [dossierExpanded, setDossierExpanded] = useState(false);"
    text = text.replace(target, new_target)
else:
    print("WARNING: target not found")

with open(r'frontend\src\AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Lexical Scope of dossierExpanded fixed!")
