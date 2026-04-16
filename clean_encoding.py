import os
import re

file_path = os.path.join("frontend", "src", "AuditoriaERPView.jsx")

with open(file_path, "rb") as f:
    content = f.read()

text = content.decode("utf-8", errors="ignore")

# Some powershell manglings that might have replaced the original ones
replacements = {
    "Y": "🧠",
    "Y\"-": "🔌",
    "Y'": "🎯",
    "\"?": "✨",
    "\"?\"?": "✨",
    "Diagnstico": "Diagnóstico",
    "Sugesto": "Sugestão",
    "sugesto": "sugestão",
    "Concilia": "Conciliaç",
    "No": "Não",
    "no": "não",
    "Lanamentos": "Lançamentos",
    "padro": "padrão",
    "Padro": "Padrão",
    "ms": "mês",
    "Ms": "Mês",
    "Operao": "Operação",
    "Ao": "Ação",
    "Contbil": "Contábil",
    "contbeis": "contábeis",
    "Anlise": "Análise",
    "anlise": "análise",
    "Competncia": "Competência",
    "Clculo": "Cálculo",
    "Fsico": "Físico",
    "fsicos": "físicos",
    "Lgica": "Lógica",
    "Histrico": "Histórico",
    "Dbito": "Débito",
    "Crdito": "Crédito",
    "ndice": "Índice",
    "rfos": "Órfãos",
    "rfos": "órfãos",
    "rfo": "órfão"
}

# General mojibake from before (if still present)
old_mojibake = {
    'ðŸ§ ': '🧠 ', 'ðŸ”Œ': '🔌', 'ðŸŽ¯': '🎯', 'âœ¨': '✨',
    'LANÃ‡AMENTOS': 'LANÇAMENTOS', 'LanÃ§amentos': 'Lançamentos', 'lanÃ§amento': 'lançamento',
    'OperaÃ§Ã£o': 'Operação', 'ConciliaÃ§Ã£o': 'Conciliação', 'AÃ§Ã£o': 'Ação',
    'ContÃ¡bil': 'Contábil', 'contÃ¡beis': 'contábeis', 'AnÃ¡lise': 'Análise', 'anÃ¡lise': 'análise',
    'CompetÃªncia': 'Competência', 'CÃ¡lculo': 'Cálculo', 'ÓrfÃ£os': 'Órfãos',
    'FÃsico': 'Físico', 'fÃsicos': 'físicos', 'DiagnÃ³stico': 'Diagnóstico',
    'NÃ£o': 'Não', 'padrÃ£o': 'padrão', 'automÃ¡tica': 'automática',
    'mÃªs': 'mês', 'MÃªs': 'Mês', 'HistÃ³rico': 'Histórico', 'DÃ©bito': 'Débito',
    'CrÃ©dito': 'Crédito', 'Ãndice': 'Índice', 'Ã\x8dndice': 'Índice', 'Ã“rfÃ£os': 'Órfãos',
    'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
    'Ã¢': 'â', 'Ãª': 'ê', 'Ã®': 'î', 'Ã´': 'ô', 'Ã»': 'û',
    'Ã£': 'ã', 'Ãµ': 'õ', 'Ã§': 'ç',
    'Ã ': 'À', 'Ã\x81': 'Á', 'Ã\x89': 'É', 'Ã\x8d': 'Í', 'Ã\x93': 'Ó', 'Ã\x9a': 'Ú',
    'Ã\x82': 'Â', 'Ã\x8a': 'Ê', 'Ã\x8e': 'Î', 'Ã\x94': 'Ô', 'Ã\x9b': 'Û',
    'Ã\x83': 'Ã', 'Ã\x95': 'Õ', 'Ã\x87': 'Ç'
}

for k, v in list(replacements.items()) + list(old_mojibake.items()):
    text = text.replace(k, v)

# Fix some leftover unicode replacement chars  that I know the context for:
text = text.replace("Diagnstico IA ?\" Causa Raiz", "Diagnóstico IA :: Causa Raiz")
text = text.replace("?\" ", ":: ")

with open(file_path, "wb") as f:
    f.write(text.encode("utf-8"))

print("Arquivo limpo com utf-8 puro salvo.")
