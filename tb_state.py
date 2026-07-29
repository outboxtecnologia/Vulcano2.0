with open(r'backend/core/agents/state.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add calibration hitl flag if exists
if "prompt_calibracao:" not in text and "prompt_calibracao" not in text:
    text = text.replace("feedback_usuario: str", "feedback_usuario: str\n    prompt_calibracao: str")

with open(r'backend/core/agents/state.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("State updated")
