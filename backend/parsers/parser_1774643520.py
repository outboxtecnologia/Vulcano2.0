import pdfplumber
import re
import json
import sys

def parse_money(text):
    """Converts a string like '18.423,64' to a float like 18423.64."""
    if not text:
        return 0.0
    text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return 0.0

def extract(pdf_path):
    records = []
    # To handle buyer names spanning multiple lines. Stores the last record if its buyer field is incomplete.
    last_incomplete_record = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # OBRIGATÓRIO: você DEVE usar text = page.extract_text(layout=True)
            # OBRIGATÓRIO: você DEVE tratar text = page.extract_text(layout=True) or ""
            text = page.extract_text(layout=True) or ""
            lines = text.split('\n')
            
            for line in lines:
                line_stripped = line.strip()

                # Pule linhas em branco vazias ou cabeçalhos.
                if not line_stripped:
                    continue
                # Specific header line
                if "Dt. baixa Cliente" in line_stripped: 
                    last_incomplete_record = None # Reset state after header
                    continue
                # Specific total line
                if "Total do dia" in line_stripped:
                    last_incomplete_record = None # Reset state for total lines
                    continue
                
                # Use condicionais simples: se não houver formato de data \d2/\d2/\d4 em colunas[0], pule a linha.
                date_match = re.match(r'^\d{2}/\d{2}/\d{4}', line_stripped)
                
                if date_match:
                    # ENVOLVA A LÓGICA DE CADA LINHA EM UM try/except Exception: continue
                    try:
                        # Como usamos layout=True, as colunas são perfeitamente separadas por 2 ou mais espaços.
                        # Use: colunas = [c.strip() for c in re.split(r'\s{2,}', line.strip()) if c.strip()]
                        cols = [c.strip() for c in re.split(r'\s{2,}', line_stripped) if c.strip()]
                        
                        # Se len(colunas) < 4 ou se não houver formato de data \d2/\d2/\d4 em colunas[0], pule a linha (continue).
                        # Using a more robust check for typical number of columns in a data row.
                        if len(cols) < 10: 
                            last_incomplete_record = None
                            continue

                        # A coluna da data costuma ser colunas[0].
                        data_str = cols[0]
                        
                        # O nome costuma ser colunas[1].
                        comprador_initial = cols[1]

                        # Encontre a Parcela iterando na lista de colunas (ela pode ter 12/41PM, etc).
                        parcela = ""
                        # Search for parcela from the third column up to a few columns before the end
                        # to avoid matching dates or monetary values.
                        for i in range(2, len(cols) - 5): 
                            if re.match(r'\d{1,2}/\d{1,2}(PM|PS|PA)', cols[i]):
                                parcela = cols[i]
                                break
                        
                        if not parcela: # If parcela is not found, it's likely not a valid data row
                             last_incomplete_record = None
                             continue

                        # Os últimos itens da lista colunas serão invariavelmente os valores monetários reais.
                        # Vl. baixa, Acréscimo, Seguro, Taxa adm, Desconto, Líquido
                        # Based on the header, these map to:
                        # cols[-6] -> Vl. baixa (valor_parcela)
                        # cols[-5] -> Acréscimo
                        # cols[-2] -> Desconto
                        # cols[-1] -> Líquido (total_pago)
                        
                        valor_parcela = parse_money(cols[-6])
                        acrescimo = parse_money(cols[-5])
                        desconto = parse_money(cols[-2])
                        total_pago = parse_money(cols[-1])

                        current_record = {
                            "comprador": comprador_initial,
                            "data": data_str,
                            "parcela": parcela,
                            "valor_parcela": valor_parcela,
                            "total_pago": total_pago,
                            "desconto": desconto,
                            "acrescimo": acrescimo
                        }
                        records.append(current_record)
                        
                        # Check if buyer name might be incomplete (ends with '(' suggesting a pending CPF/CNPJ)
                        if comprador_initial.endswith('('):
                            last_incomplete_record = current_record
                        else:
                            last_incomplete_record = None # Reset if the buyer name seems complete
                            
                    except Exception:
                        # print(f"Error parsing data line: {line_stripped}") # Uncomment for debugging
                        last_incomplete_record = None # Reset state on error
                        continue # Skip this problematic line
                
                # If it's not a new data line, check if it's a continuation of a previously incomplete buyer name
                elif last_incomplete_record:
                    # Look for CPF/CNPJ pattern in the line that completes the buyer name
                    # Example patterns: 30.149.988/0001-16) or 098.355.589-30)
                    cnpj_cpf_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})\)', line_stripped)
                    
                    if cnpj_cpf_match:
                        # Append the matched part to the last incomplete buyer name
                        last_incomplete_record['comprador'] += cnpj_cpf_match.group(0)
                        last_incomplete_record = None # Buyer name completed
                    else:
                        # If it's an incomplete record, but the next line is not a recognized continuation,
                        # assume it's garbage or an unhandled multi-line entry, so reset.
                        last_incomplete_record = None
                else:
                    # Line is neither a new record nor a recognized continuation, skip it
                    continue

    return records

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    result = extract(pdf_path)
    # Imprime json.dumps(extract(sys.argv[1]), ensure_ascii=False).
    print(json.dumps(result, ensure_ascii=False, indent=2))