import sqlite3

novo_prompt = """Siga estritamente o layout colunar deste relatório STUTTGART (ou similar).
- Comprador/Cliente na 2ª coluna (Nome, ID, Doc).
- Data de vencimento (Data vecto) ao lado direito da coluna Parc/Oper.
- Parcela (Parc) contém barra (ex: 12/41 PM). Ignore a coluna Titulo isolada.
- Valores financeiros estão MAIS À DIREITA, no seguinte formato e ordem exata das últimas colunas (da esquerda para direita na reta final de cada linha validada):
  1. Vl. baixa (Valor da parcela)
  2. Acréscimo
  3. Seguro
  4. Taxa adm
  5. Desconto
  6. Líquido (Total Pago)

REGRA CRÍTICA PARA MODELOS MENORES (COMO QWEN 3B):
Você DEVE olhar especificamente a segunda coluna desta reta final para capturar o ACRÉSCIMO, e a quinta coluna da reta final para capturar o DESCONTO. Exemplo de linha: ... 18.423,64 (Vl Baixa) | 0,00 (Acréscimo) | 3,00 (Seguro) | 0,00 (Taxa) | 0,00 (Desconto) | 18.423,64 (Líquido). 

Extraia EXPLICITAMENTE na saída JSON as descrições como as chaves: "comprador", "data", "parcela" (do Parc com a barra), "valor_parcela" (do Vl. baixa), "acrescimo" (do Acréscimo), "desconto" (do Desconto) e "total_pago" (do Líquido). Extraia TODAS as linhas similares, ignorando as de total do dia.
Sejam zero ou não, registre os valores (ex: "0,00"). Não os omita.
Formato de saída exato: {"recebimentos": [{"comprador": "...", "data": "...", "parcela": "...", "valor_parcela": "...", "acrescimo": "...", "desconto": "...", "total_pago": "..."}, ...]}"""

conn = sqlite3.connect('poc_database.sqlite')
c = conn.cursor()
c.execute("UPDATE pdf_parser_templates SET python_code = ? WHERE id = 11", (novo_prompt,))
conn.commit()
conn.close()
print("Template 11 updated successfully.")
