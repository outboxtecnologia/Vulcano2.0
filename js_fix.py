with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Add optional chainings to the table iteration to prevent white screen
text = text.replace('agentState.dossie_heuristico.dossie.amostra_unidades.map', 'agentState.dossie_heuristico.dossie.amostra_unidades?.map')
text = text.replace('agentState.dossie_heuristico.dossie.custo_total_obra_mensal.map', 'agentState.dossie_heuristico.dossie.custo_total_obra_mensal?.map')

# Ensure we wrap the render correctly
text = text.replace("{status === 'PAUSED' && agentState?.dossie_heuristico?.dossie && (", "{status === 'PAUSED' && agentState?.dossie_heuristico?.dossie?.amostra_unidades && (")

with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Added optional chaining and strict checks")
