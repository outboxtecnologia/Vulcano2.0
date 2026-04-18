# 1. Prompt Vertex AI e Extração (main.py)
A IA Generativa (gemini-2.5-flash) é usada unicamente como "Transcritor Semântico de OCR". O código em Python recorta o PDF com pdfplumber e joga numa string formatada f-string para a porta do Vertex.

**O Prompt Python Exato usado no sistema:**
`python
prompt = f"""Você extrai linhas de RECEBIMENTOS/PAGAMENTOS/PARCELAS de relatórios imobiliários.
Restaure a semântica de colunas tabulares.

SCHEMA:
1. 'comprador': Nome do cliente.
2. 'cpf_cnpj': CPF ou CNPJ.
3. 'empreendimento': Nome do prédio/projeto.
4. 'unidade': Número do apartamento/lote.
5. 'dt_vencimento': Data original de corte.
6. 'dt_pagamento': Data da baixa no banco.
7. 'parcela': Número (ex: 12/41 PM).
8. Numéricos (float): 'valor_raiz', 'descontos', 'acrescimos_variacoes' (Juros+Multa+Tx), 'total_pago' (Líquido). Se nulo, 0.0.

SAÍDA (APENAS JSON VÁLIDO):
{{
  "registros": [
    {{ "comprador": "...", "cpf_cnpj": "...", "empreendimento": "...", "unidade": "...", "dt_vencimento": "...", "dt_pagamento": "...", "parcela": "...", "valor_raiz": 0.0, "descontos": 0.0, "acrescimos_variacoes": 0.0, "total_pago": 0.0 }}
  ]
}}
Não inclua texto fora do JSON. Traga TODAS as linhas encontradas.

Text extraído:
{header_ctx}
{chunk_text}
"""
`

**Configurações do Vertex no Código:**
O sistema está programado para 	hinking_budget: 0 e 
esponse_mime_type: application/json no backend para extirpar "devaneios" da IA e obter o JSON instântaneamente.
