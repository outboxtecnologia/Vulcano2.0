import sqlite3

conn = sqlite3.connect('poc_database.sqlite')
row_id = conn.execute('SELECT id FROM pdf_parser_templates ORDER BY id DESC LIMIT 1').fetchone()[0]

new_prompt = """Comprador na col 1 (Nome, ID, Doc).
Data na col 2 (DD/MM/AAAA). 
Parcela é a coluna que obrigatoriamente contém uma barra (Ex: 11/39PM, 12/40PM, 1/3PA, etc.). IGNORE o número solto do Título.
Valor_parcela na penúltima col, Total_pago na última col.
Desconto e Acrescimo caso existam (senão deixe branco).
Extraia TODAS as linhas financeiras similares, ignore o resto.
Formato de saída: {"recebimentos": [...]}"""

conn.execute('UPDATE pdf_parser_templates SET python_code = ? WHERE id = ?', (new_prompt, row_id))
conn.commit()
print('O manifesto do ID', row_id, 'foi atualizado!')
