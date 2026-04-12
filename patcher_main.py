import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_pattern = r'@app\.get\(\"/api/questor/contabilizacoes\"\)\n(?:async )?def api_contabilizacoes[^\n]+\n    return AccountingGraphPipeline\.api_contabilizacoes[^\n]+'

good = '''@app.get("/api/questor/contabilizacoes")
def api_contabilizacoes(empresa_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None, min_divergencia: float = 0.0, limit: int = 100):
    ano = 2024
    mes = 1
    if data_ini:
        parts = data_ini.split('-')
        if len(parts) >= 2:
            ano = int(parts[0])
            mes = int(parts[1])
    return AccountingGraphPipeline.api_contabilizacoes(ano, mes, empresa_id, None)'''

text = re.sub(bad_pattern, good, text)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
