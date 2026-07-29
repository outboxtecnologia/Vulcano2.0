with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. State Hook
if "const [customPrompt, setCustomPrompt] = useState('');" not in text:
    text = text.replace(
        "const [feedback, setFeedback] = useState('');",
        "const [feedback, setFeedback] = useState('');\n  const [customPrompt, setCustomPrompt] = useState('');"
    )

if "prompt_calibracao: customPrompt || agentState?.prompt_calibracao" not in text:
    text = text.replace(
        "body: JSON.stringify({ thread_id: threadId, aprovado, feedback_usuario: feedback })",
        "body: JSON.stringify({ thread_id: threadId, aprovado, feedback_usuario: feedback, prompt_calibracao: customPrompt || agentState?.prompt_calibracao })"
    )

new_block = '''           {status === 'PAUSED' && agentState?.prompt_calibracao && (
             <div className="border-t border-[var(--v-border)] bg-[var(--v-bg)] p-6 flex flex-col gap-4 sticky bottom-0 shrink-0">
                <p className="text-[10px] font-black uppercase tracking-widest text-[#10b981]">[HITL] Calibração de Prompt e Contexto</p>
                <textarea 
                  value={customPrompt || agentState.prompt_calibracao || ''}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  style={{ width: '100%', minHeight: '300px', background: '#111', color: '#10b981', border: '1px solid #4ade80', borderRadius: '6px', fontFamily: 'monospace', padding: '10px' }}
                />
                <button onClick={() => enviarFeedback(true)} className="flex-1 bg-[#10b981] hover:bg-[#059669] text-white py-3.5 rounded-[var(--v-radius)] font-black text-xs uppercase tracking-widest transition-colors">
                  APROVAR CONTEXTO & PROCESSAR IA
                </button>
             </div>
           )}

           {status === 'PAUSED' && !agentState?.prompt_calibracao && (
             <div className="border-t border-[var(--v-border)] bg-[var(--v-bg)] p-6 flex flex-col gap-4 sticky bottom-0 shrink-0">'''

text = text.replace(
    '''           {status === 'PAUSED' && (

             <div className="border-t border-[var(--v-border)] bg-[var(--v-bg)] p-6 flex flex-col gap-4 sticky bottom-0 shrink-0">''',
    new_block
)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated successfully!")
