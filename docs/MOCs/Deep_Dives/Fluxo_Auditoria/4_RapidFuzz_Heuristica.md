# 3. Motor Heurístico: RapidFuzz (main.py)
A Busca Heurística ocorre quando a conciliação manual rápida é requisitada (Sienge vs Vulcano).

**Regras no Python:**
1. A biblioteca 
apidfuzz executa o modelo de distâncias matemáticas puras.
2. Utilizamos o **	oken_set_ratio**, que intercepta e retém as "palavras em comum" ignorando todo o lixo envolta de nomes (Ex: "João Silva da Cunha Me" vs "João Silva").

**Trecho Fonte da Matemática em main.py:**
`python
from rapidfuzz import fuzz

_score_nome = fuzz.token_set_ratio(c_nome, txt_clean)
_score_vl = 100 if abs(v_raiz - r_val) < 1.0 or abs(t_pago - r_val) < 1.0 else 0

_score_geral = (_score_nome * 0.4) + (_score_vl * 0.6)

is_diamante_c = _score_geral >= 85

# Se os dois são diamantes, consideraremos Match absoluto.
if is_diamante_c:
    candidatas.append({
       "score": int(_score_geral),
       "is_diamante": True
    })
`
