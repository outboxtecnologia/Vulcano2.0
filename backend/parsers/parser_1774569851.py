import pdfplumber
import re
import json
import sys

def clean_currency(value_str):
    if not value_str: return 0.0
    return float(value_str.replace('.', '').replace(',', '.'))

def extract(pdf_path):
    results = []
    # Regex pattern to match lines based on expected structure: Date, Name, Parcel, Values
    # Adjust the regex based on the specific layout of your PDF tables
    pattern = re.compile(r'(\d{2}/\d{2}/\d{4})\s+(.*?)\s+(\d+/\d+\w{2})\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)')

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                match = pattern.search(line)
                if match:
                    data, comprador, parcela, valor_p, total, desc, acre = match.groups()
                    results.append({
                        "comprador": comprador.strip(),
                        "data": data,
                        "parcela": parcela,
                        "valor_parcela": clean_currency(valor_p),
                        "total_pago": clean_currency(total),
                        "desconto": clean_currency(desc),
                        "acrescimo": clean_currency(acre)
                    })
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        data = extract(path)
        print(json.dumps(data, ensure_ascii=False, indent=2))