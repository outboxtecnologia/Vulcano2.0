with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Add customAnotacao state definition
text = text.replace('const [customPrompt, setCustomPrompt] = useState("");', 'const [customPrompt, setCustomPrompt] = useState("");\n  const [customAnotacao, setCustomAnotacao] = useState("");')

# Fix enviarFeedback
payload_str_old = '''const payload = {
        thread_id: reqThreadId,
        aprovado: aprovado,
        feedback_usuario: customFeedback || "",
        prompt_calibracao: customPrompt || agentState?.prompt_calibracao
      };'''

payload_str_new = '''const basePrompt = customPrompt || agentState?.prompt_calibracao || "";
      const finalPrompt = customAnotacao ? (basePrompt + "\\n\\n--- DIRETRIZ DO AUDITOR: ---\\n" + customAnotacao) : basePrompt;
      const payload = {
        thread_id: reqThreadId,
        aprovado: aprovado,
        feedback_usuario: customFeedback || "",
        prompt_calibracao: finalPrompt
      };'''
text = text.replace(payload_str_old, payload_str_new)

# Update the Prompt UI block
ui_block_old = '''<p className="text-xs font-black uppercase tracking-widest text-[#10b981]">[HITL] Calibrao de Prompt e Contexto</p>
                <textarea 
                  value={customPrompt || agentState.prompt_calibracao || ''}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  style={{ width: '100%', minHeight: '300px', background: '#111', color: '#10b981', border: '1px solid #4ade80', borderRadius: '6px', fontFamily: 'monospace', padding: '10px' }}
                />'''

ui_block_new = '''<div className="flex flex-col gap-2">
                   <p className="text-xs font-black uppercase tracking-widest text-[#10b981]">[HITL] Calibração de Prompt e Contexto</p>
                   
                   <textarea 
                     value={customAnotacao}
                     onChange={(e) => setCustomAnotacao(e.target.value)}
                     placeholder="Diretrizes Adicionais (Ex: Assuma como Venda Concluída, ignore variações de CUB)."
                     style={{ width: '100%', minHeight: '80px', background: '#1a1a1a', color: '#e2e8f0', border: '1px solid #4ade80', borderRadius: '6px', padding: '12px', fontSize: '13px' }}
                   />
                   
                   <details className="mt-2 text-[10px] text-gray-500">
                     <summary className="cursor-pointer hover:text-gray-300 transition-colors uppercase tracking-widest font-mono mb-2">Expandir Matriz Bruta do Agente</summary>
                     <textarea 
                       value={customPrompt || agentState.prompt_calibracao || ''}
                       onChange={(e) => setCustomPrompt(e.target.value)}
                       style={{ width: '100%', minHeight: '200px', background: '#0a0a0a', color: '#888', border: '1px solid #333', borderRadius: '6px', fontFamily: 'monospace', padding: '10px', fontSize: '9px' }}
                     />
                   </details>
                </div>'''

# use strict match on prefix
text = re.sub(r'<p className="text-xs font-black uppercase tracking-widest text-\[#10b981\]">\[HITL\] Calibra[^<]+<\/p>\s*<textarea[^>]+value=\{customPrompt \|\| agentState.prompt_calibracao \|\| \'\'\}[^>]+onChange=\{[^}]+\}[^>]+style=\{[^}]+\}[^>]*\/>', ui_block_new, text)

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Prompt UI successfully.")
