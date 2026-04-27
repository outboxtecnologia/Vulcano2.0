with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'f"Apropriação de Custo (POC Misto) - Unid {uni_nome}"',
    'f"{emp.get(\'hist_aprcusto\', \'Apropriação Custo\')} UNID {uni_nome}"'
)
text = text.replace(
    'f"Baixa de Estoque Físico/Imóveis - Unid {uni_nome}"',
    'f"BAIXA ESTOQUE UNID {uni_nome}"'
)
text = text.replace(
    'f"Receita Auferida (POC) - Unid {uni_nome}"',
    'f"{emp.get(\'hist_var\', \'Receita POC\')} UNID {uni_nome}"'
)
text = text.replace(
    'f"Faturamento Direito s/ Venda (POC) - Unid {uni_nome}"',
    'f"{emp.get(\'hist_venda\', \'Faturamento\')} UNID {uni_nome}"'
)
text = text.replace(
    'f"Baixa de Clientes (Pgto vs POC) - Unid {uni_nome}"',
    'f"{emp.get(\'hist_rec\', \'Baixa Cliente\')} UNID {uni_nome}"'
)
text = text.replace(
    'f"Reconhecimento Adiantamento (Excesso Pgto) - Unid {uni_nome}"',
    'f"{emp.get(\'hist_adi\', \'Reconhecimento Adiantamento\')} UNID {uni_nome}"'
)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Replaced motor strings')
