with open(r'backend/core/agents/auditoria_graph.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure we import the hitl count var if it doesn't exist
if "calibracao_count:" not in text:
    pass

# We will modify supervisor_node directly.
# Let's write a script to replace the supervisor_node code logic safely.
