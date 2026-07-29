with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Add a state hook for custom prompt
if "setCustomPrompt] = useState('');" not in text:
    text = text.replace("const [feedbackText, setFeedbackText] = useState('');", "const [feedbackText, setFeedbackText] = useState('');\n  const [customPrompt, setCustomPrompt] = useState('');")

# On component resume/enviarFeedback, pass customPrompt
text = text.replace(
'''JSON.stringify({ thread_id: threadId, aprovado, feedback_usuario: feedbackText })''',
'''JSON.stringify({ thread_id: threadId, aprovado, feedback_usuario: feedbackText, prompt_calibracao: customPrompt || agentState?.prompt_calibracao })'''
)

# Render textarea if prompt_calibracao exists
render_hitl = '''
      {status === 'PAUSED' && agentState?.prompt_calibracao && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #7c3aed', background: '#302050', borderRadius: '10px' }}>
          <h4 style={{ margin: '0 0 10px', color: '#c4b5fd' }}>[HITL] Calibração de Prompt e Contexto</h4>
          <p style={{ margin: '0 0 10px', fontSize: '12px' }}>O Agente formou o seguinte prompt + dossiê para enviar à IA. Você pode editar os parâmetros e o texto antes de liberar:</p>
          <textarea
            value={customPrompt || agentState.prompt_calibracao || ''}
            onChange={(e) => setCustomPrompt(e.target.value)}
            style={{ width: '100%', height: '300px', background: '#111', color: '#10b981', border: '1px solid #4ade80', borderRadius: '6px', fontFamily: 'monospace', padding: '10px', marginBottom: '10px' }}
          />
          <button onClick={() => enviarFeedback(true)} style={{ padding: '8px 16px', background: '#7c3aed', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
            Aprovar Contexto & Processar IA
          </button>
        </div>
      )}
'''

render_hitl_original = '''
      {status === 'PAUSED' && (
'''

if "Calibração de Prompt e Contexto" not in text:
    text = text.replace(render_hitl_original, render_hitl + "\n      {status === 'PAUSED' && !agentState?.prompt_calibracao && (")

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Frontend UX updated.")
