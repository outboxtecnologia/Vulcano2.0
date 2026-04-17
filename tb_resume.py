with open(r'backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update AuditResumeReq
text = text.replace(
    "class AuditResumeReq(BaseModel):\n    thread_id: str\n    aprovado: bool\n    feedback_usuario: str",
    "class AuditResumeReq(BaseModel):\n    thread_id: str\n    aprovado: bool\n    feedback_usuario: str\n    prompt_calibracao: str = None"
)

# Update state ingestion
text = text.replace(
    '''    graph_app.update_state(config, {
        "aprovado_pelo_usuario": req.aprovado,
        "feedback_usuario": req.feedback_usuario,
        "passos_executados": [f"Human feedback received: Approved={req.aprovado}"]
    })''',
    '''    update_data = {
        "aprovado_pelo_usuario": req.aprovado,
        "feedback_usuario": req.feedback_usuario,
        "passos_executados": [f"Human feedback received: Approved={req.aprovado}"]
    }
    if req.prompt_calibracao is not None:
        update_data["prompt_calibracao"] = req.prompt_calibracao
    graph_app.update_state(config, update_data)'''
)

with open(r'backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Resume endpoint updated in main.")
