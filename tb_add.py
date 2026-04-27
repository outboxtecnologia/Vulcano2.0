with open(r'backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'feedback_usuario="",\n        messages=[],',
    'feedback_usuario="",\n        prompt_calibracao="",\n        messages=[],'
)

with open(r'backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Added prompt_calibracao to initial_state.")
